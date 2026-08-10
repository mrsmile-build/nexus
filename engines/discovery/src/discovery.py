"""
NEXUS Discovery Engine v0.3

Calls a real LLM to suggest genuinely new angles -- patterns worth
checking, follow-on questions, adjacent ideas, unnamed risks -- when
a provider key is set. Falls back to the v0.1 templated list if the
key is missing, the call fails, or the response can't be parsed.

New in v0.3: returns {"ideas": [...], "method": "llm"/"fallback"}
instead of a bare list. Discovery was the only one of the four LLM-
backed engines with no way to tell whether it actually ran or quietly
fell back -- a real result showed exactly this: Discovery silently
returned the templated fallback (almost certainly a rate-limit hit,
since it runs last after Plan and Reasoning already spent tokens)
with zero visible sign it had happened, while Plan/Reasoning/
Verification all showed their tag correctly.
"""

import re

from core.llm_client import ask, LLMError


class DiscoveryEngine:
    def __init__(self, model=None):
        self.model = model

    def discover(self, observations, goal=None):
        try:
            ideas = self._discover_with_llm(observations, goal)
            if not ideas:
                raise LLMError("LLM response had no parseable numbered ideas")
            return {"ideas": ideas, "method": "llm"}
        except LLMError:
            return {
                "ideas": [f"Possible improvement: {item}" for item in observations],
                "method": "fallback",
            }

    def _discover_with_llm(self, observations, goal):
        context = "; ".join(observations) if observations else "no plan steps yet"

        prompt = (
            (f"Goal: {goal}\n\n" if goal else "")
            + f"Current plan/context: {context}\n\n"
            "Suggest 2-4 genuinely new angles: a pattern worth checking, "
            "a follow-on question, an adjacent idea, or a risk nobody's "
            "named yet. Reply with ONLY a numbered list, one idea per "
            "line, no other text."
        )

        kwargs = {"model": self.model} if self.model else {}
        response = ask(
            prompt,
            system=(
                "You are the Discovery Engine inside NEXUS. Look for "
                "non-obvious connections -- not restatements of what's "
                "already been said."
            ),
            **kwargs,
        )

        ideas = []
        for line in response.splitlines():
            line = line.strip()
            match = re.match(r"^\d+[\.\)]\s*(.+)$", line)
            if match:
                ideas.append(match.group(1).strip())
        return ideas
