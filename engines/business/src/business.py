"""
NEXUS Business Mentor Engine v0.1
Acts as a street-smart mentor and business simulator.
"""
import json
from core.llm_client import ask, LLMError
from engines.tools.src.math_tool import MathTool

class BusinessEngine:
    def __init__(self):
        self.math = MathTool()

    def plan(self, situation: str, goal: str):
        system = """You are a battle-tested, street-smart business mentor. You have been broke, faced real failures, and built wealth.
You DO NOT give textbook, corporate, or generic AI advice.
You focus on survival, cash flow, real-world prices, avoiding scams, and practical execution.
When suggesting a business, you must consider how to pay for rent, food, and transport while scaling.

Output ONLY a valid JSON object with these exact keys:
{
  "reality_check": "A blunt assessment of their starting point.",
  "business_idea": "The specific, high-demand business.",
  "unit_economics": {
    "product_or_service": "What is being sold",
    "estimated_cost_to_make_or_buy": 0,
    "realistic_selling_price": 0,
    "profit_margin_per_unit": 0
  },
  "survival_math": "A sympy-compatible expression calculating how many units needed to cover basic living expenses (e.g., '1000 / 25').",
  "street_risks": ["Risk 1 (e.g., supplier scam)", "Risk 2 (e.g., dead inventory)"],
  "first_7_days_action_plan": ["Day 1 action", "Day 2 action", "..."],
  "the_biggest_trap": "What will cause them to fail in month 1 and how to avoid it."
}
Do not include markdown formatting like ```json, just the raw JSON object.
"""
        prompt = f"Situation: {situation}\nGoal: {goal}"
        try:
            raw = ask(prompt, system=system, max_tokens=1500)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            
            data = json.loads(clean.strip())
            
            # Verify the math using the deterministic Math Tool
            math_expr = data.get("survival_math", "0")
            math_check = self.math.calculate(math_expr)
            data["math_verified"] = math_check
            
            return {"data": data, "method": "llm+math"}
        except json.JSONDecodeError:
            return {"raw": raw, "method": "llm", "error": "Failed to parse JSON"}
        except LLMError as e:
            return {"error": str(e), "method": "fallback"}
