"""
Tests Reasoner's RELATIONS parsing -- separating prose from extracted
entity relationships -- against a mocked LLM response. No real
network call, no API key needed. Run via:

    python -m engines.reasoning.src.test_reasoner_relations
"""

from unittest import mock

from engines.reasoning.src.reasoner import Reasoner

FAKE_RESPONSE = """Known: fly ash is a common Portland cement substitute with pozzolanic properties. Uncertain: regional pricing.
Concrete next action: compare fly ash against slag for this region.

RELATIONS:
Fly ash -> substitutes for -> Portland cement
Fly ash -> reduces -> production cost
This is not a relation line, just prose that happens to have a dash - in it.
"""

with mock.patch("engines.reasoning.src.reasoner.ask", return_value=FAKE_RESPONSE):
    reasoner = Reasoner()
    result = reasoner.reason("Design a cheaper cement", ["Concrete"])

assert result["method"] == "llm", result
assert "RELATIONS:" not in result["conclusion"], result["conclusion"]
assert "Fly ash -> substitutes" not in result["conclusion"], result["conclusion"]
assert "Known: fly ash is a common Portland cement substitute" in result["conclusion"]
print("PASS: RELATIONS lines are stripped out of the displayed conclusion")

assert result["relations"] == [
    ("Fly ash", "substitutes for", "Portland cement"),
    ("Fly ash", "reduces", "production cost"),
], result["relations"]
print("PASS: relation lines are parsed into (source, relation, target) tuples ->", result["relations"])

# A single stray dash in normal prose should never be mistaken for a relation.
assert not any("dash" in r[0].lower() for r in result["relations"])
print("PASS: prose containing a plain dash is not misparsed as a relation")

# Fallback mode should return an empty relations list, not crash.
with mock.patch(
    "engines.reasoning.src.reasoner.ask",
    side_effect=__import__("core.llm_client", fromlist=["LLMError"]).LLMError("no key"),
):
    fallback_result = Reasoner().reason("Build NEXUS", [])
assert fallback_result["relations"] == [], fallback_result
print("PASS: fallback mode returns an empty relations list")

print("\nAll reasoner-relation checks passed.")

# Reproduces the exact real failure: model wrapped the marker in
# markdown bold and provided no actual relations after it, so the
# raw "**RELATIONS:**" showed up in the displayed conclusion.
BOLD_MARKER_RESPONSE = (
    "Known: SCMs can replace clinker. Uncertain: exact blend ratios.\n"
    "Next action: gather local prices.\n\n"
    "**RELATIONS:**"
)
with mock.patch("engines.reasoning.src.reasoner.ask", return_value=BOLD_MARKER_RESPONSE):
    result = Reasoner().reason("Design a cheaper cement", ["Cement"])
assert "RELATIONS" not in result["conclusion"], result["conclusion"]
assert result["relations"] == [], result["relations"]
print("PASS: a bold-wrapped RELATIONS marker with nothing after it is stripped, not displayed")

# The prompt itself should discourage vague filler-phrase entity names,
# not just rely on filtering them out later at search time.
captured = {}
with mock.patch("engines.reasoning.src.reasoner.ask", side_effect=lambda p, **k: (captured.update(text=p), FAKE_RESPONSE)[1]):
    Reasoner().reason("Design a cheaper cement", [])
assert "vague filler phrases" in captured["text"], captured["text"]
assert "new formula design" in captured["text"].lower(), captured["text"]
print("PASS: the prompt explicitly discourages vague entity names, with a concrete bad example")
