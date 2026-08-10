"""
Proves the Learning Engine's feedback actually reaches a later,
related reasoning call -- not just that recording/retrieving feedback
works in isolation (that's test_learning.py). Run via:

    python -m engines.thinking.src.test_learning_loop
"""

from unittest import mock

from engines.thinking.src.thinking import ThinkingEngine

engine = ThinkingEngine(memory_db=":memory:", knowledge_db=":memory:")

# Someone marks a past cement answer as unhelpful, with a specific note.
engine.learning.record_feedback(
    "Design a cheaper cement",
    "down",
    note="Didn't account for local SCM availability",
)

captured_prompt = {}


def _fake_ask(prompt, **kwargs):
    captured_prompt["text"] = prompt
    return "Building on feedback. Next action: check local SCM sourcing first.\n\nRELATIONS:\n"


with mock.patch("engines.reasoning.src.reasoner.ask", side_effect=_fake_ask):
    engine.think("Cement that is 40% cheaper and stronger")

assert "Feedback on related past answers" in captured_prompt["text"], captured_prompt["text"]
assert "SCM availability" in captured_prompt["text"], captured_prompt["text"]
print("PASS: a thumbs-down note on a related goal actually reached the reasoning prompt")

# A goal with no related feedback should not mention feedback at all.
with mock.patch("engines.reasoning.src.reasoner.ask", side_effect=_fake_ask):
    engine.think("Best way to learn a new language")

assert "Feedback on related past answers" not in captured_prompt["text"], captured_prompt["text"]
print("PASS: an unrelated goal's prompt has no feedback section at all")

engine.close()
print("\nAll feedback-loop checks passed.")
