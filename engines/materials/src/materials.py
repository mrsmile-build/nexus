"""
NEXUS Materials & Chemistry Engine v0.1
Formulates cheaper, stronger materials (cement, alloys, composites)
using real market prices and deterministic math for mixture ratios.
"""
import json
from core.llm_client import ask, LLMError
from engines.tools.src.math_tool import MathTool
from engines.tools.src.search_tool import SearchTool

class MaterialsEngine:
    def __init__(self):
        self.math = MathTool()
        self.search = SearchTool()

    def formulate(self, target_material: str, constraints: str):
        # 1. Research alternative materials and current market prices
        alt_context = self.search.search(f"alternative supplementary materials for {target_material} low cost high strength", 2)
        price_context = self.search.search(f"wholesale price per ton raw materials {target_material} alternatives", 2)
        
        system = f"""You are a Materials Science and Chemical Engineering AI.
Your goal: Formulate 3 specific mixture ratios for {target_material} that are cheaper but stronger/more durable than the standard baseline.
You MUST use the real-world market context below to ensure your raw materials actually exist and your costs are realistic.

MARKET & SCIENCE CONTEXT:
---
{alt_context}
{price_context}
---

Output ONLY a valid JSON object with these exact keys:
{{
  "target_material": "{target_material}",
  "formulations": [
    {{
      "name": "Name of this specific mix",
      "ingredients_and_ratios": {{"Ingredient A": "X%", "Ingredient B": "Y%"}},
      "estimated_cost_per_ton": 0,
      "sympy_cost_math": "A sympy expression calculating total cost based on ratios and market prices (e.g., '0.5*50 + 0.5*20')",
      "why_it_works": "The chemical/structural reason this mix is stronger or more durable.",
      "manufacturing_risks": ["Real-world production challenges"]
    }}
  ],
  "the_biggest_trap": "What causes this type of material to fail in real life."
}}
"""
        prompt = f"Target: {target_material}\nConstraints: {constraints}"
        try:
            raw = ask(prompt, system=system, max_tokens=1500)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            
            data = json.loads(clean.strip())
            
            # Verify the cost math for each formulation using the deterministic Math Tool
            for mix in data.get("formulations", []):
                math_expr = mix.get("sympy_cost_math", "0")
                mix["math_verified"] = self.math.calculate(math_expr)
            
            return {"data": data, "method": "materials+math+search"}
        except json.JSONDecodeError:
            return {"raw": raw, "method": "llm", "error": "Failed to parse JSON"}
        except LLMError as e:
            return {"error": str(e), "method": "fallback"}
