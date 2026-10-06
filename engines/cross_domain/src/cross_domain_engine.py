"""
NEXUS Cross-Domain Mapper v0.1
Finds unexpected connections between domains from accumulated memory.
"""
import json
from core.llm_client import ask, LLMError
from engines.memory_semantic.src.semantic_memory import SemanticMemory

class CrossDomainEngine:
    def __init__(self):
        self.memory = SemanticMemory()

    def find_connections(self, query: str):
        all_hits = []
        for domain in ["business", "materials", "nature", "agriculture", "skills"]:
            hits = self.memory.search_similar(f"{query} {domain}", limit=2)
            all_hits.extend(hits.get("results", []))
        if not all_hits:
            return {"connections": [], "method": "no_memory"}
        mem_ctx = "\n".join(
            f"- [{h.get('title', '')}] ({h.get('metadata', {}).get('domain', 'general')}): {h.get('preview', '')}"
            for h in all_hits[:10]
        )
        system = f"""You are a cross-domain innovation expert. Find unexpected connections between fields.
Query: {query}
Discoveries:
{mem_ctx}
Output ONLY valid JSON:
{{"connections": [{{"domain_a": "", "domain_b": "", "synergy": "", "innovation": "", "evidence": []}}]}}"""
        try:
            raw = ask(query, system=system, max_tokens=2000)
            clean = raw.strip()
            for t in ("```json", "```"):
                if clean.startswith(t): clean = clean[len(t):]
            if clean.endswith("```"): clean = clean[:-3]
            return {"data": json.loads(clean.strip()), "method": "cross-domain-mapper"}
        except json.JSONDecodeError:
            return {"raw": raw[:2000], "error": "parse failed"}
        except LLMError as e:
            return {"error": str(e)}
