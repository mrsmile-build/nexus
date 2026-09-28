"""
NEXUS Agriculture & Soil Science Engine v0.1
Optimizes land for faster, bigger growth using biology and chemistry.
"""
import json
from core.llm_client import ask, LLMError
from engines.tools.src.search_tool import SearchTool
from engines.tools.src.math_tool import MathTool

class AgricultureEngine:
    def __init__(self):
        self.search = SearchTool()
        self.math = MathTool()

    def optimize(self, goal: str, current_state: str):
        soil_context = self.search.search(f"regenerative agriculture soil microbiome NPK improvement {goal}", 2)
        chem_context = self.search.search(f"non-toxic natural fertilizers soil amendments {goal}", 2)

        system = f"""You are an expert Agronomist, Soil Scientist, and Permaculture Designer.
Your goal: Provide exact, scientifically grounded, non-toxic methods to improve land for {goal}.
Do not give generic advice. Provide specific biological and chemical soil amendments.

CONTEXT:
---
{soil_context}
{chem_context}
---

Output ONLY a valid JSON object:
{{
  "soil_diagnosis": "What the soil likely lacks based on the goal.",
  "natural_amendments": [
    {{"material": "e.g., Biochar, Rock Phosphate", "purpose": "What it does", "application_rate": "e.g., 2 tons per acre"}}
  ],
  "biological_inoculants": ["Mycorrhizal fungi", "Nitrogen-fixing bacteria", etc.],
  "water_retention_strategy": "How to hold water without toxic chemicals.",
  "sympy_yield_math": "A sympy expression estimating yield increase (e.g., 'current_yield * 1.30')",
  "the_biggest_trap": "What ruins this type of soil (e.g., over-tilling, synthetic salt buildup)."
}}
"""
        prompt = f"Goal: {goal}\nCurrent State: {current_state}"
        try:
            raw = ask(prompt, system=system, max_tokens=2000)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            
            data = json.loads(clean.strip())
            
            # Verify the yield math
            math_expr = data.get("sympy_yield_math", "0")
            data["math_verified"] = self.math.calculate(math_expr)
            
            return {"data": data, "method": "agriculture+math+search"}
        except json.JSONDecodeError:
            return {"raw": raw, "method": "llm", "error": "Failed to parse JSON"}
        except LLMError as e:
            return {"error": str(e), "method": "fallback"}
