from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """工具基类，所有工具必须继承此类"""

    name: str
    description: str
    parameters: list[dict[str, Any]]

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """执行工具，返回结果字符串"""
        pass

    def to_openai_format(self) -> dict[str, Any]:
        """转换为 OpenAI tools 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        p["name"]: {
                            "type": p.get("type", "string"),
                            "description": p.get("description", "")
                        }
                        for p in self.parameters
                    },
                    "required": [p["name"] for p in self.parameters if p.get("required", False)]
                }
            }
        }

    def __repr__(self) -> str:
        return f"<Tool: {self.name}>"
