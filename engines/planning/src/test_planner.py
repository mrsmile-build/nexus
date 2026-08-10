"""
planner.py now reaches into core/llm_client.py, so this can't be run
by cd-ing into this folder anymore (unlike test_graph.py etc). Run it
from the repo root instead:

    python -m engines.planning.src.test_planner
"""

from engines.planning.src.planner import Planner

planner = Planner()

plan = planner.create_plan("Build an AI assistant")

print(plan)
