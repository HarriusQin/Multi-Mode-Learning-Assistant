from .openai_provider import OpenAIProvider, Message, TimeoutException, APIError
from .defs import Config, Role, TruncationStrategy, AgentState
from .context import Context, LRUCache
from .progress import KnowledgeProgress
from .tools.base import BaseTool
from .logging_config import get_logger
import yaml

logger = get_logger("agent")


class AgentLoopRunner:
    provider: OpenAIProvider
    model: str
    context: Context
    state: AgentState = AgentState.IDLE
    tools: dict[str, BaseTool]
    max_loop: int = 10

    # 业务状态机相关字段
    current_state: str = None
    machine_prompt: str = ""
    state_prompts: dict = {}
    state_transitions: dict = {}
    progress: KnowledgeProgress = None

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
        self.context.set_system_prompt(system_prompt or self.SYSTEM_PROMPT)

    def register_state_machine(self, config_path: str):
        """通过 YAML 配置文件注册状态机"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        self.state_prompts = config['state_prompts']
        self.state_transitions = {k: set(v) for k, v in config['transitions'].items()}
        self.current_state = config['meta'].get('initial_state', 'idle')
        self.machine_prompt = config['machine_prompt']

        self.progress = KnowledgeProgress()
        self.progress.current_phase = self.current_state

        self._update_system_prompt()

        # 注册状态机工具
        from .tools.state_tools import SwitchStateTool, ReportProgressTool, TodoListTool
        self.tools['switch_state'] = SwitchStateTool(self)
        self.tools['report_progress'] = ReportProgressTool(self)
        self.tools['todo_list'] = TodoListTool(self)

    def switch_state(self, target_state: str, reason: str = None) -> str:
        """执行状态切换"""
        # idle 是特殊终端状态，不检查 prompt 存在性
        if target_state != "idle" and target_state not in self.state_prompts:
            return f"[Error] 未知状态: {target_state}"

        # reflecting 进入条件：必须所有知识点已完成
        if target_state == "reflecting":
            if not self.progress.is_complete():
                pending = [item["concept"] for item in self.progress.todo_list
                           if item["status"] != "completed"]
                return f"[判断] 仍有知识点未完成: {', '.join(pending)}，请继续补充"

        # 检查切换是否允许（idle 不需要检查 transition）
        if target_state != "idle":
            allowed = self.state_transitions.get(self.current_state, set())
            if target_state not in allowed:
                return f"[Error] 不允许从 {self.current_state} 直接切换到 {target_state}"

        old = self.current_state
        self.current_state = target_state
        self.progress.current_phase = target_state
        self._update_system_prompt()

        return f"[State] {old} → {target_state}" + (f"，原因: {reason}" if reason else "")

    def _update_system_prompt(self):
        """组合机器级提示词 + 当前状态级提示词"""
        state_part = self.state_prompts.get(self.current_state, '')
        full_prompt = f"{self.machine_prompt}\n\n{state_part}"
        self.context.set_system_prompt(full_prompt)

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

                # 添加 assistant 消息（包含所有 tool_calls）
                self.context.add_message(
                    Role.ASSISTANT,
                    response.content or "",
                    tool_calls=[tc.to_dict() for tc in response.tool_calls]
                )

                # 执行所有工具调用
                for tc in response.tool_calls:
                    tool = self.tools.get(tc.name)
                    if not tool:
                        logger.warning(f"[{tc.name}] 未知工具")
                        self.context.add_message(
                            Role.TOOL,
                            f"Unknown tool: {tc.name}",
                            tool_call_id=tc.id
                        )
                        continue

                    try:
                        result = tool.execute(**tc.args)
                        logger.info(f"工具执行成功: {tc.name}")
                    except Exception as e:
                        result = f"Error executing {tc.name}: {str(e)}"
                        logger.error(f"工具执行失败: {e}")

                    self.context.add_message(
                        Role.TOOL,
                        result,
                        tool_call_id=tc.id
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
