"""
NEXUS Reverse Engineering Engine v0.1
Teardowns complex products into their raw materials and manufacturing processes.
"""
import json
from core.llm_client import ask, LLMError
from engines.tools.src.search_tool import SearchTool

class Decomposer:
    def __init__(self):
        self.search = SearchTool()

    def teardown(self, product: str):
        # 1. Search for real-world teardown reports and supply chains
        bom_context = self.search.search(f"bill of materials teardown {product} components parts list", 2)
        raw_context = self.search.search(f"raw materials required to manufacture {product} supply chain mining", 2)
        
        system = f"""You are a Master Manufacturing and Reverse Engineering AI.
Your goal: Teach the user exactly how to build {product} from scratch, down to the rawest materials.
Do not give textbook summaries. Give a gritty, realistic breakdown of the supply chain and manufacturing reality.

TEARDOWN & SUPPLY CHAIN CONTEXT:
---
{bom_context}
{raw_context}
---

Output ONLY a valid JSON object with these exact keys:
{{
  "product": "{product}",
  "core_assemblies": [
    {{
      "assembly_name": "e.g., System on Chip (SoC) or Battery Cell",
      "sub_components": ["Component 1", "Component 2"],
      "raw_materials_needed": ["e.g., Quartz sand (Silicon)", "Lithium", "Cobalt"],
      "manufacturing_process": "The exact industrial process used to make this (e.g., Photolithography, Smelting)."
    }}
  ],
  "the_hardest_part": "The single most difficult or capital-intensive part of building this from scratch.",
  "supply_chain_bottlenecks": ["Real-world materials that are hard to source or controlled by monopolies."]
}}
"""
        prompt = f"Teardown and explain how to manufacture: {product}"
        try:
            raw = ask(prompt, system=system, max_tokens=2500)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            
            data = json.loads(clean.strip())
            return {"data": data, "method": "reverse_engineering+search"}
        except json.JSONDecodeError:
            return {"raw": raw, "method": "llm", "error": "Failed to parse JSON"}
        except LLMError as e:
            return {"error": str(e), "method": "fallback"}
