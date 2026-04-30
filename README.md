# Multi-Mode Learning Assistant

一个基于大语言模型的智能助手，支持工具执行、知识库检索和上下文管理。

## 功能特性

- **工具执行循环 (Tool Execution Loop)**: Agent 可以调用外部工具完成任务，如计算器、知识库搜索等
- **上下文管理**: 支持消息压缩和截断，避免上下文溢出
- **知识库检索**: 基于向量数据库的 RAG 实现，支持 embedding 和 rerank
- **日志系统**: 统一的日志管理，支持轮转和持久化

## 项目结构

```
Multi-Mode-Learning-Assistant/
├── Assistant/
│   ├── agent.py              # Agent 核心实现
│   ├── context.py            # 上下文管理
│   ├── defs.py              # 数据类型定义
│   ├── logging_config.py     # 日志配置
│   ├── openai_provider.py    # OpenAI 兼容 API 封装
│   ├── openai_embedding_provider.py  # Embedding 模型封装
│   ├── vllm_reranker_provider.py    # vLLM Reranker 封装
│   ├── sqlite_rag.py         # SQLite 向量数据库
│   └── tools/                # 工具模块
│       ├── base.py           # 工具基类
│       └── default_tools.py  # 默认工具实现
├── docs/                     # 详细文档
├── main.py                   # 入口文件
└── logs/                     # 日志目录
```

## 快速开始

### 安装依赖

```bash
pip install httpx sqlite-vec
```

### 运行测试

```bash
python main.py
```

### 基本用法

```python
from Assistant.openai_provider import OpenAIProvider
from Assistant.agent import AgentLoopRunner
from Assistant.tools import CalculatorTool

provider = OpenAIProvider(
    api_key="your-api-key",
    base_url="http://localhost:1234/v1"
)

agent = AgentLoopRunner(provider, "your-model", tools=[CalculatorTool()])
response = agent.send_message("计算 123 * 456")
print(response)
```

## 文档

详细文档请参考 [docs/](docs/) 目录：

- [Agent 核心](docs/agent.md) - AgentLoopRunner 的工作原理
- [上下文管理](docs/context.md) - 消息管理和压缩机制
- [工具系统](docs/tools.md) - 如何编写自定义工具
- [知识库 RAG](docs/sqlite_rag.md) - 向量数据库和检索
- [Provider 封装](docs/providers.md) - API 封装说明
- [日志系统](docs/logging.md) - 日志配置和使用

## License

MIT
