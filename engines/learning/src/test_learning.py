"""
Tests LearningEngine: recording feedback, exact-match retrieval, and
keyword-based retrieval for a related-but-differently-worded goal.
Run via:

    python -m engines.learning.src.test_learning
"""

from engines.memory.src.memory import MemoryEngine
from engines.learning.src.learning import LearningEngine

memory = MemoryEngine(db_path=":memory:")
learning = LearningEngine(memory)

# Nothing recorded yet -> nothing found.
assert learning.relevant_feedback("Design a cheaper cement") == []
print("PASS: no feedback yet returns an empty list")

# Record feedback, then find it by exact match.
learning.record_feedback(
    "Design a cheaper cement", "down", note="Didn't account for local SCM availability"
)
exact = learning.relevant_feedback("Design a cheaper cement")
assert len(exact) == 1 and exact[0]["rating"] == "down", exact
print("PASS: exact-match retrieval works ->", exact[0]["note"])

# A differently-worded but related goal should still find it via keyword search.
related = learning.relevant_feedback("Cement that is 40% cheaper and stronger")
assert len(related) == 1 and related[0]["goal"] == "Design a cheaper cement", related
print("PASS: a related, differently-worded goal finds the same feedback ->", related[0]["goal"])

# An unrelated goal should find nothing.
unrelated = learning.relevant_feedback("Best way to learn a new language")
assert unrelated == [], unrelated
print("PASS: an unrelated goal finds nothing")

# Bad rating value is rejected rather than silently stored.
try:
    learning.record_feedback("Some goal", "sideways")
    raise AssertionError("Expected ValueError for an invalid rating")
except ValueError as error:
    print("PASS: an invalid rating is rejected ->", error)

memory.close()
print("\nAll learning-engine checks passed.")
