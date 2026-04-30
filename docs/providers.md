# Provider 封装

统一的 API 调用封装，支持重试和错误处理。

## OpenAIProvider

OpenAI 兼容的 Chat Completions API 封装。

### 初始化

```python
from Assistant.openai_provider import OpenAIProvider

provider = OpenAIProvider(
    api_key="lm_studio",                    # API 密钥
    base_url="http://localhost:1234/v1",     # API 基础地址
    timeout=60.0,                            # 请求超时（秒）
    max_retries=10,                          # 最大重试次数
    retry_delay=1.0                          # 重试间隔（秒）
)
```

### 发送消息

```python
from Assistant.openai_provider import Message

messages = [
    Message(role="system", content="你是一个有帮助的助手。"),
    Message(role="user", content="你好")
]

response = provider.chat_completions(
    model="qwen/qwen3.6-27b",
    messages=messages,
    tools=None,
    stream=False
)

print(response.content)  # 获取响应内容
print(response.tool_calls)  # 获取工具调用列表
```

### 流式响应

```python
for chunk in provider.chat_completions(
    model="qwen/qwen3.6-27b",
    messages=messages,
    stream=True
):
    print(chunk, end="", flush=True)
```

## OpenAIEmbeddingProvider

Embedding 模型 API 封装。

### 初始化

```python
from Assistant.openai_embedding_provider import OpenAIEmbeddingProvider

embed_provider = OpenAIEmbeddingProvider(
    api_key="lm_studio",
    base_url="http://localhost:1234/v1",
    timeout=60.0,
    max_retries=10
)
```

### 生成 Embedding

```python
# 单条文本
vector = embed_provider.embed_single(
    model="text-embedding-qwen3-embedding-8b",
    text="Python 是一种编程语言"
)
# 返回: list[float]

# 批量文本
vectors = embed_provider.embed_batch(
    model="text-embedding-qwen3-embedding-8b",
    texts=["文本1", "文本2", "文本3"]
)
# 返回: list[list[float]]
```

## VLLMRerankerProvider

vLLM Reranker API 封装。

### 初始化

```python
from Assistant.vllm_reranker_provider import VLLMRerankerProvider

rerank_provider = VLLMRerankerProvider(
    api_key="lm_studio",
    base_url="http://localhost:8000",
    timeout=60.0,
    max_retries=10
)
```

### Rerank 排序

```python
results = rerank_provider.rerank(
    model="bge-reranker",
    query="什么是 Python？",
    documents=[
        "Python 是一种编程语言。",
        "JavaScript 用于网页开发。",
        "Python 是一种广泛使用的编程语言。"
    ],
    top_n=2
)

# 返回 RerankResponse，包含 relevance_score
for r in results.results:
    print(f"Index: {r.index}, Score: {r.relevance_score}, Text: {r.text}")
```

### 简化用法

```python
# 直接返回 (文档, 分数) 列表
doc_scores = rerank_provider.rerank_with_scores(
    model="bge-reranker",
    query="什么是 Python？",
    documents=["文档1", "文档2", "文档3"],
    top_k=2,
    score_threshold=0.5
)
# 返回: [("文档1", 0.95), ("文档3", 0.88)]
```

## 错误处理

所有 Provider 使用相同的异常体系：

```python
from Assistant.openai_provider import TimeoutException, APIError

try:
    response = provider.chat_completions(...)
except TimeoutException:
    print("请求超时")
except APIError as e:
    print(f"API 错误: {e}")
```

| 异常 | 说明 |
|------|------|
| `TimeoutException` | 请求超时 |
| `APIError` | API 返回错误 |
| `EmbeddingError` | Embedding 相关错误 |
| `RerankerError` | Reranker 相关错误 |

## 下一步

- [知识库 RAG](sqlite_rag.md) - 了解如何组合使用 Embedding 和 Reranker
