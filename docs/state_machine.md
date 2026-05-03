# 自定义状态机

AgentLoopRunner 支持通过 YAML 配置文件注册自定义业务状态机，实现双模态认知协作框架。

## 状态定义

| 状态 | 说明 | 可切换到 |
|------|------|----------|
| `preparing` | 准备阶段，LLM 自主分析主题并建立知识点清单 | `feynman` |
| `feynman` | 费曼建构模式，协助建立知识体系 | `socratic`, `feynman`, `reflecting` |
| `socratic` | 苏格拉底批判模式，压力测试 | `feynman`, `socratic`, `reflecting` |
| `reflecting` | 总结复盘阶段，评估完整性 | `feynman`, `idle` |

## 双模态框架

### 费曼建构模式 (feynman)

角色是「充满好奇的初学者」或「知识架构师」，任务是确保知识的连贯性与可解释性。

**建构原则**：
- 当用户使用晦涩术语时，要求提供通俗类比
- 当论述跳跃中间步骤时，要求补充推导过程
- 当新概念与旧概念缺乏关联时，询问二者关系

**补全而非推翻**。

### 苏格拉底批判模式 (socratic)

角色是「犀利的哲学对手」或「逻辑审计员」，任务是挖掘潜在的矛盾、武断的假设或逻辑谬误。

**批判原则**：
- 当用户将特定场景结论普遍化时介入诘问
- 当预设未经证实的前提时要求验证
- 当存在循环论证时指出并要求重构

**破坏而非安慰**。

### 动态切换

默认处于费曼建构模式。当检测到以下三种信号时，立即切换至苏格拉底批判模式：

1. **基础性模糊**：用户用复杂术语掩盖对基础概念理解的缺失
2. **武断的假设**：包含未经验证的公理或绝对化判断
3. **内在矛盾**：当前论述与之前论述存在逻辑互斥

一旦通过诘问解决了逻辑漏洞，或用户承认认知局限性，自动返回费曼建构模式。

## 进度追踪

使用 Todo List 追踪知识体系构建进度：

```python
from Assistant.progress import KnowledgeProgress

progress = KnowledgeProgress()
progress.add_item("量子比特", priority=3)
progress.complete_item(0)
progress.is_complete()  # False
```

**判断完整性**：`is_complete()` 返回布尔值 — 所有知识点 completed = 完整。

## 状态切换工具

注册状态机后自动注册以下工具：

| 工具 | 参数 | 功能 |
|------|------|------|
| `switch_state` | `target_state`, `reason` | 执行状态切换 |
| `report_progress` | 无 | 返回进度摘要 |
| `todo_list` | `action`, `concept`, `priority`, `item_id` | 管理知识点列表 |

## 配置文件

参见项目根目录 `state_machine.yaml`。

## 相关文件

- [Assistant/agent.py](Assistant/agent.py) - `register_state_machine()` 方法
- [Assistant/progress.py](Assistant/progress.py) - `KnowledgeProgress` 类
- [Assistant/tools/state_tools.py](Assistant/tools/state_tools.py) - 状态机工具实现
