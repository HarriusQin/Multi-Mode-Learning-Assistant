"""State machine tools: switch_state, report_progress, todo_list"""

from Assistant.tools.base import BaseTool


class SwitchStateTool(BaseTool):
    """Switch Agent's business state"""
    name = "switch_state"
    description = "切换 Agent 的工作状态。当任务阶段发生变化时调用此工具。"
    parameters = [
        {"name": "target_state", "type": "string", "description": "目标状态", "required": True},
        {"name": "reason", "type": "string", "description": "切换原因", "required": False}
    ]

    def __init__(self, agent):
        self.agent = agent

    def execute(self, target_state: str, reason: str = None) -> str:
        return self.agent.switch_state(target_state, reason)


class ReportProgressTool(BaseTool):
    """Report current progress"""
    name = "report_progress"
    description = "查询当前知识体系构建进度"
    parameters = []

    def __init__(self, agent):
        self.agent = agent

    def execute(self) -> str:
        return self.agent.progress.progress_summary()


class TodoListTool(BaseTool):
    """Manage knowledge point todo list"""
    name = "todo_list"
    description = "管理知识点的待办列表"
    parameters = [
        {"name": "action", "type": "string", "description": "操作类型: add/complete/list/check", "required": True},
        {"name": "concept", "type": "string", "description": "概念名称（add时必需）", "required": False},
        {"name": "priority", "type": "integer", "description": "优先级 1-5（add时必需）", "required": False},
        {"name": "item_id", "type": "integer", "description": "知识点ID（complete/check时必需）", "required": False}
    ]

    def __init__(self, agent):
        self.agent = agent

    def execute(self, action: str, concept: str = None, priority: int = None, item_id: int = None) -> str:
        p = self.agent.progress
        if action == "add":
            idx = p.add_item(concept, priority)
            return f"[Todo] 添加知识点: {concept} (优先级:{priority}, ID:{idx})"
        elif action == "complete":
            p.complete_item(item_id)
            return f"[Todo] 已完成 ID:{item_id}"
        elif action == "list":
            return p.progress_summary()
        elif action == "check":
            is_done = p.is_complete()
            return f"[Todo] 完整性检查: {'✓ 可以进入复盘' if is_done else '✗ 仍有未完成项'}"
