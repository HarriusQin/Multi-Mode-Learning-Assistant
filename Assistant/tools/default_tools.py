import re
from .base import BaseTool


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "一个简单的计算器，可以进行数学运算。表达式应使用 Python 语法，指数用 ** 表示（如 2**10 表示 2 的 10 次方）"
    parameters = [
        {"name": "expression", "type": "string", "description": "数学表达式，使用 Python 语法，如 2+3*4, 2**10"}
    ]

    def execute(self, expression: str) -> str:
        try:
            expr = re.sub(r'(?<!\*)\^(?!\*)', '**', expression)
            result = eval(expr, {"__builtins__": {}}, {})
            return str(result)
        except Exception as e:
            return f"计算错误: {e}"


class HelloTool(BaseTool):
    name = "hello_tool"
    description = "一个简单的工具，返回问候语"
    parameters = [
        {"name": "name", "type": "string", "description": "你的名字"}
    ]

    def execute(self, name: str) -> str:
        return f"Hello, {name}! 这是一个测试工具。"


class KBSearchTool(BaseTool):
    name = "kb_search"
    description = "从知识库中搜索相关信息。适用于回答需要事实依据的问题。"
    parameters = [
        {"name": "query", "type": "string", "description": "搜索查询"},
        {"name": "top_k", "type": "integer", "description": "返回数量", "required": False, "default": 3}
    ]

    def __init__(self, kb):
        self.kb = kb

    def execute(self, query: str, top_k: int = 3) -> str:
        results = self.kb.search(query, top_k=top_k, use_rerank=False)
        if not results:
            return "知识库中未找到相关信息"
        formatted = "\n".join(
            f"[{i+1}] {r['content']} (score: {r['score']:.2f})"
            for i, r in enumerate(results)
        )
        return formatted
