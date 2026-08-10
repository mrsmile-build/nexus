"""
NEXUS Learning Engine v0.1

The README lists "User feedback" as an input and "Better reasoning
strategies" as an output -- this is the first actual implementation
of that, and the last of the originally-named engines to get real
code (Tools Engine is still README-only after this).

Stores a thumbs up/down (+ optional note) against a goal, and can
surface relevant past feedback for a related future goal, using the
same keyword-search approach as the Knowledge Graph's context
lookup. Feedback lives in the same Memory store as everything else
-- no new persistence layer needed.
"""

_GENERIC_TERMS = {
    "formula", "formulas", "method", "methods", "approach", "approaches",
    "process", "processes", "system", "systems", "result", "results",
    "structure", "structures", "model", "models", "technique", "techniques",
    "strategy", "strategies", "solution", "solutions", "tool", "tools",
    "framework", "concept", "concepts", "idea", "ideas", "factor", "factors",
    "aspect", "aspects", "element", "elements", "component", "components",
    "type", "types", "kind", "kinds", "form", "forms", "way", "ways",
}


class LearningEngine:
    def __init__(self, memory):
        self.memory = memory

    def record_feedback(self, goal, rating, note=None):
        """rating: 'up' or 'down'."""
        if rating not in ("up", "down"):
            raise ValueError(f"rating must be 'up' or 'down', got {rating!r}")
        self.memory.store(f"feedback::{goal}", {"rating": rating, "note": note})

    def relevant_feedback(self, goal, limit=5):
        """Past feedback for goals related to this one -- same
        keyword-search idea as ThinkingEngine._gather_context, kept
        separate since it searches Memory's feedback entries, not the
        Knowledge Graph."""
        found = []
        seen_goals = set()

        # Exact match first.
        exact = self.memory.retrieve(f"feedback::{goal}")
        if exact:
            seen_goals.add(goal.lower())
            found.append({"goal": goal, **exact})

        for word in goal.split():
            word = word.strip(".,!?:;\"'()").lower()
            if len(word) <= 3 or word in _GENERIC_TERMS:
                continue
            for entry in self.memory.recent(prefix="feedback::", contains=word, limit=limit):
                past_goal = entry["key"][len("feedback::"):]
                if past_goal.lower() not in seen_goals:
                    seen_goals.add(past_goal.lower())
                    found.append({"goal": past_goal, **entry["value"]})

        return found[:limit]
