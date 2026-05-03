from dataclasses import dataclass
from collections import OrderedDict
from .openai_provider import OpenAIProvider, Message
from .defs import Config, Role, TruncationStrategy, AgentState, ToolCall, ToolResult

class LRUCache:
    def __init__(self, capacity: int = 128):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: str) -> str | None:
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, value: str) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

class Context:
    system_prompt: str = ""  # 系统提示词，单独存储
    messages: list[Message] = []  # 普通消息记录
    cache: LRUCache  # Cache for storing kb / web search results (not implemented yet)
    max_messages: int = 20
    compressed_reserve: int = 5
    truncate_strategy: TruncationStrategy = TruncationStrategy.COMPRESS

    def __init__(self):
        self.messages = []
        self.cache = LRUCache()
        self.system_prompt = ""

    def add_message(self, role: Role, content: str, tool_call_id: str = None, tool_calls: list = None):
        self.messages.append(Message(role=role.value, content=content, tool_call_id=tool_call_id, tool_calls=tool_calls))

    def set_system_prompt(self, prompt: str):
        """设置系统提示词"""
        self.system_prompt = prompt

    def get_messages(self) -> list[Message]:
        """获取消息列表，系统提示词作为首条消息返回"""
        if self.system_prompt:
            return [Message(role="system", content=self.system_prompt)] + self.messages
        return self.messages

    def message_overflow(self) -> bool:
        return len(self.messages) > self.max_messages

    def truncate_messages(self, provider: OpenAIProvider = None, model: str = None, prompt: str = None) -> None:
        if self.message_overflow():
            if self.truncate_strategy == TruncationStrategy.COMPRESS and provider and model and prompt:
                # 压缩前面的消息，保留最近的 compressed_reserve 条
                self.compress_messages(provider, model, prompt)
            else:
                self.messages = self.messages[-self.max_messages:]

    def compress_messages(self, provider: OpenAIProvider, model: str, prompt: str) -> None:
        if len(self.messages) < self.compressed_reserve:
            return

        msgs_to_compress = self.messages[:-self.compressed_reserve]
        msgs_recent = self.messages[-self.compressed_reserve:]

        conversation = "\n".join([f"{msg.role}: {msg.content}" for msg in msgs_to_compress if msg.content])
        full_prompt = f"{prompt}\n\n{conversation}\n\n请压缩以上对话，保留关键信息。"

        summarized = provider.chat_completions(
            model=model,
            messages=[
                Message(role="system", content=full_prompt),
                Message(role="user", content="请总结上述对话的关键内容。")
            ],
            stream=False
        )
        # summary 作为消息添加到列表最前面，系统提示词保持不变
        self.messages = [Message(role="system", content=summarized.content)] + msgs_recent
