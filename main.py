from dotenv import load_dotenv

load_dotenv()

from Assistant.openai_provider import OpenAIProvider
from Assistant.agent import AgentLoopRunner
from Assistant.tools.base import BaseTool
from Assistant.tools import CalculatorTool, KBSearchTool
from Assistant.logging_config import init_logging, get_logger
from Assistant.sqlite_rag import VectorDB_kb
from Assistant.openai_embedding_provider import OpenAIEmbeddingProvider
from Assistant.vllm_reranker_provider import VLLMRerankerProvider
from Assistant import config

init_logging(level=config.LOG_LEVEL)
logger = get_logger("main")

logger.info("=" * 50)
logger.info("应用启动")
logger.info("=" * 50)


def create_provider() -> OpenAIProvider:
    return OpenAIProvider(
        api_key=config.LLM_API_KEY,
        base_url=config.LLM_BASE_URL,
        timeout=config.LLM_TIMEOUT,
    )


def create_embed_provider() -> OpenAIEmbeddingProvider:
    return OpenAIEmbeddingProvider(
        api_key=config.EMBED_API_KEY,
        base_url=config.EMBED_BASE_URL,
        timeout=config.EMBED_TIMEOUT,
    )


def create_rerank_provider() -> VLLMRerankerProvider:
    return VLLMRerankerProvider(
        api_key=config.RERANK_API_KEY,
        base_url=config.RERANK_BASE_URL,
        timeout=config.RERANK_TIMEOUT,
    )


def create_vector_db() -> VectorDB_kb:
    return VectorDB_kb(
        emb_model_provider=create_embed_provider(),
        emb_model_name=config.EMBED_MODEL,
        rerank_model_provider=create_rerank_provider(),
        rerank_model_name=config.RERANK_MODEL,
        db_path=config.VECTOR_DB_PATH,
        n_dims=config.EMBED_N_DIMS,
    )


def loop(tools: list[BaseTool] = None):
    provider = create_provider()
    agent = AgentLoopRunner(provider, config.LLM_MODEL, tools=tools)
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
    logger.info("开始测试 Tool Execution Loop")

    provider = create_provider()
    tools = [CalculatorTool()]
    agent = AgentLoopRunner(provider, config.LLM_MODEL, tools=tools)

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
    logger.info("开始测试上下文压缩")

    provider = create_provider()
    tools = [CalculatorTool()]
    agent = AgentLoopRunner(provider, config.LLM_MODEL, tools=tools)

    print("=== 上下文压缩测试 ===")
    print(f"max_messages: {agent.context.max_messages}")
    print()

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
    logger.info("开始测试 KB Search 工具")

    kb = create_vector_db()

    kb.cursor.execute("DELETE FROM documents")
    kb.conn.commit()

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

    provider = create_provider()
    kb_tool = KBSearchTool(kb)
    agent = AgentLoopRunner(provider, config.LLM_MODEL, tools=[kb_tool])

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
    loop(tools=[CalculatorTool()])


if __name__ == "__main__":
    test_kb_search()

    #main()
