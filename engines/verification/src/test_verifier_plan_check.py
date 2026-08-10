"""
Tests that Verifier actually receives and uses the plan, not just the
reasoning conclusion in isolation -- using the real bag-vs-tonne unit
mismatch found in production, not a hypothetical. Run via:

    python -m engines.verification.src.test_verifier_plan_check
"""

from unittest import mock

from engines.verification.src.verifier import Verifier

PLAN_STEPS = ["Formulate a mix design targeting cost below ₦13,000 per tonne"]
CONCLUSION = "Dangote's cement is priced ~13,000 NGN per bag; our blend must beat that."

captured_prompt = {}


def _fake_ask(prompt, **kwargs):
    captured_prompt["text"] = prompt
    return "VERIFIED: no\nCONFIDENCE: 0.85\nISSUES: plan says per tonne, reasoning says per bag for the same figure"


with mock.patch("engines.verification.src.verifier.ask", side_effect=_fake_ask):
    verifier = Verifier()
    result = verifier.verify(CONCLUSION, goal="Beat Dangote's price", plan_steps=PLAN_STEPS)

assert "per tonne" in captured_prompt["text"], "plan steps were never included in the prompt"
assert "13,000 per tonne" in captured_prompt["text"]
print("PASS: the plan is actually included in what gets sent for verification")

assert result["verified"] is False, result
assert any("per bag" in issue for issue in result["issues"]), result
print("PASS: a plan/reasoning unit mismatch is surfaced as an issue ->", result["issues"])

# Without a plan (backward compatible -- e.g. called with no plan_steps
# at all), it should still work exactly as before.
with mock.patch(
    "engines.verification.src.verifier.ask",
    return_value="VERIFIED: yes\nCONFIDENCE: 0.9\nISSUES: none",
):
    no_plan_result = Verifier().verify("A plain conclusion with no plan given.")
assert no_plan_result["verified"] is True, no_plan_result
print("PASS: verification without a plan still works (backward compatible)")

print("\nAll plan-consistency checks passed.")

# Reproduces the exact real bug: the old prompt said "...or
# plan-mismatch problems" as a category description, and a real
# model echoed the bare word "plan-mismatch" back as its entire
# ISSUES answer -- true, but useless, since it never said what
# actually mismatched.
assert "plan-mismatch" not in captured_prompt["text"], (
    "the old bare category word is still in the prompt -- it's exactly "
    "the kind of phrase a model can echo back verbatim as a non-answer"
)
print("PASS: the prompt no longer contains the bare 'plan-mismatch' label a model echoed back")

assert "50% clinker" in captured_prompt["text"] and "30% clinker replacement" in captured_prompt["text"], (
    "the concrete worked example should be in the prompt, showing what a "
    "SPECIFIC issue description looks like"
)
print("PASS: the prompt shows a concrete example of a specific, useful issue description")

# If a model still returns only a bare label despite the improved
# prompt (never fully guaranteed), parsing must not crash -- it just
# won't be a very useful issue string, which is a prompt-quality
# problem, not a parsing bug.
with mock.patch(
    "engines.verification.src.verifier.ask",
    return_value="VERIFIED: no\nCONFIDENCE: 0.8\nISSUES: plan-mismatch",
):
    bare_result = Verifier().verify("Some claim", plan_steps=["Some step"])
assert bare_result["issues"] == ["plan-mismatch"], bare_result
print("PASS: even a bare-label response still parses without crashing (a prompt problem, not a parser one)")
