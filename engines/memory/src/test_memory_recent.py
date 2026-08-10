"""
Tests MemoryEngine.recent() -- ordering, prefix filtering, and
search -- without touching store/retrieve/forget/all, which already
have their own tests. Run via:

    python -m engines.memory.src.test_memory_recent
"""

from memory import MemoryEngine
import time

mem = MemoryEngine(db_path=":memory:")

mem.store("result::Design a cheaper cement", {"conclusion": "Fly ash substitution looks promising."})
time.sleep(0.01)
mem.store("result::Solve calculus problems", {"conclusion": "What level are you at?"})
time.sleep(0.01)
mem.store("last_goal", "Solve calculus problems")

# Most recent first
recent = mem.recent(limit=10)
assert recent[0]["key"] == "last_goal", recent  # stored last
assert len(recent) == 3, recent
print("PASS: recent() orders most-recent-first ->", [r["key"] for r in recent])

# Prefix filtering excludes last_goal
results_only = mem.recent(prefix="result::")
assert len(results_only) == 2, results_only
assert all(r["key"].startswith("result::") for r in results_only)
print("PASS: prefix filtering works ->", [r["key"] for r in results_only])

# Search matches inside the value, not just the key
cement_hits = mem.recent(prefix="result::", contains="fly ash")
assert len(cement_hits) == 1, cement_hits
assert "cement" in cement_hits[0]["key"]
print("PASS: search matches inside stored values ->", cement_hits[0]["key"])

# Search with no matches returns an empty list, not an error
no_hits = mem.recent(contains="nonexistent-term-xyz")
assert no_hits == [], no_hits
print("PASS: a search with no matches returns an empty list")

mem.close()
print("\nAll recent()/search checks passed.")
