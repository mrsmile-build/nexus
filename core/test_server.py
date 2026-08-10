"""
Tests core/server.py's render_result() against both a fallback-style
and an llm-style outcome -- no real server or network needed. Run
via:

    python -m core.test_server
"""

from core.server import render_result

fallback_outcome = {
    "goal": "Build NEXUS",
    "plan": {"method": "fallback", "steps": ["Understand the goal"]},
    "reasoning": {"method": "fallback", "conclusion": "Templated conclusion."},
    "verification": {"method": "fallback", "verified": True, "confidence": None, "issues": []},
    "ideas": ["Possible improvement: Understand the goal"],
}
out = render_result(fallback_outcome)
assert "tag fallback" in out
assert "fallback path" in out
assert "confidence" not in out.split("Verified: True")[1].split("</p>")[0]
print("PASS: fallback outcome renders without a confidence figure or crash")

llm_outcome = {
    "goal": "Design a cheaper cement",
    "plan": {"method": "llm", "steps": ["Research binder alternatives"]},
    "reasoning": {"method": "llm", "conclusion": "Fly ash substitution looks promising."},
    "verification": {"method": "llm", "verified": False, "confidence": 0.42, "issues": ["No lab data yet"]},
    "ideas": ["Check regional fly ash availability"],
}
out = render_result(llm_outcome)
assert "tag llm" in out
assert "confidence 0.42" in out
assert "No lab data yet" in out
assert "real LLM call" in out
print("PASS: llm outcome renders confidence and issues correctly")

empty_ideas_outcome = dict(llm_outcome, ideas=[])
out = render_result(empty_ideas_outcome)
assert "none" in out
print("PASS: empty ideas list renders a placeholder instead of a blank list")

from core.server import render_history_entry

llm_entry = {
    "key": "result::Design a cheaper cement",
    "updated_at": "2026-08-03 12:00:00.000",
    "value": {
        "plan": {"method": "llm"},
        "conclusion": "Fly ash substitution looks promising.",
        "verification": {"method": "llm", "issues": ["No lab data yet"]},
        "ideas": ["Check regional fly ash availability"],
    },
}
out = render_history_entry(llm_entry)
assert "Design a cheaper cement" in out
assert "tag llm" in out
assert "No lab data yet" in out
print("PASS: history entry renders goal, tag, and issues from a real-LLM result")

fallback_entry = {
    "key": "result::Build NEXUS",
    "updated_at": "2026-08-03 12:00:01.000",
    "value": {
        "plan": {"method": "fallback"},
        "conclusion": "Templated conclusion.",
        "verification": {"method": "fallback", "issues": []},
        "ideas": [],
    },
}
out = render_history_entry(fallback_entry)
assert "tag fallback" in out
print("PASS: history entry correctly tags a fallback result")

print("\nAll server render checks passed.")

# --- Discovery now shows its own method tag -- previously silent either way ---
discovery_llm = dict(llm_outcome, discovery_method="llm")
out = render_result(discovery_llm)
assert 'Discovery <span class="tag llm">llm</span>' in out, out
print("PASS: Discovery shows an 'llm' tag when it actually used the LLM")

discovery_fallback = dict(llm_outcome, discovery_method="fallback")
out = render_result(discovery_fallback)
assert 'Discovery <span class="tag fallback">fallback</span>' in out, out
print("PASS: Discovery shows a 'fallback' tag when it silently degraded -- no longer invisible")

# Missing entirely (e.g. an old stored result from before this fix) should
# default to fallback rather than crash or claim to be real.
no_discovery_method = {k: v for k, v in llm_outcome.items() if k != "discovery_method"}
out = render_result(no_discovery_method)
assert 'Discovery <span class="tag fallback">fallback</span>' in out, out
print("PASS: a result with no discovery_method at all defaults to 'fallback', not a crash or false 'llm'")

# --- Feedback form renders with the correct goal ---
out = render_result(llm_outcome)
assert 'name="goal" value="Design a cheaper cement"' in out, out
assert 'name="rating" value="up"' in out and 'name="rating" value="down"' in out, out
print("PASS: feedback form renders with the goal and both rating buttons")

# --- External-check callout: shown when present, absent when not ---
needs_check_outcome = dict(llm_outcome)
needs_check_outcome["verification"] = dict(
    llm_outcome["verification"],
    needs_external_check=["current market price", "named competitor's actual spec"],
)
out = render_result(needs_check_outcome)
assert "Verify externally before relying on this" in out
assert "current market price" in out
print("PASS: needs_external_check renders a visible callout, not just a data field")

out = render_result(llm_outcome)  # original fixture has no needs_external_check key at all
assert "check-box" not in out
print("PASS: no callout appears when there's nothing to externally verify")

from core.server import render_history_entry

history_entry = {
    "key": "result::Design a cheaper cement",
    "updated_at": "2026-08-03 12:00:00.000",
    "value": {
        "conclusion": "text",
        "verification": {"issues": [], "needs_external_check": ["current supplier pricing"]},
        "ideas": [],
    },
}
out = render_history_entry(history_entry)
assert "Verify externally before relying on this" in out
print("PASS: history entries show the same callout, not just the live result page")

# --- Context visibility: generic fallback vs. real graph context ---
generic_ctx = dict(llm_outcome)
generic_ctx["reasoning"] = dict(llm_outcome["reasoning"], knowledge_used=["Memory", "Knowledge Graph", "Planning"])
out = render_result(generic_ctx)
assert "first time seeing this topic" in out, out
print("PASS: generic first-time context is labeled as such, not implied to be real prior knowledge")

real_ctx = dict(llm_outcome)
real_ctx["reasoning"] = dict(llm_outcome["reasoning"], knowledge_used=["Portland cement", "Limestone"])
out = render_result(real_ctx)
assert "from the Knowledge Graph" in out and "Portland cement" in out, out
print("PASS: genuine graph context is shown and labeled as coming from the graph")
