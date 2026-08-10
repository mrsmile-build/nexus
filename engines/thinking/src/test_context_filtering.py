"""
Reproduces the exact bug found in real use: a calculus question
containing the word "formula" pulled in unrelated cement context
because "formula" was a substring of "high-clinker Portland formula".
Proves the fix without breaking genuine topical matches. Run via:

    python -m engines.thinking.src.test_context_filtering
"""

from engines.thinking.src.thinking import ThinkingEngine

engine = ThinkingEngine(memory_db=":memory:", knowledge_db=":memory:")

# Seed the graph exactly as real cement reasoning would have.
engine.knowledge.add_edge("Fly ash", "substitutes for", "high-clinker Portland formula")
engine.knowledge.add_edge("Dangote cement", "uses", "high-clinker Portland formula")

# The exact real query that caused the bug.
context = engine._gather_context("Lets create a new simple formula to solve calculus")
assert "high-clinker Portland formula" not in context, context
assert "Dangote cement" not in context, context
assert context == ["Memory", "Knowledge Graph", "Planning"], context
print("PASS: 'formula' no longer pulls in unrelated cement context ->", context)

# A genuinely relevant match on a specific term should still work --
# this isn't a blunt fix that breaks the feature it's protecting.
context2 = engine._gather_context("What is the cheapest source of fly ash")
assert "high-clinker Portland formula" in context2, context2
print("PASS: a real topical match (fly ash) still works ->", context2)

# The exact second leak found in real use: "design" pulling in an
# unrelated "New formula design" node from a prior calculus answer
# into a cement question.
engine.knowledge.add_edge("Reasoning", "produced", "New formula design")
context3 = engine._gather_context("Design a cheaper cement and give ingredients")
assert "New formula design" not in context3, context3
print("PASS: 'design' no longer pulls in an unrelated node ->", context3)

engine.close()
print("\nAll context-filtering checks passed.")
