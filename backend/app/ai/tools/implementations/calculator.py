"""
ai/tools/implementations/calculator.py

Why this file exists:
    Evaluates arithmetic expressions safely. Deliberately does NOT use
    Python's eval() on user input — instead parses the expression through
    Python's `ast` module and only permits numeric literals and a small
    whitelist of operators, so "2+2" works but arbitrary code execution
    does not.
"""

import ast
import operator

from app.ai.tools.tool import Tool, ToolResult

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"Disallowed expression element: {type(node).__name__}")


class CalculatorTool(Tool):
    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Evaluates a numeric arithmetic expression (e.g. '2 + 2 * 3')."

    async def execute(self, arguments: dict) -> ToolResult:
        expression = arguments.get("expression", "")
        try:
            tree = ast.parse(expression, mode="eval")
            result = _safe_eval(tree.body)
            return ToolResult(output=str(result))
        except Exception as exc:
            return ToolResult(output="", success=False, error=f"Invalid expression: {exc}")
