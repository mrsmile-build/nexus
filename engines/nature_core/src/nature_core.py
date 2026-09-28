"""
NEXUS Nature-Core Engine v0.1
Specialized research for plants, traditional medicine, and natural products.
Strictly separates traditional belief from scientific evidence.
"""
import json
from core.llm_client import ask, LLMError
from engines.tools.src.search_tool import SearchTool

class NatureCore:
    def __init__(self):
        self.search = SearchTool()

    def investigate(self, subject: str, tradition: str = "General"):
        # 1. Gather real-world ethnobotanical and pharmacological data
        ethno_context = self.search.search(f"traditional {tradition} medicine uses of {subject} ethnobotany", 3)
        science_context = self.search.search(f"pharmacology toxicity scientific evidence clinical trials {subject}", 3)
        
        system = f"""You are Nature-Core, a specialized research AI for ethnobotany and traditional medicine.
Your core directive: You strictly separate traditional beliefs/historical practices from modern scientific evidence. 
You NEVER present a traditional claim as a proven scientific fact.

TRADITIONAL/HISTORICAL CONTEXT:
---
{ethno_context}
---

SCIENTIFIC/PHARMACOLOGICAL CONTEXT:
---
{science_context}
---

Output ONLY a valid JSON object with these exact keys:
{{
  "subject": "{subject}",
  "traditional_claims": ["What traditional systems say it does"],
  "preparation_methods": ["How it is traditionally prepared (boiling, decoction, etc.)"],
  "known_chemical_constituents": ["Active compounds identified by science"],
  "scientific_evidence": ["What modern pharmacology actually proves (or if evidence is limited)"],
  "safety_and_toxicity": ["Known risks, interactions, or toxicities"],
  "the_divide": "A blunt summary of where traditional belief ends and scientific proof begins for this subject."
}}
"""
        prompt = f"Investigate: {subject} (Tradition: {tradition})"
        try:
            raw = ask(prompt, system=system, max_tokens=1500)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            
            data = json.loads(clean.strip())
            return {"data": data, "method": "nature_core+search"}
        except json.JSONDecodeError:
            return {"raw": raw, "method": "llm", "error": "Failed to parse JSON"}
        except LLMError as e:
            return {"error": str(e), "method": "fallback"}
