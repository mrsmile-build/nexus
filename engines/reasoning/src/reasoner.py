"""
NEXUS Reasoning Engine v0.4

Calls a real LLM to reason about the goal when a provider key is set.
Falls back to the v0.1 templated conclusion if no key is set, the
network call fails, or the API errors.

Extracts entity relationships from its own output (v0.3) so
ThinkingEngine can write them into the Knowledge Graph, and now (v0.4)
accepts optional feedback from LearningEngine on related past goals,
so a thumbs-down note actually changes this reasoning instead of
sitting unused in storage.
"""

import re

from core.llm_client import ask, LLMError

_RELATION_LINE = re.compile(r"^\s*(.+?)\s*(?:->|\u2192)\s*(.+?)\s*(?:->|\u2192)\s*(.+?)\s*$")
_MAX_ENTITY_LEN = 60  # sanity limit -- a real entity name, not a stray sentence


class Reasoner:
    def __init__(self, model=None):
        self.model = model

    def reason(self, goal, knowledge, feedback=None):
        try:
            conclusion, relations = self._reason_with_llm(goal, knowledge, feedback)
            method = "llm"
        except LLMError as error:
            conclusion = (
                f"Using available knowledge, the next action is to work "
                f"toward '{goal}'. (LLM reasoning unavailable: {error})"
            )
            relations = []
            method = "fallback"

        return {
            "goal": goal,
            "knowledge_used": knowledge,
            "conclusion": conclusion,
            "relations": relations,
            "method": method,
        }

    def _reason_with_llm(self, goal, knowledge, feedback):
        known = ", ".join(knowledge) if knowledge else "nothing yet"

        feedback_block = ""
        if feedback:
            notes = "; ".join(
                f"on '{f['goal']}' someone said {f['rating']}"
                + (f" ({f['note']})" if f.get("note") else "")
                for f in feedback
            )
            feedback_block = (
                f"Feedback on related past answers -- take this into "
                f"account, especially anything marked down: {notes}\n\n"
            )

        prompt = (
            f"Goal: {goal}\n\n"
            f"Related knowledge NEXUS already has: {known}.\n\n"
            f"{feedback_block}"
            "Reason step by step about how to approach this goal. State "
            "what's already known, what's uncertain, and one concrete next "
            "action. Under 150 words.\n\n"
            "Then, on their own lines, list 2-4 short entity relationships "
            "your reasoning actually relied on, exactly in this format:\n"
            "RELATIONS:\n"
            "Entity A -> relation -> Entity B\n"
            "Use short, SPECIFIC entity/concept names -- real materials, "
            "techniques, standards, or named things (e.g. 'Fly ash', "
            "'ASTM C150', 'Taylor series') -- not full sentences, and not "
            "vague filler phrases that could apply to any topic (e.g. "
            "'new formula design', 'the approach', 'this method'). Only "
            "entities you genuinely used above."
        )

        kwargs = {"model": self.model} if self.model else {}

        response = ask(
            prompt,
            system=(
                "You are the Reasoning Engine inside NEXUS, a research "
                "assistant system. Be precise, flag uncertainty honestly, "
                "and never state a guess as a fact."
            ),
            **kwargs,
        )

        return self._split(response)

    def _split(self, response):
        """Separates the prose conclusion from RELATIONS lines, so the
        displayed reasoning doesn't show raw 'A -> rel -> B' lines."""
        conclusion_lines = []
        relations = []

        for line in response.splitlines():
            match = _RELATION_LINE.match(line)
            if match:
                a, rel, b = (part.strip().strip("*").strip() for part in match.groups())
                if a and rel and b and max(len(a), len(rel), len(b)) <= _MAX_ENTITY_LEN:
                    relations.append((a, rel, b))
                continue
            # Tolerate markdown emphasis around the marker (**RELATIONS:**,
            # *RELATIONS:*) -- a real response used the bold form and it
            # slipped through an exact-string check straight into the
            # displayed conclusion.
            marker = line.strip().strip("*").strip().upper()
            if marker == "RELATIONS:":
                continue
            conclusion_lines.append(line)

        conclusion = "\n".join(conclusion_lines).strip()
        return conclusion, relations
