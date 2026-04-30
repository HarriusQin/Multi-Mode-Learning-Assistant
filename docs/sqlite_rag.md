# 知识库 RAG

基于 SQLite 和 sqlite-vec 实现的向量数据库，支持 ANN 检索和 Rerank 精排。

## 架构

```
用户查询 → Embedding → ANN 检索 → Rerank 精排 → 返回结果
                          ↓
                    SQLite 向量存储
```

## VectorDB_kb 类

### 初始化

```python
from Assistant.sqlite_rag import VectorDB_kb
from Assistant.openai_embedding_provider import OpenAIEmbeddingProvider
from Assistant.vllm_reranker_provider import VLLMRerankerProvider

embed_provider = OpenAIEmbeddingProvider(
    api_key="lm_studio",
    base_url="http://localhost:1234/v1"
)

rerank_provider = VLLMRerankerProvider(
    api_key="lm_studio",
    base_url="http://localhost:8000"
)

kb = VectorDB_kb(
    emb_model_provider=embed_provider,
    emb_model_name="text-embedding-qwen3-embedding-8b",
    rerank_model_provider=rerank_provider,
    rerank_model_name="bge-reranker",
    db_path="knowledge.db",
    n_dims=4096
)
```

### 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `emb_model_provider` | `OpenAIEmbeddingProvider` | Embedding 模型提供商 |
| `emb_model_name` | `str` | Embedding 模型名称 |
| `rerank_model_provider` | `VLLMRerankerProvider` | Rerank 模型提供商（可选） |
| `rerank_model_name` | `str` | Rerank 模型名称（可选） |
| `db_path` | `str` | SQLite 数据库路径 |
| `n_dims` | `int` | Embedding 向量维度 |

### 添加文档

```python
# 添加单个文档
doc_id = kb.add_document("Python 是一种编程语言。")

# 批量添加
doc_ids = kb.add_documents([
    "Python 是一种编程语言。",
    "JavaScript 用于网页开发。",
    "机器学习是 AI 的一个分支。"
])
```

### 搜索文档

```python
results = kb.search(
    query="什么是 Python？",
    top_k=5,      # 最终返回数量
    ann_k=20,     # ANN 检索候选数量
    use_rerank=True  # 是否使用 rerank
)

# 返回格式:
# [
#     {"id": 1, "content": "Python 是一种编程语言。", "score": 0.95},
#     ...
# ]
```

### 删除文档

```python
kb.delete_document(doc_id)
```

### 文档计数

```python
count = kb.count()
```

### 关闭连接

```python
kb.close()

# 或使用上下文管理器
with VectorDB_kb(...) as kb:
    results = kb.search("query")
```

## 搜索流程

1. **Embedding**: 将查询文本转为向量
2. **ANN 检索**: 使用向量相似度搜索，返回 top_k 候选
3. **Rerank 精排**（可选）: 使用交叉编码器重新排序

## 下一步

- [工具系统](tools.md) - 了解 KBSearchTool 如何使用知识库
- [Provider 封装](providers.md) - 了解 Embedding 和 Reranker 的 API 封装
