from dataclasses import dataclass
from collections import OrderedDict
from .openai_provider import OpenAIProvider, Message
from .defs import Config, Role, TruncationStrategy, AgentState

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
    messages: list[Message] = []
    cache: LRUCache = LRUCache() # Cache for storing kb / web search results (not implemented yet)
    max_messages: int = 20
    compressed_reserve: int = 5
    truncate_strategy: TruncationStrategy = TruncationStrategy.COMPRESS


    def add_message(self, role: Role, content: str):
        self.messages.append(Message(role=role.value, content=content))

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

        conversation = "\n".join([f"{msg.role}: {msg.content}" for msg in msgs_to_compress])
        full_prompt = f"{prompt}\n\n{conversation}\n\nCompressed Conversation:"

        summarized = provider.chat_completions(model=model, messages=[Message(role="system", content=full_prompt)], stream=False)[0]
        self.messages = [Message(role="system", content=summarized)] + msgs_recent
