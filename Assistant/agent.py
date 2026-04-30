from .openai_provider import OpenAIProvider, Message, TimeoutException, APIError
from .defs import Config, Role, TruncationStrategy, AgentState
from .context import Context, LRUCache
from .tools.base import BaseTool


class AgentLoopRunner:
    provider: OpenAIProvider
    model: str
    context: Context
    state: AgentState = AgentState.IDLE
    tools: dict[str, BaseTool]
    max_loop: int = 10

    def __init__(self, provider: OpenAIProvider, model: str, tools: list[BaseTool] = None):
        self.provider = provider
        self.model = model
        self.context = Context()
        self.tools = {t.name: t for t in (tools or [])}

    def send_message(self, content: str):
        self.context.add_message(Role.USER, content)

        for step in range(self.max_loop):
            self.state = AgentState.THINKING

            response = self.provider.chat_completions(
                model=self.model,
                messages=self.context.messages,
                tools=self._get_tools_format(),
                stream=False,
            )

            if response.tool_calls:
                self.state = AgentState.TOOL_EXECUTING
                tool_call = response.tool_calls[0]

                tool = self.tools.get(tool_call.name)
                if not tool:
                    self.context.add_message(
                        Role.TOOL,
                        f"Unknown tool: {tool_call.name}",
                        tool_call_id=tool_call.id
                    )
                    continue

                try:
                    result = tool.execute(**tool_call.args)
                except Exception as e:
                    result = f"Error executing {tool_call.name}: {str(e)}"

                self.context.add_message(
                    Role.TOOL,
                    result,
                    tool_call_id=tool_call.id
                )
            else:
                self.state = AgentState.RESPONDING
                self.context.add_message(Role.ASSISTANT, response.content)
                self.state = AgentState.IDLE
                return response.content

        self.state = AgentState.IDLE
        return "[Error: Maximum tool execution loop reached]"

    def _get_tools_format(self) -> list[dict]:
        return [t.to_openai_format() for t in self.tools.values()] if self.tools else None
