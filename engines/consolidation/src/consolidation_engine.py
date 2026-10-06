"""
NEXUS Consolidation Engine v0.1
Overnight pattern synthesis: reads accumulated memory, identifies themes,
suggests engine upgrades, creates unified theses.
"""
import json
from datetime import datetime
from core.llm_client import ask, LLMError
from engines.memory_semantic.src.semantic_memory import SemanticMemory

class ConsolidationEngine:
    def __init__(self):
        self.memory = SemanticMemory()

    def consolidate(self, days_back: int = 30):
        """Synthesize patterns from accumulated memory and suggest upgrades."""
        try:
            # Search for all types of discoveries
            all_hits = []
            queries = [
                "discoveries insights opportunities",
                "business strategies plans",
                "materials science formulations",
                "agricultural techniques",
                "traditional medicine nature",
                "skills training curricula",
                "code reviews patterns",
            ]
            for q in queries:
                hits = self.memory.search_similar(q, limit=5)
                all_hits.extend(hits.get("results", []))

            # Deduplicate by title
            seen = set()
            unique_hits = []
            for h in all_hits:
                title = h.get("title", "")
                if title and title not in seen:
                    seen.add(title)
                    unique_hits.append(h)

            if not unique_hits:
                return {
                    "summary": "No accumulated discoveries to consolidate.",
                    "themes": [],
                    "upgrade_suggestions": [],
                    "unified_theses": [],
                    "method": "empty"
                }

            mem_ctx = "\n".join(
                f"- [{h.get('title', 'Untitled')}]: {h.get('preview', '')} "
                f"(domain: {h.get('metadata', {}).get('domain', 'general')}, "
                f"score: {h.get('score', 0):.2f})"
                for h in unique_hits[:20]  # Top 20 discoveries
            )

            system = f"""You are NEXUS Consolidation, a meta-analyst that synthesizes patterns from accumulated knowledge.

Your job:
1. Identify recurring themes across discoveries
2. Find unexpected connections between domains
3. Spot gaps in current engine frameworks
4. Suggest specific upgrades to improve future reasoning
5. Create unified theses that span multiple domains

RULES:
- Be specific: don't say "consider regulations" — say "80% of business discoveries mention NAFDAC compliance; add regulatory_environment as a scoring axis"
- Cite discoveries by title when relevant
- Prioritize actionable upgrades over vague observations

ACCUMULATED DISCOVERIES (last {days_back} days, {len(unique_hits)} total):
{mem_ctx}

Output ONLY valid JSON:
{{
  "summary": "2-3 sentence overview of accumulated knowledge",
  "themes": [
    {{
      "theme": "recurring pattern",
      "frequency": "how often it appears",
      "examples": ["discovery title 1", "discovery title 2"]
    }}
  ],
  "connections": [
    {{
      "domain_a": "first domain",
      "domain_b": "second domain",
      "insight": "unexpected connection or synthesis"
    }}
  ],
  "upgrade_suggestions": [
    {{
      "engine": "which engine to upgrade",
      "current_limitation": "what it's missing",
      "suggested_change": "specific improvement",
      "evidence": "discovery titles that support this"
    }}
  ],
  "unified_theses": [
    {{
      "thesis": "cross-domain insight that unifies multiple discoveries",
      "implications": "what this means for future reasoning"
    }}
  ],
  "timestamp": "{datetime.utcnow().isoformat()}"
}}"""
            try:
                raw = ask("Consolidate", system=system, max_tokens=3000)
                clean = raw.strip()
                if clean.startswith("```json"): clean = clean[7:]
                if clean.startswith("```"): clean = clean[3:]
                if clean.endswith("```"): clean = clean[:-3]
                data = json.loads(clean.strip())
                data["timestamp"] = datetime.utcnow().isoformat()
                data["discovery_count"] = len(unique_hits)

                # Store the consolidation itself as a discovery
                try:
                    self.memory.store_discovery(
                        title=f"Consolidation: {data.get('summary', '')[:60]}",
                        content=json.dumps(data)[:2000],
                        metadata={"type": "consolidation", "days_back": days_back}
                    )
                except Exception:
                    pass

                return {"data": data, "method": "consolidation-engine"}
            except json.JSONDecodeError:
                return {"raw": raw[:2000], "error": "parse failed"}
            except LLMError as e:
                return {"error": str(e)}

        except Exception as e:
            return {"error": str(e), "method": "consolidation-failed"}
