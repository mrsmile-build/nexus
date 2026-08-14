"""
Tests core/export_history.py against a real (temp-file) database,
not mocked -- SQLite persistence and real HTML rendering both need
to actually work together for this to be worth anything. Run via:

    python -m core.test_export_history
"""

import os

from core.export_history import export
from engines.memory.src.memory import MemoryEngine

TEST_DB = "test_export_history.db"
TEST_OUTPUT = "test_export_history_output.html"

for path in (TEST_DB, TEST_OUTPUT):
    if os.path.exists(path):
        os.remove(path)

# Nothing recorded yet -> a real file with an empty-state message, not a crash.
count = export(db_path=TEST_DB, output_path=TEST_OUTPUT)
assert count == 0, count
with open(TEST_OUTPUT, encoding="utf-8") as f:
    empty_page = f.read()
assert "Nothing recorded yet" in empty_page, empty_page
assert "<html>" in empty_page and "</html>" in empty_page
print("PASS: exporting with no history yet writes a real, valid, empty-state page")

# Seed real results the way ThinkingEngine actually would, then export again.
memory = MemoryEngine(db_path=TEST_DB)
memory.store(
    "result::Design a cheaper cement",
    {
        "plan": {"method": "llm", "steps": ["Research SCMs"]},
        "conclusion": "Fly ash substitution looks promising.",
        "verification": {"method": "llm", "verified": True, "issues": []},
        "ideas": ["Check regional fly ash availability"],
    },
)
memory.close()

count = export(db_path=TEST_DB, output_path=TEST_OUTPUT)
assert count == 1, count
with open(TEST_OUTPUT, encoding="utf-8") as f:
    page = f.read()
assert "Design a cheaper cement" in page, page
assert "Fly ash substitution looks promising" in page, page
assert "tag llm" in page, page
print("PASS: a real seeded result renders correctly in the exported static page")

# The privacy-relevant claim in the docstring/output should actually
# be true: no API key or provider name should ever appear in the
# exported file.
assert "GROQ_API_KEY" not in page and "sk-" not in page, page
print("PASS: no credential-shaped text ends up in the exported (public) file")

os.remove(TEST_DB)
os.remove(TEST_OUTPUT)
print("\nAll export-history checks passed.")
