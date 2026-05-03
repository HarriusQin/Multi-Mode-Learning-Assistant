"""Knowledge progress tracking with Todo List"""


class KnowledgeProgress:
    """Track knowledge system construction progress"""

    def __init__(self):
        self.topic: str = None
        self.topic_confirmed: bool = False
        self.todo_list: list[dict] = []
        self.pending_contradictions: list[str] = []
        self.resolved_contradictions: list[str] = []
        self.trigger_signals: int = 0
        self.current_phase: str = None

    def add_item(self, concept: str, priority: int = 0) -> int:
        """Add a knowledge point to todo list, return index"""
        idx = len(self.todo_list)
        self.todo_list.append({
            "id": idx,
            "concept": concept,
            "priority": priority,
            "status": "pending"
        })
        return idx

    def complete_item(self, idx: int):
        """Mark a knowledge point as completed"""
        if idx < len(self.todo_list):
            self.todo_list[idx]["status"] = "completed"

    def is_complete(self) -> bool:
        """Check if all knowledge points are completed"""
        return all(item["status"] == "completed" for item in self.todo_list)

    def progress_summary(self) -> str:
        """Generate progress summary string"""
        total = len(self.todo_list)
        completed = sum(1 for item in self.todo_list if item["status"] == "completed")
        pending = [item["concept"] for item in self.todo_list
                   if item["status"] == "pending"]

        lines = ["=== 知识构建进度 ==="]
        lines.append(f"主题: {self.topic or '未设定'}")
        lines.append(f"完成: {completed}/{total}")
        if pending:
            lines.append(f"待完成: {', '.join(pending)}")
        lines.append(f"矛盾: {len(self.resolved_contradictions)} 已解决 / {len(self.pending_contradictions)} 待解决")
        lines.append(f"当前阶段: {self.current_phase}")
        return '\n'.join(lines)
