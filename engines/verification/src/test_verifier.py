"""
verifier.py now reaches into core/llm_client.py, so run this from the
repo root:

    python -m engines.verification.src.test_verifier
"""

from engines.verification.src.verifier import Verifier

v = Verifier()

print("Empty conclusion:", v.verify(""))
print("None conclusion:", v.verify(None))
print("Real conclusion (no API key in this environment -> fallback):")
print(v.verify("The bridge can hold 40 tons.", goal="Design a bridge"))
