"""
NEXUS Evolution Engine v0.1
Foresight and Upgrade Intelligence: looks at Past, Present (scientific bottlenecks),
and Metaphysical aspirations to design the Next Generation upgrade.
"""
import json
from core.llm_client import ask, LLMError
from engines.tools.src.search_tool import SearchTool

class EvolutionEngine:
    def __init__(self):
        self.search = SearchTool()

    def upgrade(self, artifact: str, goal: str = "next generation"):
        web = self.search.search(f"{artifact} limitations unsolved problems future predictions {goal}", 2)
        system = f"""You are NEXUS's Evolution Engine: a visionary futurist, hard-science engineer, and metaphysical philosopher combined.
Your job is to take an existing artifact and design its NEXT GENERATION upgrade by looking at the Past, Present, and Future, bridging the physical and the "beyond human."

RULES:
1. PAST: How did this evolve? What original problems were solved?
2. PRESENT (Friction): What still sucks? What are the hard scientific bottlenecks that researchers are still working on today? (e.g., battery density, material fatigue, biological limits, consciousness).
3. METAPHYSICAL/SPIRITUAL: What do humans *wish* this could do that borders on magic, spirituality, or telepathy? (e.g., "I wish my phone knew my mood without me touching it", "I wish this bridge felt no stress", "I wish this medicine could talk to my cells").
4. SYNTHESIS (The Upgrade): Combine the friction points and the metaphysical wishes into a concrete, engineered blueprint for the NEXT GENERATION. Give it a new name (e.g., if input is iPhone 19, output is iPhone 25 Pro or Nexus Prime).
5. REQUIRED BREAKTHROUGHS: What specific scientific or engineering breakthroughs are needed to build this?

Output ONLY valid JSON:
{{
  "artifact": "",
  "evolution_name": "the new name for the upgraded version",
  "past_trajectory": "how it got here",
  "current_bottlenecks": ["scientific limits researchers are stuck on"],
  "metaphysical_aspirations": "the magic/spiritual things humans wish it could do",
  "upgrade_blueprint": "detailed description of the new upgraded version",
  "key_features": ["feature 1", "feature 2"],
  "required_breakthroughs": ["what science needs to invent first"],
  "confidence": ""
}}"""
        prompt = f"Upgrade this: {artifact}. Goal: {goal}."
        try:
            raw = ask(prompt, system=system, max_tokens=3000)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            data = json.loads(clean.strip())
            return {"data": data, "method": "evolution-engine+web"}
        except json.JSONDecodeError:
            return {"raw": raw[:3000], "error": "parse failed"}
        except LLMError as e:
            return {"error": str(e)}
