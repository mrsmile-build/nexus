"""
NEXUS Business Mentor Engine v0.3 (With Semantic Memory Integration)
"""
import json
from core.llm_client import ask, LLMError
from engines.tools.src.math_tool import MathTool
from engines.tools.src.search_tool import SearchTool
from engines.memory_semantic.src.semantic_memory import SemanticMemory

class BusinessEngine:
    def __init__(self):
        self.math = MathTool()
        self.search = SearchTool()
        self.memory = SemanticMemory()

    def plan(self, situation: str, goal: str):
        # 1. THE ANTI-REDISCOVERY LOOP: Check Memory First
        memory_hits = self.memory.search_similar(f"{situation} {goal}", limit=2)
        memory_context = "No relevant past discoveries found in memory."
        if memory_hits.get("results"):
            memory_context = "PAST DISCOVERIES (Use this knowledge, do not re-research if applicable):\n"
            for hit in memory_hits["results"]:
                memory_context += f"- [{hit['title']}]: {hit['preview']} (Relevance Score: {hit['score']})\n"

        # 2. Gather real-world context from the web
        market_context = self.search.search("low capital high margin business ideas current market", 2)
        price_context = self.search.search("wholesale prices for small business phone accessories or cleaning supplies", 2)
        
        system = f"""You are a battle-tested, street-smart business mentor. 
You DO NOT give textbook advice. You focus on survival, cash flow, and avoiding scams.
Your prices and costs MUST be grounded in the real-world market data provided below. Do not hallucinate costs.

YOUR PAST MEMORY:
---
{memory_context}
---

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
            
            # Verify the math
            math_expr = data.get("survival_math", "0")
            math_check = self.math.calculate(math_expr)
            data["math_verified"] = math_check
            
            # 3. SAVE TO MEMORY: Store this new plan so we never research it again
            try:
                mem_result = self.memory.store_discovery(
                    title=data.get("business_idea", "Business Plan"),
                    content=f"Situation: {situation}. Goal: {goal}. Plan: {json.dumps(data)}",
                    metadata={"engine": "business", "verified": True}
                )
                data["saved_to_memory"] = mem_result
            except Exception:
                pass
            
            return {"data": data, "method": "llm+math+search+memory"}
        except json.JSONDecodeError:
            return {"raw": raw, "method": "llm", "error": "Failed to parse JSON"}
        except LLMError as e:
            return {"error": str(e), "method": "fallback"}
