"""
NEXUS Briefing Engine v0.1
Generates morning briefings from recent discoveries in Semantic Memory.
"""
import json
from datetime import datetime, timedelta
from core.llm_client import ask, LLMError
from engines.memory_semantic.src.semantic_memory import SemanticMemory

class BriefingEngine:
    def __init__(self):
        self.memory = SemanticMemory()

    def generate_briefing(self, days_back: int = 7):
        """Generate a briefing from recent discoveries."""
        try:
            hits = self.memory.search_similar("discoveries insights opportunities patterns", limit=10)
            items = hits.get("results", [])
        except Exception:
            items = []

        if not items:
            return {
                "briefing": "No recent discoveries. NEXUS has been idle.",
                "summary": "No activity",
                "key_findings": [],
                "method": "empty"
            }

        mem_ctx = "\n".join(f"- [{h.get('title', 'Untitled')}]: {h.get('preview', '')} (score: {h.get('score', 0)})" for h in items)

        system = f"""You are NEXUS Briefing, a strategic analyst. Generate a morning briefing from recent discoveries.
Format:
1. **Executive Summary** (2-3 sentences on the big picture)
2. **Key Findings** (3-5 bullet points, most important first)
3. **Opportunities** (what the user should act on)
4. **Patterns** (themes across the discoveries)

Tone: concise, actionable, no fluff.

RECENT DISCOVERIES (last {days_back} days):
{mem_ctx}

Output ONLY valid JSON:
{{
  "summary": "2-3 sentence executive summary",
  "key_findings": ["finding 1", "finding 2", "finding 3"],
  "opportunities": ["actionable opportunity 1", "actionable opportunity 2"],
  "patterns": ["theme 1", "theme 2"],
  "timestamp": "{datetime.utcnow().isoformat()}"
}}"""
        try:
            raw = ask("Generate briefing", system=system, max_tokens=2000)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            data = json.loads(clean.strip())
            data["timestamp"] = datetime.utcnow().isoformat()
            return {"data": data, "method": "briefing-engine"}
        except json.JSONDecodeError:
            return {"raw": raw[:2000], "error": "parse failed"}
        except LLMError as e:
            return {"error": str(e)}
