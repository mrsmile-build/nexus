"""
NEXUS Blend Engine v0.1
Substitution intelligence: science profile + cultural belief profile +
blend ratios (~90% match, SymPy-verified sum) + method + mistakes +
economics (feasible != worth it, the water rule).
"""
import json
from core.llm_client import ask, LLMError
from engines.tools.src.math_tool import MathTool
from engines.tools.src.search_tool import SearchTool

class BlendEngine:
    def __init__(self):
        self.math = MathTool()
        self.search = SearchTool()

    def blend(self, request_text: str):
        web = self.search.search(request_text + " properties uses studies", 2)
        system = f"""You are NEXUS's Blend Engine: master of chemistry, nutrition, materials science AND cultural anthropology.
The user lacks something, or wants to recreate/substitute something.
WEB CONTEXT:
---
{web}
---
RULES:
1. SCIENCE and BELIEF stay in SEPARATE fields. Beliefs (treatment, mercy, favour, spiritual powers, e.g. ayeta, okigbe madarikan) are reported respectfully as what people actually use and believe, most common uses first. Never mocked. Never presented as science.
2. Blend ratios must sum to 100 and target ~90% of the target's useful profile. 2-4 components.
3. ECONOMICS: compare blend cost vs original. If synthesizing is absurd (like H2+O2 for water when water is free), say so bluntly with the cost logic.
4. Include method, mistakes to avoid, and anything that would be BETTER than the original.
Output ONLY valid JSON:
{{
  "target": "what is being substituted or recreated",
  "science_profile": "chemical/nutritional/functional properties + what studies say",
  "belief_profile": "what cultures use it for, most common first, labeled as belief",
  "blend": [{{"component": "...", "ratio_percent": 0, "what_it_supplies": "..."}}, ...],
  "match_percent": 0,
  "method": "step-by-step preparation/combination",
  "mistakes_to_avoid": ["..."],
  "better_than_original": "..." ,
  "economics": "blend cost vs original, blunt verdict",
  "confidence": "high/medium/low + what is unverified"
}}"""
        try:
            raw = ask(request_text, system=system, max_tokens=2500)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            data = json.loads(clean.strip())
            ratios = [float(c.get("ratio_percent", 0)) for c in data.get("blend", [])]
            expr = "+".join(str(r) for r in ratios) if ratios else "0"
            check = self.math.calculate(expr)
            data["ratio_sum"] = check.get("result")
            try:
                data["ratios_valid"] = abs(float(check.get("result", 0)) - 100) < 0.5
            except Exception:
                data["ratios_valid"] = False
            return {"data": data, "method": "llm+math+search+belief_layer"}
        except json.JSONDecodeError:
            return {"raw": raw, "method": "llm", "error": "parse failed"}
        except LLMError as e:
            return {"error": str(e)}
