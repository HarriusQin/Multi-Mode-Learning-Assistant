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
from Assistant.logging_config import init_logging, get_logger

# 初始化日志系统
init_logging(level=10)  # DEBUG level
logger = get_logger("main")

logger.info("=" * 50)
logger.info("应用启动")
logger.info("=" * 50)

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
    description = "一个简单的计算器，可以进行数学运算。表达式应使用 Python 语法，指数用 ** 表示（如 2**10 表示 2 的 10 次方）"
    parameters = [
        {"name": "expression", "type": "string", "description": "数学表达式，使用 Python 语法，如 2+3*4, 2**10"}
    ]

    def execute(self, expression: str) -> str:
        try:
            # 将 ^ 转换为 ** (Python 中 ^ 是 XOR)
            import re
            # 替换不跟在 ** 后面的 ^ 为 **
            expr = re.sub(r'(?<!\*)\^(?!\*)', '**', expression)
            result = eval(expr, {"__builtins__": {}}, {})
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
    logger.info("开始测试 Tool Execution Loop")

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
        logger.info(f"发送问题: {q}")
        print(f"You: {q}")
        response = agent.send_message(q)
        print(f"Assistant: {response}")
        print()
        logger.info(f"收到回答: {response[:100]}...")

    logger.info("测试完成")


def test_context_compression():
    """测试上下文压缩"""
    logger.info("开始测试上下文压缩")

    provider = OpenAIProvider(
        api_key="lm_studio",
        base_url="http://100.126.144.112:1234/v1",
        timeout=120.0,
    )

    tools = [CalculatorTool()]
    agent = AgentLoopRunner(provider, "qwen/qwen3.6-27b", tools=tools)

    print("=== 上下文压缩测试 ===")
    print(f"max_messages: {agent.context.max_messages}")
    print()

    # 发送超过 max_messages 的对话
    # 每个问题产生约 3 条消息 (user + assistant + tool)，超过 20 条时触发压缩
    questions = [
        "计算 10 + 20",
        "计算 30 - 15",
        "计算 5 * 6",
        "计算 100 / 4",
        "计算 2 的 3 次方",
        "计算 15 + 25",
        "计算 50 - 20",
        "计算 7 * 8",
    ]

    for q in questions:
        print(f"You: {q}")
        response = agent.send_message(q)
        print(f"Assistant: {response}")
        print(f"  [消息数: {len(agent.context.messages)}]")
        print()

    logger.info("上下文压缩测试完成")


def main():

    provider = OpenAIProvider(
        api_key="lm_studio", base_url="http://100.126.144.112:1234/v1"
    )

    loop(provider, "qwen/qwen3.6-27b")


if __name__ == "__main__":
    test_context_compression()

    #main()
