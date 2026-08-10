"""
discovery.py now reaches into core/llm_client.py, so run this from
the repo root:

    python -m engines.discovery.src.test_discovery
"""

from engines.discovery.src.discovery import DiscoveryEngine

d = DiscoveryEngine()

# No API key in this environment -> exercises the fallback path.
result = d.discover(["Understand the goal", "Gather knowledge"], goal="Build NEXUS")
print("Method:", result["method"])
for idea in result["ideas"]:
    print("-", idea)
