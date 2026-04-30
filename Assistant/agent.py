from .openai_provider import OpenAIProvider, Message, TimeoutException, APIError
from .defs import Config, Role, TruncationStrategy, AgentState
from .context import Context, LRUCache
from .tools.base import BaseTool
from .logging_config import get_logger

logger = get_logger("agent")


class AgentLoopRunner:
    provider: OpenAIProvider
    model: str
    context: Context
    state: AgentState = AgentState.IDLE
    tools: dict[str, BaseTool]
    max_loop: int = 10

    SYSTEM_PROMPT = """你是一个有帮助的助手。当你需要执行计算或查找信息时，可以使用工具。

重要规则：
1. 当你调用工具后，收到工具返回的结果时，必须直接回答用户的问题，不要再次调用工具。
2. 只调用一次工具就足够回答大多数问题。
3. 如果工具返回了结果，结合结果回答用户。"""

    COMPRESS_PROMPT = """请将以下对话内容进行压缩，保留关键信息，删除冗余部分，使得压缩后的内容更简洁但仍能表达原意。请尽量保留对话中的重要细节和上下文信息。"""

    def __init__(self, provider: OpenAIProvider, model: str, tools: list[BaseTool] = None, system_prompt: str = None):
        self.provider = provider
        self.model = model
        self.context = Context()
        self.tools = {t.name: t for t in (tools or [])}
        # 系统提示词单独存储
        self.context.set_system_prompt(system_prompt or self.SYSTEM_PROMPT)

    def send_message(self, content: str):
        logger.info(f"收到消息: {content[:100]}...")
        self.context.add_message(Role.USER, content)

        # 检查是否需要截断/压缩上下文
        self.context.truncate_messages(
            provider=self.provider,
            model=self.model,
            prompt=self.COMPRESS_PROMPT
        )

        for step in range(self.max_loop):
            self.state = AgentState.THINKING
            logger.debug(f"[Step {step + 1}] 调用 LLM, 消息数: {len(self.context.messages)}")

            response = self.provider.chat_completions(
                model=self.model,
                messages=self.context.get_messages(),
                tools=self._get_tools_format(),
                stream=False,
            )

            if response.tool_calls:
                self.state = AgentState.TOOL_EXECUTING
                tool_call = response.tool_calls[0]
                logger.info(f"[Step {step + 1}] 调用工具: {tool_call.name}, 参数: {tool_call.args}")

                # 先添加 assistant 消息（包含 tool_calls）
                self.context.add_message(
                    Role.ASSISTANT,
                    response.content or "",
                    tool_call_id=tool_call.id
                )

                tool = self.tools.get(tool_call.name)
                if not tool:
                    logger.warning(f"[Step {step + 1}] 未知工具: {tool_call.name}")
                    self.context.add_message(
                        Role.TOOL,
                        f"Unknown tool: {tool_call.name}",
                        tool_call_id=tool_call.id
                    )
                    continue

                try:
                    result = tool.execute(**tool_call.args)
                    logger.info(f"[Step {step + 1}] 工具执行成功: {result[:100]}...")
                except Exception as e:
                    result = f"Error executing {tool_call.name}: {str(e)}"
                    logger.error(f"[Step {step + 1}] 工具执行失败: {e}")

                # 添加 tool 结果消息
                self.context.add_message(
                    Role.TOOL,
                    result,
                    tool_call_id=tool_call.id
                )
            else:
                self.state = AgentState.RESPONDING
                logger.info(f"[Step {step + 1}] 响应: {response.content[:100]}...")
                self.context.add_message(Role.ASSISTANT, response.content)
                self.state = AgentState.IDLE
                return response.content

        logger.error(f"达到最大循环次数 {self.max_loop}")
        self.state = AgentState.IDLE
        return "[Error: Maximum tool execution loop reached]"

    def _get_tools_format(self) -> list[dict]:
        return [t.to_openai_format() for t in self.tools.values()] if self.tools else None
