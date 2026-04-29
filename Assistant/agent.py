from .openai_provider import OpenAIProvider, Message, TimeoutException, APIError
from .defs import Config, Role, TruncationStrategy, AgentState
from .context import Context, LRUCache


class AgentLoopRunner:
    provider: OpenAIProvider
    model: str
    context: Context
    state: AgentState = AgentState.IDLE

    def __init__(self, provider: OpenAIProvider, model: str):
        self.provider = provider
        self.model = model
        self.context = Context()

    def send_message(self, content: str):
        if self.context.message_overflow():
            self.state = AgentState.COMPACTING
            self.context.truncate_strategy()
        self.context.add_message(Role.USER, content)
        self.state = AgentState.RESPONDING

        response = ""
        try:
            for chunk in self.provider.chat_completions(
                model=self.model, messages=self.context.messages, stream=True
            ):
                yield chunk
                response += chunk
        except (TimeoutException, APIError) as e:
            self.state = AgentState.IDLE
            yield f"\n[Error: {e}]\n"
            return

        self.context.add_message(Role.ASSISTANT, response)
        self.state = AgentState.IDLE