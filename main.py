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
from Assistant.openai_embedding_provider import OpenAIEmbeddingProvider
from Assistant.vllm_reranker_provider import VLLMRerankerProvider
from Assistant.sqlite_rag import VectorDB_kb


def loop(provider: OpenAIProvider, model: str):
    context = Context()
    agent = AgentLoopRunner(provider, "qwen/qwen3.6-27b")
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input in {"exit", "quit"}:
                print("Goodbye!")
                break

            agent.send_message(user_input)
            context.messages.append(Message(role="user", content=user_input))
            print("Assistant: ", end="", flush=True)
            response = ""
            for chunk in agent.send_message(user_input):
                print(chunk, end="", flush=True)
                response += chunk
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


def test_vector_db():
    """测试 VectorDB_kb"""
    emb_provider = OpenAIEmbeddingProvider(
        base_url="http://100.76.92.62:1234/v1",
    )
    emb_model = "text-embedding-qwen3-embedding-8b"
    n_dims = 4096

    rerank_provider = VLLMRerankerProvider(
        api_key="lm_studio",
        base_url="http://100.126.144.112:18293",
    )
    rerank_model = "Qwen3-Reranker-0.6B"

    kb = VectorDB_kb(
        emb_model_provider=emb_provider,
        emb_model_name=emb_model,
        rerank_model_provider=rerank_provider,
        rerank_model_name=rerank_model,
        db_path="test_kb.db",
        n_dims=n_dims,
    )

    docs = [
        "Python 是一种高级编程语言，支持多种编程范式。",
        "JavaScript 主要用于 Web 前端开发，也可用于后端。",
        "机器学习是人工智能的一个分支，研究如何让计算机学习。",
        "深度学习是机器学习的子集，使用神经网络模型。",
        "向量数据库用于存储和检索高维向量数据。",
    ]

    print(f"添加 {len(docs)} 个文档...")
    for doc in docs:
        kb.add_document(doc)
    print(f"当前文档总数: {kb.count()}")

    queries = [
        "什么是 Python？",
        "深度学习和机器学习有什么关系？",
        "数据库相关",
    ]

    print("\n=== ANN 检索（无 Rerank）===")
    for q in queries:
        print(f"\n查询: {q}")
        results = kb.search(q, top_k=3, ann_k=5, use_rerank=False)
        for r in results:
            print(f"  [score={r['score']:.4f}] {r['content'][:50]}...")

    print("\n=== ANN + Rerank 精排 ===")
    for q in queries:
        print(f"\n查询: {q}")
        results = kb.search(q, top_k=3, ann_k=5, use_rerank=True)
        for r in results:
            print(f"  [score={r['score']:.4f}] {r['content'][:50]}...")

    kb.close()
    print("\n测试完成！")


def main():

    provider = OpenAIProvider(
        api_key="lm_studio", base_url="http://100.126.144.112:1234/v1"
    )

    loop(provider, "qwen/qwen3.6-27b")


if __name__ == "__main__":
    test_vector_db()

    #main()
