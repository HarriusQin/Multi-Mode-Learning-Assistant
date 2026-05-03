# Multi-Mode Learning Assistant

```
██╗    ██╗██╗██████╗ 
██║    ██║██║██╔══██╗
██║ █╗ ██║██║██████╔╝
██║███╗██║██║██╔═══╝ 
╚███╔███╔╝██║██║     
 ╚══╝╚══╝ ╚═╝╚═╝     
                     
```

一个基于大语言模型的智能助手，支持工具执行、知识库检索和上下文管理。

## 功能特性

- **工具执行循环 (Tool Execution Loop)**: Agent 可以调用外部工具完成任务，如计算器、知识库搜索等
- **上下文管理**: 支持消息压缩和截断，避免上下文溢出
- **知识库检索**: 基于向量数据库的 RAG 实现，支持 embedding 和 rerank
- **日志系统**: 统一的日志管理，支持轮转和持久化
- **自定义状态机**: 支持双模态认知协作（费曼建构模式 + 苏格拉底批判模式）
- **进度追踪**: 基于 Todo List 的知识体系构建进度管理
- **API 服务**: 提供 Web API 接口和交互式 Web 界面

## 已完成功能

| 功能 | 状态 | 说明 |
|------|--------|-------|
| Agent Tool Execution Loop | ✓ | LLM → 工具调用 → 结果 → 响应 |
| 上下文压缩 | ✓ | 消息超过阈值时自动压缩 |
| CalculatorTool | ✓ | 支持 `+`, `-`, `*`, `/`, `**`, `^` 运算 |
| HelloTool | ✓ | 简单问候工具 |
| KBSearchTool | ✓ | 知识库检索工具 |
| 日志轮转 | ✓ | 按大小自动轮转，保留 5 个备份 |
| 自定义状态机 | ✓ | preparing/feynman/socratic/reflecting 四状态 |
| Todo List 进度追踪 | ✓ | LLM 自主分析并追踪知识点完成度 |
| API + Web 界面 | ✓ | FastAPI 服务（端口 8765） |

## 支持的模型/服务

| 类型 | 支持 | 说明 |
|------|--------|-------|
| OpenAI 兼容 API | ✓ | 通过 `OpenAIProvider` |
| LM Studio | ✓ | 本地模型服务 |
| DeepSeek API | ✓ | 原生支持 |
| Embedding 模型 | ✓ | 通过 `OpenAIEmbeddingProvider` |
| vLLM Reranker | ✓ | 通过 `VLLMRerankerProvider` |
| SQLite Vec | ✓ | 向量数据库存储 |

## 自定义状态机

Agent 内置双模态认知协作框架：

| 状态 | 说明 |
|------|------|
| `preparing` | 准备阶段，LLM 自主分析主题并建立知识点清单 |
| `feynman` | 费曼建构模式，协助建立知识体系 |
| `socratic` | 苏格拉底批判模式，压力测试知识体系 |
| `reflecting` | 总结复盘阶段，评估完整性 |

详细说明请参考 [docs/state_machine.md](docs/state_machine.md)。

## 项目结构

```
Multi-Mode-Learning-Assistant/
├── Assistant/
│   ├── agent.py              # Agent 核心实现
│   ├── context.py            # 上下文管理
│   ├── defs.py              # 数据类型定义
│   ├── progress.py          # 进度追踪（KnowledgeProgress）
│   ├── logging_config.py     # 日志配置
│   ├── openai_provider.py    # OpenAI 兼容 API 封装
│   ├── openai_embedding_provider.py  # Embedding 模型封装
│   ├── vllm_reranker_provider.py    # vLLM Reranker 封装
│   ├── sqlite_rag.py         # SQLite 向量数据库
│   └── tools/                # 工具模块
│       ├── base.py           # 工具基类
│       ├── default_tools.py  # 默认工具实现
│       └── state_tools.py    # 状态机工具
├── docs/                     # 详细文档
├── web/                      # Web 界面
├── api.py                    # FastAPI 服务入口
├── state_machine.yaml        # 状态机配置文件
├── main.py                   # 入口文件
└── logs/                     # 日志目录
```

## 快速开始

### 安装依赖

```bash
pip install httpx sqlite-vec fastapi "uvicorn[standard]" pydantic
```

### 启动 Web API

```bash
python api.py
```

访问 `http://127.0.0.1:8765` 打开 Web 界面。

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | Web 界面 |
| `/api/init` | POST | 初始化会话 |
| `/api/chat` | POST | 发送消息 |
| `/api/switch_state` | POST | 切换状态 |
| `/api/todo` | POST | 管理 Todo List |
| `/api/progress` | POST | 查询进度 |

### 程序化使用

```python
from Assistant.agent import AgentLoopRunner
from Assistant.openai_provider import OpenAIProvider

provider = OpenAIProvider(
    api_key="your-api-key",
    base_url="https://api.deepseek.com/v1"
)

agent = AgentLoopRunner(provider, "deepseek-chat")
agent.register_state_machine("state_machine.yaml")

response = agent.send_message("我想深入理解量子计算")
```

## 文档

详细文档请参考 [docs/](docs/) 目录：

- [Agent 核心](docs/agent.md) - AgentLoopRunner 的工作原理
- [上下文管理](docs/context.md) - 消息管理和压缩机制
- [工具系统](docs/tools.md) - 如何编写自定义工具
- [知识库 RAG](docs/sqlite_rag.md) - 向量数据库和检索
- [Provider 封装](docs/providers.md) - API 封装说明
- [日志系统](docs/logging.md) - 日志配置和使用
- [API Reference](docs/api.md) - 完整 API 参考文档
- [状态机设计](docs/state_machine.md) - 状态机架构说明

## License

MIT
