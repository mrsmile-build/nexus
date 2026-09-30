"""
NEXUS Truth Engine v0.1
Adversarial self-verification: every answer is attacked by a critic pass,
then rebuilt. Enforces terminology accuracy, no category mixing,
science vs tradition vs disputed separation, no overconfidence.
"""
from core.llm_client import ask

class TruthEngine:
    def verify(self, question: str, draft: str):
        critic = f"""You are NEXUS's ruthless internal fact-checker. The user asked: '{question}'. A draft answer was produced:
---
{draft[:6000]}
---
Attack it. List EVERY problem:
1. Factual or terminology errors (names, translations, style/field attributions).
2. Mixed categories presented as one kind.
3. Overconfident claims lacking evidence (health, legal, historical, 'proven' claims).
4. Traditional/belief claims presented as scientific fact, or science dismissing belief disrespectfully.
5. Missing nuance (jurisdiction, context, 'best for WHAT exactly?').
If clean, say 'NO MAJOR ISSUES'. Be concise and brutal."""
        critique = ask(critic, max_tokens=1200)

        revise = f"""You are NEXUS. The user asked: '{question}'.
Your draft answer:
---
{draft[:6000]}
---
Your internal fact-checker found:
---
{critique[:3000]}
---
Rewrite the final answer:
- Fix every valid issue. Keep what was correct and useful.
- Label claims where relevant: [VERIFIED], [TRADITIONAL BELIEF], [DISPUTED], [UNCERTAIN].
- End with a short 'Confidence:' note - what is solid, what needs verification.
- Speak naturally. Complete fully, never cut off."""
        final = ask(revise, max_tokens=4000)
        return final, critique
