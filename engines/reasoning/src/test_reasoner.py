"""
reasoner.py now reaches into core/llm_client.py, so this can't be run
by cd-ing into this folder anymore (unlike test_graph.py etc). Run it
from the repo root instead:

    python -m engines.reasoning.src.test_reasoner
"""

from engines.reasoning.src.reasoner import Reasoner

ai = Reasoner()

result = ai.reason(
    "Build NEXUS",
    ["Memory", "Knowledge Graph", "Planning"]
)

print(result)
