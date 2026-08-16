"""
NEXUS Static History Export v0.1

Generates a static HTML snapshot of everything in Memory's history --
suitable for GitHub Pages, which can only ever serve static files. It
can never run this project's actual backend (that needs Python, a
real API key, and SQLite; none of that exists in static hosting).

This is NOT NEXUS "hosted." It's a read-only snapshot of what NEXUS
has already answered, frozen at export time. Asking a new question
still only works locally, via `python -m core.server`.

Privacy: once this is committed and pushed with GitHub Pages enabled,
it's public. Anyone with the link can see every question and answer
in it, at the time of the last export.

Run:
    python -m core.export_history

Writes docs/index.html (alongside your existing docs/nexus_vision.md
-- doesn't touch it). One-time setup after the first export:
GitHub repo -> Settings -> Pages -> Deploy from a branch -> main ->
/docs. After that, re-running this script and pushing updates the
live page.
"""

import os

from core.server import STYLE, render_history_entry
from engines.memory.src.memory import MemoryEngine

OUTPUT_PATH = "docs/index.html"
MAX_ENTRIES = 1000  # generous ceiling; revisit if history genuinely exceeds this

REPO_URL = "https://github.com/mrsmile-build/nexus"

PAGE_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NEXUS &middot; History</title>
<style>{style}</style>
</head>
<body>
<div class="wrap">
  <p class="brand">Nexus &middot; static snapshot &middot; read-only</p>
  <p class="nav"><a href="{repo_url}">View the source on GitHub &rarr;</a></p>
  <h1>NEXUS History</h1>
  <p class="hint">A snapshot of past questions and answers, frozen at export
  time. This page can't think about new ones &mdash; that needs a real API
  key and a running Python backend, neither of which static hosting can
  hold. Search below works entirely in your browser; everything on this
  page is already here, nothing is fetched.</p>
  <input type="text" id="search-box" class="search-box" placeholder="Search past questions and answers" oninput="nexusFilter()">
  <p id="no-results" class="empty" style="display:none">No entries match that search.</p>
  {entries_html}
</div>
<script>
function nexusFilter() {{
  var term = document.getElementById('search-box').value.toLowerCase();
  var entries = document.querySelectorAll('.entry');
  var visible = 0;
  entries.forEach(function(entry) {{
    var matches = entry.textContent.toLowerCase().indexOf(term) !== -1;
    entry.style.display = matches ? '' : 'none';
    if (matches) visible++;
  }});
  document.getElementById('no-results').style.display =
    (visible === 0 && term !== '') ? '' : 'none';
}}
</script>
</body>
</html>"""


def export(db_path="data/memory.db", output_path=OUTPUT_PATH):
    memory = MemoryEngine(db_path=db_path)
    entries = memory.recent(prefix="result::", limit=MAX_ENTRIES)
    memory.close()

    entries_html = (
        "".join(render_history_entry(e, include_delete=False) for e in entries)
        if entries
        else '<p class="empty">Nothing recorded yet.</p>'
    )

    directory = os.path.dirname(output_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(PAGE_TEMPLATE.format(style=STYLE, repo_url=REPO_URL, entries_html=entries_html))

    return len(entries)


def main():
    count = export()
    print(f"Wrote {OUTPUT_PATH} with {count} entries.")
    print("git add docs/index.html && git commit -m 'Update history snapshot' && git push")


if __name__ == "__main__":
    main()
