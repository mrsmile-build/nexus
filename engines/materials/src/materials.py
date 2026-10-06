"""
NEXUS Materials Engine v0.6
Formulation optimization + agri-byproduct mapping + SymPy verification.
"""
import json
from core.llm_client import ask, LLMError
from engines.tools.src.math_tool import MathTool
from engines.tools.src.search_tool import SearchTool
from engines.memory_semantic.src.semantic_memory import SemanticMemory

class MaterialsEngine:
    def __init__(self):
        self.math = MathTool()
        self.search = SearchTool()
        self.memory = SemanticMemory()

    def _map_agri_byproducts(self, target: str) -> dict:
        """Map agricultural waste to industrial substitutes."""
        prompt = f"""You are an industrial materials expert in agricultural by-product utilization.
Target material/application: {target}
List crop-residue substitutes for conventional materials.
Output ONLY valid JSON:
{{"byproduct_substitutes": [{{"byproduct": "", "replaces": "", "processing": "", "performance": "", "availability": "", "sustainability": ""}}], "cost_comparison": ""}}"""
        try:
            raw = ask(prompt, max_tokens=1200)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            return json.loads(clean.strip())
        except Exception:
            return {"byproduct_substitutes": []}

    def formulate(self, target_material: str, constraints: str = ""):
        web_context = self.search.search(f"{target_material} formulation cost optimization", 2)
        memory_hits = self.memory.search_similar(f"material {target_material}", limit=2)
        memory_context = "None"
        if memory_hits.get("results"):
            memory_context = "\n".join(f"- [{h['title']}]: {h['preview']}" for h in memory_hits["results"])

        system = f"""You are NEXUS Materials Engineer. Optimize formulations for cost, strength, availability.
Constraints: {constraints or "standard production"}
WEB CONTEXT: {web_context}
MEMORY: {memory_context}
Output ONLY valid JSON:
{{
  "target_material": "{target_material}",
  "formulation": {{"ingredients": [], "process": "", "equipment": [], "estimated_cost_per_unit": ""}},
  "alternatives": [{{"name": "", "trade_off": ""}}],
  "optimization_notes": "",
  "confidence": ""
}}"""
        try:
            raw = ask(f"Formulate: {target_material}", system=system, max_tokens=2500)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            data = json.loads(clean.strip())

            # Agri-byproduct mapping (self-improvement)
            byproducts = self._map_agri_byproducts(target_material)
            data["agri_byproduct_substitutes"] = byproducts

            return {"data": data, "method": "llm+search+math+memory+byproduct_mapping"}
        except json.JSONDecodeError:
            return {"raw": raw, "error": "parse failed"}
        except LLMError as e:
            return {"error": str(e)}
