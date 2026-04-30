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
from Assistant.tools import CalculatorTool, HelloTool, KBSearchTool
from Assistant.logging_config import init_logging, get_logger
from Assistant.sqlite_rag import VectorDB_kb
from Assistant.openai_embedding_provider import OpenAIEmbeddingProvider

# 初始化日志系统
init_logging(level=10)  # DEBUG level
logger = get_logger("main")

logger.info("=" * 50)
logger.info("应用启动")
logger.info("=" * 50)


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


def test_kb_search():
    """测试知识库搜索工具"""
    logger.info("开始测试 KB Search 工具")

    # 创建 embedding provider
    embed_provider = OpenAIEmbeddingProvider(
        api_key="lm_studio",
        base_url="http://100.76.92.62:1234/v1",
        timeout=120.0,
    )

    # 创建 KB
    kb = VectorDB_kb(
        emb_model_provider=embed_provider,
        emb_model_name="text-embedding-qwen3-embedding-8b",
        db_path="test_kb.db",
        n_dims=4096,
    )

    # 清空现有数据
    kb.cursor.execute("DELETE FROM documents")
    kb.conn.commit()

    # 添加测试文档
    docs = [
        "Python 是一种广泛使用的编程语言。",
        "JavaScript 主要用于网页开发。",
        "机器学习是人工智能的一个分支。",
        "深度学习是机器学习的一个子领域。",
        "向量数据库用于存储和检索向量数据。",
    ]
    kb.add_documents(docs)
    print(f"已添加 {len(docs)} 个文档到知识库")
    print()

    # 创建带 KB 搜索工具的 agent
    provider = OpenAIProvider(
        api_key="lm_studio",
        base_url="http://100.126.144.112:1234/v1",
        timeout=120.0,
    )

    kb_tool = KBSearchTool(kb)
    agent = AgentLoopRunner(provider, "qwen/qwen3.6-27b", tools=[kb_tool])

    print("=== KB Search 工具测试 ===")
    print()

    questions = [
        "什么是 Python？",
        "机器学习和深度学习有什么关系？",
    ]

    for q in questions:
        print(f"You: {q}")
        response = agent.send_message(q)
        print(f"Assistant: {response}")
        print()

    kb.close()
    logger.info("KB Search 测试完成")


def main():

    provider = OpenAIProvider(
        api_key="lm_studio", base_url="http://100.126.144.112:1234/v1"
    )

    loop(provider, "qwen/qwen3.6-27b")


if __name__ == "__main__":
    test_kb_search()

    #main()
