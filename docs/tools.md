# 工具系统

工具允许 Agent 执行外部操作，如计算、搜索等。

## BaseTool 抽象类

所有工具必须继承 `BaseTool`：

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

## 工具属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 工具唯一标识符 |
| `description` | `str` | 工具功能描述（用于 LLM 理解） |
| `parameters` | `list[dict]` | 参数定义 |

## 参数定义

```python
parameters = [
    {
        "name": "参数名",
        "type": "string | integer | number | boolean | array | object",
        "description": "参数描述",
        "required": True,      # 是否必需（可选）
        "default": "默认值"    # 默认值（可选）
    }
]
```

## 转换为 OpenAI 格式

```python
tool_format = my_tool.to_openai_format()
# 返回:
# {
#     "type": "function",
#     "function": {
#         "name": "my_tool",
#         "description": "工具描述",
#         "parameters": {
#             "type": "object",
#             "properties": {...},
#             "required": [...]
#         }
#     }
# }
```

## 内置工具

### CalculatorTool

计算器工具，支持基本数学运算：

```python
from Assistant.tools import CalculatorTool

calc = CalculatorTool()
result = calc.execute("2**10")  # 返回 "1024"
```

注意：`^` 会被自动转换为 `**`（指数运算）。

### HelloTool

简单的问候工具：

```python
from Assistant.tools import HelloTool

hello = HelloTool()
result = hello.execute(name="张三")  # 返回 "Hello, 张三! 这是一个测试工具。"
```

### KBSearchTool

知识库搜索工具（需要传入 VectorDB_kb 实例）：

```python
from Assistant.tools import KBSearchTool
from Assistant.sqlite_rag import VectorDB_kb

kb = VectorDB_kb(...)
kb_search = KBSearchTool(kb)
result = kb_search.execute(query="Python", top_k=3)
```

## 在 Agent 中使用工具

```python
from Assistant.agent import AgentLoopRunner
from Assistant.tools import CalculatorTool, HelloTool

tools = [CalculatorTool(), HelloTool()]
agent = AgentLoopRunner(provider, model, tools=tools)

# Agent 会根据问题自动选择合适的工具调用
response = agent.send_message("你好，我叫小明")
```

## 下一步

- [Agent 核心](agent.md) - 了解工具如何在 Agent 中执行
- [知识库 RAG](sqlite_rag.md) - 了解知识库搜索实现
