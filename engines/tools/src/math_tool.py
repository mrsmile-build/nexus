import sympy as sp

class MathTool:
    def calculate(self, expression: str):
        """Safely evaluates math or calculus using deterministic SymPy."""
        try:
            # Parse and evaluate (e.g., "diff(x**2, x)" or "integrate(sin(x))")
            result = sp.sympify(expression)
            return {"success": True, "result": str(result), "method": "deterministic"}
        except Exception as e:
            return {"success": False, "error": str(e), "method": "deterministic"}
