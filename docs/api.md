# API Reference

> **WIP** - 文档持续更新中

## 目录

- [Agent](#agent)
- [Context](#context)
- [Tools](#tools)
- [Providers](#providers)
- [Database](#database)

---

## Agent

### AgentLoopRunner

Agent 核心类，负责协调 LLM 和工具的执行。

```python
from Assistant.agent import AgentLoopRunner

agent = AgentLoopRunner(
    provider: OpenAIProvider,    # LLM 提供者
    model: str,                   # 模型名称
    tools: list[BaseTool] = None,# 工具列表
    system_prompt: str = None    # 自定义系统提示词
)
```

#### 方法

##### `send_message(content: str) -> str`

发送用户消息并获取 Agent 响应。

```python
response = agent.send_message("计算 2^10")
# 返回: "2 的 10 次方是 1024。"
```

##### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `context` | `Context` | 上下文管理器 |
| `state` | `AgentState` | 当前状态 |
| `max_loop` | `int` | 最大循环次数（默认 10） |

#### 状态枚举

```python
from Assistant.defs import AgentState

AgentState.IDLE              # 空闲
AgentState.THINKING          # 思考中
AgentState.TOOL_EXECUTING    # 执行工具中
AgentState.RESPONDING        # 返回响应中
```

---

## Context

### Context

消息上下文管理器。

```python
from Assistant.context import Context

context = Context()
```

#### 方法

##### `add_message(role: Role, content: str, tool_call_id: str = None)`

添加消息到上下文。

```python
from Assistant.defs import Role

context.add_message(Role.USER, "你好")
context.add_message(Role.ASSISTANT, "你好，有什么可以帮你的？")
context.add_message(Role.TOOL, "计算结果: 1024", tool_call_id="call_xxx")
```

##### `set_system_prompt(prompt: str)`

设置系统提示词。

```python
context.set_system_prompt("你是一个有帮助的助手。")
```

##### `get_messages() -> list[Message]`

获取完整消息列表（系统提示词作为首条）。

```python
messages = context.get_messages()
```

##### `truncate_messages(provider, model, prompt)`

检查并执行上下文截断/压缩。

```python
context.truncate_messages(
    provider=provider,
    model="qwen/qwen3.6-27b",
    prompt="请压缩对话"
)
```

#### 属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_messages` | `int` | 20 | 最大消息数量 |
| `compressed_reserve` | `int` | 5 | 压缩后保留消息数 |
| `truncate_strategy` | `TruncationStrategy` | `COMPRESS` | 截断策略 |

#### 截断策略

```python
from Assistant.defs import TruncationStrategy

TruncationStrategy.COMPRESS   # 使用 LLM 压缩
TruncationStrategy.TRUNCATE  # 直接截断
```

---

## Tools

### BaseTool

工具抽象基类。

```python
from Assistant.tools.base import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "工具描述"
    parameters = [
        {"name": "param1", "type": "string", "description": "参数描述"}
    ]

    def execute(self, param1: str) -> str:
        return f"结果: {param1}"
```

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 工具唯一标识 |
| `description` | `str` | 工具功能描述 |
| `parameters` | `list[dict]` | 参数定义 |

#### 参数定义格式

```python
parameters = [
    {
        "name": "参数名",
        "type": "string | integer | number | boolean | array | object",
        "description": "参数描述",
        "required": True,      # 可选
        "default": "默认值"     # 可选
    }
]
```

#### 方法

##### `to_openai_format() -> dict`

转换为 OpenAI function calling 格式。

##### `execute(**kwargs) -> str`

执行工具逻辑（子类实现）。

---

### 内置工具

#### CalculatorTool

```python
from Assistant.tools import CalculatorTool

calc = CalculatorTool()
result = calc.execute("2**10")  # "1024"
result = calc.execute("10 + 20")  # "30"
result = calc.execute("2^10")  # "1024" (^ 自动转换为 **)
```

#### HelloTool

```python
from Assistant.tools import HelloTool

hello = HelloTool()
result = hello.execute(name="小明")  # "Hello, 小明! 这是一个测试工具。"
```

#### KBSearchTool

```python
from Assistant.tools import KBSearchTool
from Assistant.sqlite_rag import VectorDB_kb

kb = VectorDB_kb(...)
kb_search = KBSearchTool(kb)
result = kb_search.execute(query="Python", top_k=3)
```

---

## Providers

### OpenAIProvider

OpenAI 兼容 Chat Completions API 封装。

```python
from Assistant.openai_provider import OpenAIProvider

provider = OpenAIProvider(
    api_key: str = None,
    base_url: str = "https://api.openai.com/v1",
    timeout: float = 60.0,
    max_retries: int = 10,
    retry_delay: float = 1.0
)
```

#### 方法

##### `chat_completions(model: str, messages: list, tools=None, stream=False)`

发送聊天完成请求。

```python
from Assistant.openai_provider import Message

messages = [
    Message(role="system", content="你是一个助手。"),
    Message(role="user", content="你好")
]

response = provider.chat_completions(
    model="qwen/qwen3.6-27b",
    messages=messages,
    tools=None,
    stream=False
)

print(response.content)        # 响应内容
print(response.tool_calls)    # 工具调用列表
```

#### Message 数据类

```python
from Assistant.openai_provider import Message

msg = Message(
    role: Literal["system", "user", "assistant", "developer", "tool"],
    content: str,
    name: str = None,
    tool_call_id: str = None
)
```

#### 响应类型

```python
response.content       # str, 响应内容
response.tool_calls    # list[ToolCall] | None, 工具调用列表
response.usage         # dict, token 使用量
```

#### 异常

```python
from Assistant.openai_provider import TimeoutException, APIError

try:
    response = provider.chat_completions(...)
except TimeoutException:
    # 请求超时
except APIError as e:
    # API 错误
```

---

### OpenAIEmbeddingProvider

Embedding 模型 API 封装。

```python
from Assistant.openai_embedding_provider import OpenAIEmbeddingProvider

embed_provider = OpenAIEmbeddingProvider(
    api_key: str = None,
    base_url: str = "https://api.openai.com/v1",
    timeout: float = 60.0,
    max_retries: int = 10
)
```

#### 方法

##### `embed_single(model: str, text: str) -> list[float]`

生成单条文本的 embedding。

```python
vector = embed_provider.embed_single(
    model="text-embedding-qwen3-embedding-8b",
    text="Python 是一种编程语言"
)
# 返回: [0.123, -0.456, ...]
```

##### `embed_batch(model: str, texts: list[str]) -> list[list[float]]`

批量生成 embedding。

```python
vectors = embed_provider.embed_batch(
    model="text-embedding-qwen3-embedding-8b",
    texts=["文本1", "文本2", "文本3"]
)
# 返回: [[0.123, ...], [-0.456, ...], [0.789, ...]]
```

---

### VLLMRerankerProvider

vLLM Reranker API 封装。

```python
from Assistant.vllm_reranker_provider import VLLMRerankerProvider

rerank_provider = VLLMRerankerProvider(
    api_key: str = None,
    base_url: str = "http://localhost:8000",
    timeout: float = 60.0,
    max_retries: int = 10
)
```

#### 方法

##### `rerank(model: str, query: str, documents: list[str], top_n=None) -> RerankResponse`

执行 rerank 请求。

```python
response = rerank_provider.rerank(
    model="bge-reranker",
    query="什么是 Python？",
    documents=["文档1", "文档2", "文档3"],
    top_n=2
)

for r in response.results:
    print(f"Index: {r.index}, Score: {r.relevance_score}, Text: {r.text}")
```

##### `rerank_with_scores(model: str, query: str, documents: list[str], top_k=None, score_threshold=None) -> list[tuple[str, float]]`

简化用法，直接返回 (文档, 分数) 列表。

```python
results = rerank_provider.rerank_with_scores(
    model="bge-reranker",
    query="什么是 Python？",
    documents=["文档1", "文档2", "文档3"],
    top_k=2,
    score_threshold=0.5
)
# 返回: [("文档1", 0.95), ("文档3", 0.88)]
```

---

## Database

### VectorDB_kb

SQLite 向量数据库，支持 ANN 检索和 Rerank 精排。

```python
from Assistant.sqlite_rag import VectorDB_kb
from Assistant.openai_embedding_provider import OpenAIEmbeddingProvider
from Assistant.vllm_reranker_provider import VLLMRerankerProvider

embed_provider = OpenAIEmbeddingProvider(...)
rerank_provider = VLLMRerankerProvider(...)

kb = VectorDB_kb(
    emb_model_provider=embed_provider,
    emb_model_name="text-embedding-qwen3-embedding-8b",
    rerank_model_provider=rerank_provider,    # 可选
    rerank_model_name="bge-reranker",         # 可选
    db_path="knowledge.db",
    n_dims=4096
)
```

#### 方法

##### `add_document(text: str) -> int`

添加单个文档，返回文档 ID。

```python
doc_id = kb.add_document("Python 是一种编程语言。")
```

##### `add_documents(texts: list[str]) -> list[int]`

批量添加文档。

```python
doc_ids = kb.add_documents([
    "Python 是一种编程语言。",
    "JavaScript 用于网页开发。"
])
```

##### `search(query: str, top_k=5, ann_k=20, use_rerank=True) -> list[dict]`

搜索文档。

```python
results = kb.search(
    query="什么是 Python？",
    top_k=5,        # 最终返回数量
    ann_k=20,       # ANN 候选数量
    use_rerank=True # 是否使用 rerank
)

for r in results:
    print(f"ID: {r['id']}, Content: {r['content']}, Score: {r['score']}")
```

##### `delete_document(doc_id: int) -> bool`

删除文档。

##### `count() -> int`

返回文档总数。

##### `close()`

关闭数据库连接。

---

## 日志

### init_logging

初始化日志系统。

```python
from Assistant.logging_config import init_logging, get_logger

init_logging(level=10)  # DEBUG level
```

### get_logger

获取模块 logger。

```python
logger = get_logger("module_name")
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 日志级别

| 级别 | 值 |
|------|-----|
| `DEBUG` | 10 |
| `INFO` | 20 |
| `WARNING` | 30 |
| `ERROR` | 40 |
| `CRITICAL` | 50 |
