"""
NEXUS Verification Engine v0.4

Calls a real LLM to assess a conclusion three separate ways when a
provider key is set:
  1. Internal consistency -- logically sound, doesn't contradict
     well-established physics/chemistry/math.
  2. Consistency with the plan -- if a plan is given, does the
     reasoning use the same numbers, units, and assumptions as the
     plan, or does it quietly contradict it (e.g. the plan says
     "per tonne" and the reasoning says "per bag" for the same
     figure)? Verification previously only ever saw the reasoning's
     conclusion in isolation -- it had no way to catch this class of
     bug because it never saw the plan at all.
  3. External verifiability -- does it lean on specific real-world
     facts (named companies/products, current prices, dated specs,
     statistics) that the model can't actually know are current or
     accurate, as opposed to general, timeless domain knowledge.

The v0.1 null/empty check still runs first regardless of any of this.
Falls back to the old "any non-empty conclusion passes" behaviour if
the key is missing or the call fails.
"""

from core.llm_client import ask, LLMError


class Verifier:
    def __init__(self, model=None):
        self.model = model

    def verify(self, conclusion, goal=None, plan_steps=None):
        if conclusion is None or (isinstance(conclusion, str) and conclusion.strip() == ""):
            return {
                "verified": False,
                "confidence": 0.0,
                "issues": ["No conclusion to verify"],
                "needs_external_check": [],
                "method": "basic",
            }

        try:
            parsed = self._verify_with_llm(conclusion, goal, plan_steps)
            parsed["method"] = "llm"
            return parsed
        except LLMError as error:
            return {
                "verified": True,  # matches v0.1: any non-empty conclusion passed
                "confidence": None,
                "issues": [f"LLM verification unavailable: {error}"],
                "needs_external_check": [],
                "method": "fallback",
            }

    def _verify_with_llm(self, conclusion, goal, plan_steps):
        plan_block = ""
        if plan_steps:
            steps_text = "\n".join(f"- {s}" for s in plan_steps)
            plan_block = f"Plan this reasoning is supposed to be consistent with:\n{steps_text}\n\n"

        prompt = (
            (f"Goal: {goal}\n\n" if goal else "")
            + plan_block
            + f"Claim to check: {conclusion}\n\n"
            "Assess this claim three separate ways:\n"
            "1. Internal consistency: is it logically sound, and does it "
            "contradict well-established physics, chemistry, or "
            "mathematics?\n"
            "2. Consistency with the plan above, if one is given: does the "
            "claim use the same numbers, units, and assumptions as the "
            "plan? A mismatch here (e.g. one says a price is per tonne, "
            "the other treats the same number as per bag) is a real "
            "issue even if each half reads fine on its own.\n"
            "3. External verifiability: does it state or rely on specific "
            "facts about real, named entities -- companies, products, "
            "current prices, dated specs, statistics -- that could be "
            "outdated or unverified, as opposed to general, timeless "
            "domain knowledge? A claim can be internally consistent and "
            "still need this.\n\n"
            "Reply in EXACTLY this format, nothing else:\n"
            "VERIFIED: yes or no\n"
            "CONFIDENCE: a number from 0 to 1\n"
            "ISSUES: comma-separated list of SPECIFIC problems you found -- "
            "describe what's actually wrong in a few words (e.g. \"plan's "
            "example uses 50% clinker but reasoning's target is at most "
            "30% clinker replacement\"), never just a one- or two-word "
            "category tag with no explanation. Or 'none' if there are no issues.\n"
            "NEEDS_EXTERNAL_CHECK: short comma-separated list of specific "
            "real-world facts that need independent verification (e.g. "
            "\"current market price\", \"named competitor's actual spec\"), or none"
        )

        kwargs = {"model": self.model} if self.model else {}
        response = ask(
            prompt,
            system=(
                "You are the Verification Engine inside NEXUS. Be "
                "skeptical by default. Flag anything unproven as "
                "unproven, flag any mismatch between the plan and the "
                "reasoning even if each sounds fine alone, and never let "
                "internal consistency stand in for factual currency."
            ),
            **kwargs,
        )

        return self._parse(response)

    def _parse(self, response):
        verified = None
        confidence = None
        issues = []
        needs_external_check = []

        for line in response.splitlines():
            line = line.strip()
            upper = line.upper()
            if upper.startswith("NEEDS_EXTERNAL_CHECK:"):
                raw = line.split(":", 1)[1].strip()
                if raw and raw.lower() != "none":
                    needs_external_check = [i.strip() for i in raw.split(",") if i.strip()]
            elif upper.startswith("VERIFIED:"):
                verified = "yes" in line.split(":", 1)[1].strip().lower()
            elif upper.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":", 1)[1].strip())
                except (ValueError, IndexError):
                    confidence = None
            elif upper.startswith("ISSUES:"):
                raw = line.split(":", 1)[1].strip()
                if raw and raw.lower() != "none":
                    issues = [i.strip() for i in raw.split(",") if i.strip()]

        if verified is None:
            raise LLMError(f"Could not parse verification response: {response!r}")

        return {
            "verified": verified,
            "confidence": confidence,
            "issues": issues,
            "needs_external_check": needs_external_check,
        }
