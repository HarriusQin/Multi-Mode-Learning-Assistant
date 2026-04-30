from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any

@dataclass
class Config:
    api_key: str
    base_url: str
    model: str

class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class TruncationStrategy(Enum):
    RECENT = "recent"
    COMPRESS = "compress"

class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    RESPONDING = "responding"
    COMPACTING = "compacting"
    TOOL_EXECUTING = "tool_executing"

@dataclass
class ToolCall:
    id: str
    name: str
    args: dict[str, Any]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.args
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ToolCall':
        # Handle nested function object in OpenAI format
        func = data.get("function", {})
        name = func.get("name", "") or data.get("name", "")
        args = func.get("arguments", data.get("arguments", {}))
        if isinstance(args, str):
            import json
            args = json.loads(args)
        return cls(
            id=data.get("id", ""),
            name=name,
            args=args
        )

@dataclass
class ToolResult:
    tool_call_id: str
    content: str
    is_error: bool = False