"""
NEXUS Business Mentor Engine v0.2 (With Real-World Search)
"""
import json
from core.llm_client import ask, LLMError
from engines.tools.src.math_tool import MathTool
from engines.tools.src.search_tool import SearchTool

class BusinessEngine:
    def __init__(self):
        self.math = MathTool()
        self.search = SearchTool()

    def plan(self, situation: str, goal: str):
        # 1. Gather real-world context first
        market_context = self.search.search("low capital high margin business ideas current market", 2)
        price_context = self.search.search("wholesale prices for small business phone accessories or cleaning supplies", 2)
        
        system = f"""You are a battle-tested, street-smart business mentor. 
You DO NOT give textbook advice. You focus on survival, cash flow, and avoiding scams.
Your prices and costs MUST be grounded in the real-world market data provided below. Do not hallucinate costs.

REAL-WORLD MARKET DATA:
---
{market_context}
{price_context}
---

Output ONLY a valid JSON object with these exact keys:
{{
  "reality_check": "A blunt assessment of their starting point.",
  "business_idea": "The specific, high-demand business.",
  "unit_economics": {{
    "product_or_service": "What is being sold",
    "estimated_cost_to_make_or_buy": 0,
    "realistic_selling_price": 0,
    "profit_margin_per_unit": 0
  }},
  "survival_math": "A sympy-compatible expression calculating how many units needed to cover basic living expenses (e.g., '1000 / 25').",
  "street_risks": ["Risk 1", "Risk 2"],
  "first_7_days_action_plan": ["Day 1 action", "Day 2 action"],
  "the_biggest_trap": "What will cause them to fail in month 1."
}}
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
            
            return {"data": data, "method": "llm+math+search"}
        except json.JSONDecodeError:
            return {"raw": raw, "method": "llm", "error": "Failed to parse JSON"}
        except LLMError as e:
            return {"error": str(e), "method": "fallback"}
