"""
NEXUS Planning Engine v0.2

Calls a real LLM to produce a goal-specific plan when
ANTHROPIC_API_KEY is set. Falls back to the v0.1 static 5-step plan
if the key is missing, the call fails, or the response can't be
parsed into steps.
"""

import re

from core.llm_client import ask, LLMError

FALLBACK_STEPS = [
    "Understand the goal",
    "Gather knowledge",
    "Create strategy",
    "Execute tasks",
    "Verify results",
]


class Planner:
    def __init__(self, model=None):
        self.model = model

    def create_plan(self, goal):
        try:
            steps = self._plan_with_llm(goal)
            if not steps:
                raise LLMError("LLM response had no parseable numbered steps")
            method = "llm"
        except LLMError:
            steps = list(FALLBACK_STEPS)
            method = "fallback"

        return {"goal": goal, "steps": steps, "method": method}

    def _plan_with_llm(self, goal):
        prompt = (
            f"Goal: {goal}\n\n"
            "Break this into 4-6 concrete, ordered steps to work toward "
            "it. Reply with ONLY a numbered list, one step per line, no "
            "other text."
        )

        kwargs = {"model": self.model} if self.model else {}

        response = ask(
            prompt,
            system=(
                "You are the Planning Engine inside NEXUS, a research "
                "assistant system. Produce short, concrete, ordered "
                "steps -- no commentary."
            ),
            **kwargs,
        )

        steps = []
        for line in response.splitlines():
            line = line.strip()
            match = re.match(r"^\d+[\.\)]\s*(.+)$", line)
            if match:
                steps.append(match.group(1).strip())

        return steps
