import asyncio
from dataclasses import dataclass
from collections import OrderedDict
from enum import Enum
from typing import Optional
from Assistant.openai_provider import OpenAIProvider, Message

compress_prompt = """请将以下对话内容进行压缩，保留关键信息，删除冗余部分，使得压缩后的内容更简洁但仍能表达原意。请尽量保留对话中的重要细节和上下文信息。"""

from Assistant.defs import Config, Role, TruncationStrategy, AgentState
from Assistant.context import Context, LRUCache
from Assistant.openai_provider import OpenAIProvider
from Assistant.agent import AgentLoopRunner
from Assistant.tools.base import BaseTool

class HelloTool(BaseTool):
    name = "hello_tool"
    description = "一个简单的工具，返回问候语"
    parameters = [
        {"name": "name", "type": "string", "description": "你的名字"}
    ]

    def execute(self, name: str) -> str:
        return f"Hello, {name}! 这是一个测试工具。"

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "一个简单的计算器，可以进行数学运算"
    parameters = [
        {"name": "expression", "type": "string", "description": "数学表达式，如 2+3*4"}
    ]

    def execute(self, expression: str) -> str:
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return str(result)
        except Exception as e:
            return f"计算错误: {e}"


class KBSearchTool(BaseTool):
    name = "kb_search"
    description = "从知识库中搜索相关信息。适用于回答需要事实依据的问题。"
    parameters = [
        {"name": "query", "type": "string", "description": "搜索查询"},
        {"name": "top_k", "type": "integer", "description": "返回数量", "required": False, "default": 3}
    ]

    def __init__(self, kb):
        self.kb = kb

    def execute(self, query: str, top_k: int = 3) -> str:
        results = self.kb.search(query, top_k=top_k, use_rerank=False)
        if not results:
            return "知识库中未找到相关信息"
        formatted = "\n".join(
            f"[{i+1}] {r['content']} (score: {r['score']:.2f})"
            for i, r in enumerate(results)
        )
        return formatted


def loop(provider: OpenAIProvider, model: str, tools: list[BaseTool] = None):
    context = Context()
    agent = AgentLoopRunner(provider, model, tools=tools)
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input in {"exit", "quit"}:
                print("Goodbye!")
                break

            print("Assistant: ", end="", flush=True)
            response = agent.send_message(user_input)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


def test_tool_loop():
    """测试 Tool Execution Loop"""
    provider = OpenAIProvider(
        api_key="lm_studio",
        base_url="http://100.126.144.112:1234/v1",
        timeout=120.0,
    )

    tools = [CalculatorTool()]

    agent = AgentLoopRunner(provider, "qwen/qwen3.6-27b", tools=tools)

    print("=== Tool Execution Loop 测试 ===")
    print("工具: calculator")
    print()

    questions = [
        "计算 123 * 456",
        "请问 2 的 10 次方是多少？",
    ]

    for q in questions:
        print(f"You: {q}")
        response = agent.send_message(q)
        print(f"Assistant: {response}")
        print()


def main():

    provider = OpenAIProvider(
        api_key="lm_studio", base_url="http://100.126.144.112:1234/v1"
    )

    loop(provider, "qwen/qwen3.6-27b")


if __name__ == "__main__":
    test_tool_loop()

    #main()
