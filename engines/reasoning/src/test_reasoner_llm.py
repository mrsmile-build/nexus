"""
Tests Reasoner against a fake LLM response -- no real network call,
no API key needed. Run via:

    python -m engines.reasoning.src.test_reasoner_llm

This proves the wiring works. It does not prove the real Anthropic
API call works -- this sandbox has no network access, so that part is
untested until you run it yourself with a real key.
"""

from unittest import mock

from engines.reasoning.src.reasoner import Reasoner

FAKE_RESPONSE = (
    "Known: concrete strength mainly comes from the cement-to-water ratio "
    "and aggregate quality. Uncertain: which cheaper substitute binder "
    "keeps compressive strength within spec. Next action: pull three "
    "candidate substitute binders from the knowledge graph and compare "
    "their published compressive strength data."
)

with mock.patch("engines.reasoning.src.reasoner.ask", return_value=FAKE_RESPONSE):
    reasoner = Reasoner()
    result = reasoner.reason(
        "Design a cheaper cement", ["Concrete", "Materials Science"]
    )

assert result["method"] == "llm", result
assert result["conclusion"] == FAKE_RESPONSE, result

print("PASS: Reasoner used the (mocked) LLM response ->")
print(result["conclusion"])
