"""
Run from the repo root (not this folder), because ThinkingEngine
imports other engines via their full package path:

    python -m engines.thinking.src.test_thinking
"""

from engines.thinking.src.thinking import ThinkingEngine

engine = ThinkingEngine(memory_db=":memory:", knowledge_db=":memory:")

outcome = engine.think("Discover a stronger concrete")

print("Plan steps:", outcome["plan"]["steps"])
print("Conclusion:", outcome["reasoning"]["conclusion"])
print("Verification:", outcome["verification"])
print("Ideas:", outcome["ideas"])

engine.close()
