# 上下文管理

`Context` 类负责管理对话消息和上下文压缩。

## 消息结构

### 角色类型

| 角色 | 说明 |
|------|------|
| `system` | 系统提示词 |
| `user` | 用户消息 |
| `assistant` | 助手响应 |
| `tool` | 工具执行结果 |

### 消息格式

```python
from Assistant.defs import Role

message = Message(
    role=Role.USER.value,
    content="计算 123 * 456"
)
```

## 系统提示词与消息分离

系统提示词单独存储，消息列表只包含对话记录：

```python
context = Context()
context.set_system_prompt("你是一个有帮助的助手。")
context.add_message(Role.USER, "你好")
context.add_message(Role.ASSISTANT, "你好，有什么可以帮你的？")

# 获取完整消息列表（系统提示词作为首条）
messages = context.get_messages()
# 返回: [Message(role="system", content="..."), Message(role="user", ...), Message(role="assistant", ...)]
```

## 上下文压缩

当消息数量超过 `max_messages` 时，自动触发压缩。

### 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_messages` | 20 | 最大消息数量 |
| `compressed_reserve` | 5 | 压缩后保留的最近消息数 |
| `truncate_strategy` | `COMPRESS` | 截断策略 |

### 压缩流程

1. 消息数量超过 `max_messages`
2. 将 `[-compressed_reserve:]` 之外的消息合并为一段对话
3. 调用 LLM 生成压缩摘要（Summary）
4. Summary 作为 system 消息插入列表最前面
5. 保留最近的 `compressed_reserve` 条消息

### 压缩示例

```
压缩前消息数: 21
压缩后消息数: 6  (1 summary + 5 保留消息)
```

### 截断策略

| 策略 | 说明 |
|------|------|
| `COMPRESS` | 使用 LLM 压缩（默认） |
| `TRUNCATE` | 直接丢弃前面的消息 |

## LRU 缓存

`LRUCache` 用于缓存知识库搜索结果等临时数据：

```python
cache = LRUCache(capacity=128)
cache.put("query_key", "search_result")
result = cache.get("query_key")
```

## 下一步

- [Agent 核心](agent.md) - 了解 Agent 如何使用上下文
