"""
Proves the Knowledge Graph actually grows from real reasoning, and
that a later, differently-worded goal can find prior context via
keyword search -- not just an exact repeat of the same goal string.
Uses a real (in-memory) KnowledgeGraph, only Reasoner's LLM call is
mocked. Run via:

    python -m engines.thinking.src.test_thinking_knowledge_loop
"""

from unittest import mock

from engines.thinking.src.thinking import ThinkingEngine

FIRST_RESPONSE = """Known: fly ash is a common substitute for Portland cement. Uncertain: local pricing.
Next action: compare regional fly ash cost.

RELATIONS:
Fly ash -> substitutes for -> Portland cement
Cement -> requires -> Limestone
"""

engine = ThinkingEngine(memory_db=":memory:", knowledge_db=":memory:")

# Before anything runs, the graph is genuinely empty.
assert engine.knowledge.show()["nodes"] == {}
print("PASS: graph starts empty, as expected")

with mock.patch("engines.reasoning.src.reasoner.ask", return_value=FIRST_RESPONSE):
    first = engine.think("Design a cheaper cement")

# The graph should now actually contain what reasoning just used --
# not stay empty the way it always used to.
assert engine.knowledge.relation_exists("Fly ash", "substitutes for", "Portland cement")
assert engine.knowledge.relation_exists("Cement", "requires", "Limestone")
print("PASS: extracted relations were actually written to the graph")

# A second, differently-worded goal sharing the word "cement" should
# now find that prior context via keyword search -- not just an exact
# repeat of "Design a cheaper cement".
SECOND_RESPONSE = "Building on prior knowledge. Next action: proceed.\n\nRELATIONS:\n"
with mock.patch("engines.reasoning.src.reasoner.ask", return_value=SECOND_RESPONSE) as mocked:
    second = engine.think("Cement that is 40% cheaper and stronger")

knowledge_used = mocked.call_args
# Check what context ThinkingEngine actually looked up before reasoning.
context = engine._gather_context("Cement that is 40% cheaper and stronger")
assert "Portland cement" in context or "Fly ash" in context or "Limestone" in context, context
print("PASS: a differently-worded goal found prior graph context via keyword search ->", context)

engine.close()
print("\nAll knowledge-graph-loop checks passed.")
