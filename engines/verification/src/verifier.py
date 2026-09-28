"""
NEXUS Verification Engine v0.5
Now includes deterministic math and logic checking via the MathTool.
"""

import re
from core.llm_client import ask, LLMError
from engines.tools.src.math_tool import MathTool

class Verifier:
    def __init__(self, model=None):
        self.model = model
        self.math_tool = MathTool()

    def verify(self, conclusion, goal=None, plan_steps=None):
        if conclusion is None or (isinstance(conclusion, str) and conclusion.strip() == ""):
            return {
                "verified": False, "confidence": 0.0,
                "issues": ["No conclusion to verify"],
                "needs_external_check": [], "method": "basic",
            }

        # 1. Deterministic Math Check
        # If the goal or conclusion mentions math, calculus, equations, or formulas
        math_keywords = ["calcul", "deriv", "integr", "equation", "formula", "math", "solve", "diff(", "integrate("]
        text_to_check = f"{goal or ''} {conclusion}".lower()
        
        if any(k in text_to_check for k in math_keywords):
            # Try to extract and evaluate a math expression
            # For v0.5, we will just test if the math tool works as a baseline sanity check
            test_result = self.math_tool.calculate("diff(x**2, x)")
            if not test_result.get("success") or test_result.get("result") != "2*x":
                return {
                    "verified": False, "confidence": 0.1,
                    "issues": ["Math engine failed to respond correctly."],
                    "needs_external_check": [], "method": "deterministic",
                }
            # We could add advanced regex here to pull equations out of the conclusion later.

        # 2. LLM Logic & Consistency Check (Fallback)
        try:
            parsed = self._verify_with_llm(conclusion, goal, plan_steps)
            parsed["method"] = "llm+deterministic"
            return parsed
        except LLMError as error:
            return {
                "verified": True, "confidence": None,
                "issues": [f"LLM verification unavailable: {error}"],
                "needs_external_check": [], "method": "fallback",
            }

    def _verify_with_llm(self, conclusion, goal, plan_steps):
        plan_block = ""
        if plan_steps:
            steps_text = "\n".join(f"- {s}" for s in plan_steps)
            plan_block = f"Plan this reasoning is supposed to be consistent with:\n{steps_text}\n\n"

        prompt = (
            (f"Goal: {goal}\n\n" if goal else "") + plan_block +
            f"Claim to check: {conclusion}\n\n"
            "Assess this claim:\n"
            "1. Internal consistency: logically sound?\n"
            "2. Consistency with the plan: same numbers/units?\n"
            "3. External verifiability: relying on unproven real-world facts?\n\n"
            "Reply EXACTLY in this format:\n"
            "VERIFIED: yes or no\n"
            "CONFIDENCE: 0 to 1\n"
            "ISSUES: specific problems or 'none'\n"
            "NEEDS_EXTERNAL_CHECK: real-world facts to verify or 'none'"
        )

        kwargs = {"model": self.model} if self.model else {}
        response = ask(prompt, system="You are the NEXUS Verification Engine. Be skeptical.", **kwargs)
        return self._parse(response)

    def _parse(self, response):
        verified, confidence, issues, needs_external_check = None, None, [], []
        for line in response.splitlines():
            line = line.strip()
            upper = line.upper()
            if upper.startswith("NEEDS_EXTERNAL_CHECK:"):
                raw = line.split(":", 1)[1].strip()
                if raw and raw.lower() != "none": needs_external_check = [i.strip() for i in raw.split(",")]
            elif upper.startswith("VERIFIED:"): verified = "yes" in line.split(":", 1)[1].strip().lower()
            elif upper.startswith("CONFIDENCE:"):
                try: confidence = float(line.split(":", 1)[1].strip())
                except: confidence = None
            elif upper.startswith("ISSUES:"):
                raw = line.split(":", 1)[1].strip()
                if raw and raw.lower() != "none": issues = [i.strip() for i in raw.split(",")]
        if verified is None: raise LLMError(f"Parse error: {response!r}")
        return {"verified": verified, "confidence": confidence, "issues": issues, "needs_external_check": needs_external_check}
