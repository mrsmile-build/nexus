"""
NEXUS Nature-Core Engine v0.2
Specialized research for plants, traditional medicine, charms, and natural products.
Strictly separates traditional belief from scientific evidence and flags high-risk practices.
"""
import json
from core.llm_client import ask, LLMError
from engines.tools.src.search_tool import SearchTool

class NatureCore:
    def __init__(self):
        self.search = SearchTool()

    def investigate(self, subject: str, tradition: str = "General"):
        # 1. Gather real-world ethnobotanical, pharmacological, and anthropological data
        ethno_context = self.search.search(f"traditional {tradition} medicine uses of {subject} ethnobotany anthropology", 3)
        science_context = self.search.search(f"pharmacology toxicity scientific evidence clinical trials {subject}", 3)
        
        system = f"""You are Nature-Core, a specialized research AI for ethnobotany, traditional medicine, and anthropology.
Your core directives:
1. STRICT SEPARATION: You strictly separate traditional beliefs/historical practices from modern scientific evidence. You NEVER present a traditional claim as a proven scientific fact.
2. SAFETY FIRST: You explicitly flag high-risk practices (e.g., putting herbs in eyes, ingesting toxic plants, relying on charms for medical emergencies).
3. CULTURAL RESPECT: You describe spiritual/mysterious practices (charms, incantations) as anthropological facts, not medical mechanisms.

CONTEXT:
---
TRADITIONAL/ANTHROPOLOGICAL:
{ethno_context}
---
SCIENTIFIC/PHARMACOLOGICAL:
{science_context}
---

Output ONLY a valid JSON object with these exact keys:
{{
  "subject": "{subject}",
  "risk_level": "Low | Moderate | High | Extreme",
  "traditional_claims": ["What traditional systems say it does"],
  "cultural_context": "The spiritual, ritual, or anthropological context (e.g., 'Used in protection charms', 'Requires incantations').",
  "preparation_methods": ["How it is traditionally prepared"],
  "known_chemical_constituents": ["Active compounds identified by science"],
  "scientific_evidence": ["What modern pharmacology actually proves (or 'None' if it's purely spiritual)"],
  "safety_and_toxicity": ["Known risks, interactions, or toxicities. BE BLUNT ABOUT DANGERS."],
  "the_divide": "A blunt summary of where traditional belief ends and scientific proof begins."
}}
"""
        prompt = f"Investigate: {subject} (Tradition: {tradition})"
        try:
            raw = ask(prompt, system=system, max_tokens=2000)
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
