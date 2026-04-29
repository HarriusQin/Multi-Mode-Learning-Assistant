from dataclasses import dataclass
from enum import Enum

@dataclass
class Config:
    api_key: str
    base_url: str
    model: str

class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class TruncationStrategy(Enum):
    RECENT = "recent"
    COMPRESS = "compress"

class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    RESPONDING = "responding"
    COMPACTING = "compacting"