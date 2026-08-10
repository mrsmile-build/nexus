"""
Tests DiscoveryEngine's parser against a fake LLM reply -- no real
network call, no API key needed. Run via:

    python -m engines.discovery.src.test_discovery_llm

This proves the parsing/wiring logic works. It does not prove the
real Anthropic API call works -- this sandbox has no network access,
so that part is untested until you run it yourself with a real key.
"""

from unittest import mock

from engines.discovery.src.discovery import DiscoveryEngine

FAKE_RESPONSE = (
    "1. Check whether fly ash could replace part of the binder\n"
    "2. Nobody has priced in transport cost for the substitute material\n"
)

with mock.patch("engines.discovery.src.discovery.ask", return_value=FAKE_RESPONSE):
    discovery = DiscoveryEngine()
    result = discovery.discover(["Research existing concrete mixes"], goal="Design a cheaper cement")

assert result["method"] == "llm", result
assert len(result["ideas"]) == 2, result
assert result["ideas"][0] == "Check whether fly ash could replace part of the binder", result

print("PASS: Discovery parsed", len(result["ideas"]), "(mocked) ideas, method reported as 'llm' ->")
for idea in result["ideas"]:
    print("-", idea)

# Fallback should report its method too, not just the templated ideas.
from core.llm_client import LLMError

with mock.patch("engines.discovery.src.discovery.ask", side_effect=LLMError("no key")):
    fallback = DiscoveryEngine().discover(["Understand the goal"], goal="Build NEXUS")
assert fallback["method"] == "fallback", fallback
assert fallback["ideas"] == ["Possible improvement: Understand the goal"], fallback
print("PASS: fallback mode reports method='fallback', not silently indistinguishable from real")
