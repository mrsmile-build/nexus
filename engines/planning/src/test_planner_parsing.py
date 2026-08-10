"""
Tests Planner's numbered-list parser against a fake LLM response --
no real network call, no API key needed. Run via:

    python -m engines.planning.src.test_planner_parsing

This proves the parsing/wiring logic works. It does not prove the
real Anthropic API call works -- this sandbox has no network access,
so that part is untested until you run it yourself with a real key.
"""

from unittest import mock

from engines.planning.src.planner import Planner

FAKE_RESPONSE = (
    "1. Research existing concrete mixes\n"
    "2. Identify cheaper substitute materials\n"
    "3. Model expected strength\n"
    "4. Run a small lab batch\n"
    "5. Compare cost and strength to the baseline\n"
)

with mock.patch("engines.planning.src.planner.ask", return_value=FAKE_RESPONSE):
    planner = Planner()
    plan = planner.create_plan("Design a cheaper cement")

assert plan["method"] == "llm", plan
assert len(plan["steps"]) == 5, plan
assert plan["steps"][0] == "Research existing concrete mixes", plan

print("PASS: numbered-list parser extracted", len(plan["steps"]), "steps ->")
for step in plan["steps"]:
    print(" -", step)
