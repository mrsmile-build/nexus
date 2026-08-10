"""
Tests Verifier's response parser against fake LLM replies -- no real
network call, no API key needed. Run via:

    python -m engines.verification.src.test_verifier_llm

This proves the parsing/wiring logic works. It does not prove the
real Anthropic API call works -- this sandbox has no network access,
so that part is untested until you run it yourself with a real key.
"""

from unittest import mock

from engines.verification.src.verifier import Verifier

# --- Internally consistent, but leaning on unverified real-world facts ---
FAKE_RESPONSE = (
    "VERIFIED: yes\n"
    "CONFIDENCE: 0.75\n"
    "ISSUES: none\n"
    "NEEDS_EXTERNAL_CHECK: current Dangote cement price in Naira, which Dangote strength grade is being compared"
)
with mock.patch("engines.verification.src.verifier.ask", return_value=FAKE_RESPONSE):
    verifier = Verifier()
    result = verifier.verify(
        "This blend beats standard Dangote cement on cost and strength.",
        goal="Design a cheaper stronger cement than Dangote",
    )

assert result["method"] == "llm", result
assert result["verified"] is True, result
assert result["issues"] == [], result
assert len(result["needs_external_check"]) == 2, result
print("PASS: a consistent-but-unverified claim is flagged for external check ->", result["needs_external_check"])

# --- Both internal issues and external-check items at once ---
FAKE_RESPONSE_2 = (
    "VERIFIED: no\n"
    "CONFIDENCE: 0.3\n"
    "ISSUES: no published data on this binder, cost estimate unsourced\n"
    "NEEDS_EXTERNAL_CHECK: none"
)
with mock.patch("engines.verification.src.verifier.ask", return_value=FAKE_RESPONSE_2):
    result = Verifier().verify("This binder cuts cost by 40% with no strength loss.", goal="Design a cheaper cement")

assert result["verified"] is False, result
assert len(result["issues"]) == 2, result
assert result["needs_external_check"] == [], result
print("PASS: internal issues and external-check are tracked independently, not conflated")

# --- Pure timeless domain knowledge needs no external check ---
FAKE_RESPONSE_3 = "VERIFIED: yes\nCONFIDENCE: 0.95\nISSUES: none\nNEEDS_EXTERNAL_CHECK: none"
with mock.patch("engines.verification.src.verifier.ask", return_value=FAKE_RESPONSE_3):
    result = Verifier().verify("Water boils at 100C at sea level.", goal="Explain boiling point")

assert result["needs_external_check"] == [], result
print("PASS: general domain knowledge correctly needs no external check")

# --- Empty conclusion and fallback paths still include the new field ---
basic = Verifier().verify("")
assert basic["needs_external_check"] == [], basic
assert basic["method"] == "basic", basic
print("PASS: the empty-conclusion path includes needs_external_check as an empty list, not a missing key")

print("\nAll verifier checks passed.")
