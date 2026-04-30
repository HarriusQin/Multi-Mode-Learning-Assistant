# Agent 核心

Agent 是整个系统的核心，负责协调语言模型、工具执行和上下文管理。

## AgentLoopRunner

`AgentLoopRunner` 类实现了工具执行循环（Tool Execution Loop）。

### 核心流程

```
用户消息 → LLM推理 → [有工具调用?] → 执行工具 → 返回结果 → LLM再次推理 → 最终响应
                         ↓
                      [无工具调用]
                         ↓
                      直接返回响应
```

### 状态机

Agent 使用 `AgentState` 枚举表示当前状态：

| 状态 | 说明 |
|------|------|
| `IDLE` | 空闲，等待用户输入 |
| `THINKING` | 正在调用 LLM |
| `TOOL_EXECUTING` | 正在执行工具 |
| `RESPONDING` | 正在返回最终响应 |

### 初始化

```python
from Assistant.agent import AgentLoopRunner
from Assistant.openai_provider import OpenAIProvider
from Assistant.tools import CalculatorTool

provider = OpenAIProvider(
    api_key="lm_studio",
    base_url="http://localhost:1234/v1"
)

tools = [CalculatorTool()]
agent = AgentLoopRunner(provider, "qwen/qwen3.6-27b", tools=tools)
```

### 发送消息

```python
response = agent.send_message("计算 2^10")
print(response)
```

### 系统提示词

默认系统提示词：

```
你是一个有帮助的助手。当你需要执行计算或查找信息时，可以使用工具。

重要规则：
1. 当你调用工具后，收到工具返回的结果时，必须直接回答用户的问题，不要再次调用工具。
2. 只调用一次工具就足够回答大多数问题。
3. 如果工具返回了结果，结合结果回答用户。
```

可通过构造函数自定义：

```python
agent = AgentLoopRunner(
    provider, model,
    system_prompt="你是一个专业的数学助手。"
)
```

### 最大循环次数

默认 `max_loop = 10`，防止无限循环。如果达到最大循环次数，返回错误信息。

## 下一步

- [工具系统](tools.md) - 了解如何编写自定义工具
- [上下文管理](context.md) - 了解消息如何被管理和压缩
