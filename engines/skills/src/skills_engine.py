"""
NEXUS Skills & Mastery Engine v0.1
Teaches ANY skill: olden (blacksmithing, weaving, pottery, herbalism),
modern (coding, AI, marketing), physical (welding, plumbing, tailoring),
online (freelancing, content), professional or informal.
Mastery path + local costs + substitutes + safety + tradition-vs-science + monetization.
"""
import json
from core.llm_client import ask, LLMError
from engines.tools.src.search_tool import SearchTool
from engines.memory_semantic.src.semantic_memory import SemanticMemory

class SkillsEngine:
    def __init__(self):
        self.search = SearchTool()
        self.memory = SemanticMemory()

    def teach(self, skill: str, level: str = "beginner", context: str = ""):
        mem = self.memory.search_similar(f"skill training {skill}", limit=1)
        mem_ctx = mem["results"][0]["preview"] if mem.get("results") else "None"
        web = self.search.search(f"{skill} apprenticeship training modern best practices how to learn", 2)
        system = f"""You are NEXUS's Master Teacher: equal parts old-world guild master, modern university professor, and street-smart business coach.
You teach ANY skill honestly: what works, what is tradition, what is myth.
RULES:
1. Separate VERIFIED technique from TRADITIONAL practice (apprenticeship customs, beliefs) - label each clearly.
2. Every tool gets a Naira cost estimate AND a substitute if missing (Blend logic).
3. Mastery path has real stages with durations, daily drills, and assessment gates (proof you can charge money).
4. End with monetization: Nigeria first, then global/online.
MEMORY: {mem_ctx}
WEB: {web}
Output ONLY valid JSON:
{{
  "skill": "", "category": "physical-trade|online|professional|traditional|artistic", "era": "olden|modern|both",
  "what_it_is": "", "why_it_matters": "",
  "prerequisites": [],
  "tools": [{{"item": "", "purpose": "", "naira_cost": "", "substitute_if_missing": ""}}],
  "safety": [],
  "mastery_path": [{{"stage": "beginner", "duration": "", "goals": [], "daily_drill": ""}}, {{"stage": "intermediate", "duration": "", "goals": [], "daily_drill": ""}}, {{"stage": "master", "duration": "", "goals": [], "daily_drill": ""}}],
  "first_7_days": [],
  "common_mistakes": [],
  "traditional_wisdom": "customs/apprenticeship/beliefs around this skill, labeled as tradition",
  "modern_edge": "tools/AI/platforms that 10x learning today",
  "monetization": "how to turn it into income, Nigeria + global",
  "assessment_gate": "the exact test that proves readiness to charge money",
  "confidence": ""
}}"""
        prompt = f"Teach me: {skill}. My level: {level}. Context: {context or 'Nigeria, limited capital'}"
        try:
            raw = ask(prompt, system=system, max_tokens=3000)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            data = json.loads(clean.strip())
            try:
                self.memory.store_discovery(title=f"Skill curriculum: {skill}", content=json.dumps(data)[:1500], metadata={"engine": "skills"})
            except Exception:
                pass
            return {"data": data, "method": "llm+search+memory+belief_layer"}
        except json.JSONDecodeError:
            return {"raw": raw, "error": "parse failed"}
        except LLMError as e:
            return {"error": str(e)}
