"""
NEXUS Business Mentor Engine v0.5
HARD RULE: proven-demand businesses only. Scorecard + SymPy ranking + memory.
"""
import json
from core.llm_client import ask, LLMError
from engines.tools.src.math_tool import MathTool
from engines.tools.src.search_tool import SearchTool
from engines.memory_semantic.src.semantic_memory import SemanticMemory

class BusinessEngine:
    def __init__(self):
        self.math = MathTool()
        self.search = SearchTool()
        self.memory = SemanticMemory()

    def _score_idea(self, idea: dict):
        b = float(idea.get("broke_start_score", 50))
        e = float(idea.get("ecosystem_pull", 50))
        c = float(idea.get("b2b_corporate_potential", 50))
        s = float(idea.get("scale_potential", 50))
        p = float(idea.get("competition_pressure", 50))
        expr = f"0.25*{b} + 0.20*{e} + 0.20*{c} + 0.20*{s} + 0.15*(100-{p})"
        res = self.math.calculate(expr)
        try:
            val = round(float(res.get("result")), 1)
        except Exception:
            val = None
        return expr, val, res

    def plan(self, situation: str, goal: str):
        memory_hits = self.memory.search_similar(f"{situation} {goal}", limit=2)
        memory_context = "None"
        if memory_hits.get("results"):
            memory_context = "\n".join(f"- [{h['title']}]: {h['preview']}" for h in memory_hits["results"])

        market_context = self.search.search("proven everyday consumer products manufacturing small business Nigeria prices", 2)

        system = f"""You are a battle-tested, street-smart business mentor AND ruthless investment analyst.

HARD RULE - PROVEN DEMAND ONLY:
Only propose businesses that sell products the world ALREADY knows and buys every day TODAY (food, water, energy, hygiene, building materials, animal feed, packaging).
NEVER propose novel concepts, app-first ideas, or products that need market education or 3+ years to become popular.
Boring proven winners beat exciting unknowns. Acceptable examples: palm oil refining, flour milling, soap and detergent, bottled/refill water, bread and bakery, animal feed, charcoal briquettes, rice milling, cement blocks, packaging bags, cooking oil, paper products.

USER'S PAST MEMORY:
---
{memory_context}
---

REAL-WORLD MARKET DATA:
---
{market_context}
---

INSTRUCTIONS:
1. Restate the user's constraints in "constraint_readback" (capital, location, horizon). State assumptions where missing.
2. Score every idea 0-100 per axis. competition_pressure=100 means fully saturated.
3. End with up to 3 clarifying questions.

Output ONLY a valid JSON object:
{{
  "constraint_readback": "What I heard: capital=..., location=..., horizon=...",
  "ideas": [
    {{
      "name": "Idea name",
      "one_line": "What it is, one sentence",
      "competition_pressure": 0,
      "broke_start_score": 0,
      "scale_potential": 0,
      "ecosystem_pull": 0,
      "b2b_corporate_potential": 0,
      "time_to_first_profit": "e.g. 2 months",
      "scale_horizon": "e.g. 5-8 years to large company",
      "why_it_survives": "Why recession/inflation/new-tech won't kill it",
      "first_move_7_days": "Exact first step this week"
    }}
  ],
  "clarifying_questions": ["q1", "q2", "q3"],
  "the_biggest_trap": "The month-one killer"
}}
"""
        prompt = f"Situation: {situation}\nGoal: {goal}"
        try:
            raw = ask(prompt, system=system, max_tokens=3000)
            clean = raw.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]

            data = json.loads(clean.strip())

            rows = ["| Idea | NEXUS SCORE | Competition | Broke-Start | Scale | Ecosystem | B2B |",
                    "|---|---|---|---|---|---|---|"]
            for idea in data.get("ideas", []):
                expr, val, res = self._score_idea(idea)
                idea["nexus_score"] = val
                idea["math_verified"] = res.get("success", False)
                rows.append(f"| {idea.get('name','?')} | {val}/100 | {idea.get('competition_pressure','?')}% | {idea.get('broke_start_score','?')} | {idea.get('scale_potential','?')} | {idea.get('ecosystem_pull','?')} | {idea.get('b2b_corporate_potential','?')} |")
            data.get("ideas", []).sort(key=lambda x: x.get("nexus_score") or 0, reverse=True)
            data["scorecard_markdown"] = "\n".join(rows)

            try:
                self.memory.store_discovery(
                    title=f"Business scorecard: {goal[:60]}",
                    content=json.dumps(data)[:1800],
                    metadata={"engine": "business", "scored": True}
                )
                data["saved_to_memory"] = True
            except Exception:
                data["saved_to_memory"] = False

            return {"data": data, "method": "llm+math+search+memory+scorecard"}
        except json.JSONDecodeError:
            return {"raw": raw, "method": "llm", "error": "Failed to parse JSON"}
        except LLMError as e:
            return {"error": str(e), "method": "fallback"}
