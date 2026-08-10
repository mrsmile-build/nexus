"""
NEXUS Web UI v0.1

A minimal local server so you can use NEXUS from your phone's browser
instead of reading terminal output. Stdlib only -- no pip install.

Run:
    python -m core.server

Then open http://localhost:8765 in your phone's browser while Termux
keeps running. Ctrl+C in Termux to stop it.

This never leaves your device. Nothing is hosted anywhere, nobody
else can reach it, and no API key ever touches the browser -- every
LLM call still happens server-side in Python, exactly like
core/nexus.py. A browser is just a nicer way to see the same
ThinkingEngine you already have.
"""

import html
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, unquote_plus, urlparse

from engines.thinking.src.thinking import ThinkingEngine

PORT = 8765

STYLE = """
:root {
  --bg: #12151c;
  --surface: #1b2029;
  --border: #2a3040;
  --text: #e8e6e0;
  --muted: #8b92a3;
  --teal: #4fbdaa;
  --amber: #d99a4e;
  --rust: #d2685a;
  --mono: ui-monospace, "SF Mono", "Cascadia Code", Consolas, monospace;
  --sans: system-ui, -apple-system, "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--sans);
  margin: 0;
  padding: 24px 16px 64px;
  line-height: 1.5;
}
.wrap { max-width: 640px; margin: 0 auto; }
.brand {
  font-family: var(--mono);
  font-size: 13px;
  letter-spacing: 0.12em;
  color: var(--muted);
  text-transform: uppercase;
  margin: 0 0 4px;
}
h1 {
  font-family: var(--mono);
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 24px;
  letter-spacing: -0.01em;
}
form { display: flex; gap: 8px; margin-bottom: 8px; }
input[type=text] {
  flex: 1;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-family: var(--sans);
  font-size: 16px;
  padding: 12px 14px;
}
input[type=text]:focus {
  outline: 2px solid var(--teal);
  outline-offset: 1px;
}
button {
  background: var(--teal);
  border: none;
  border-radius: 8px;
  color: #0a1512;
  font-family: var(--sans);
  font-size: 16px;
  font-weight: 600;
  padding: 12px 20px;
  cursor: pointer;
}
button:active { opacity: 0.85; }
.hint {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--muted);
  margin: 0 0 32px;
}
.stage {
  position: relative;
  padding: 0 0 24px 20px;
  border-left: 2px solid var(--border);
  margin-left: 6px;
}
.stage:last-child { border-left-color: transparent; padding-bottom: 0; }
.stage::before {
  content: "";
  position: absolute;
  left: -7px;
  top: 4px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--surface);
  border: 2px solid var(--border);
}
.stage.on::before { border-color: var(--teal); background: var(--teal); }
.label {
  font-family: var(--mono);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.tag {
  font-family: var(--mono);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--border);
}
.tag.llm { color: var(--teal); border-color: var(--teal); }
.tag.fallback, .tag.basic { color: var(--amber); border-color: var(--amber); }
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
}
.card p { margin: 0; }
.card ol, .card ul { margin: 0; padding-left: 20px; }
.card li { margin-bottom: 6px; }
.card li:last-child { margin-bottom: 0; }
.meta { font-family: var(--mono); font-size: 13px; color: var(--muted); margin-top: 8px; }
.issue { color: var(--rust); }
.empty { color: var(--muted); font-style: italic; }
.check-box {
  margin-top: 10px;
  padding: 10px 12px;
  border: 1px solid var(--amber);
  border-radius: 8px;
  background: rgba(217, 154, 78, 0.08);
}
.check-box-label {
  font-family: var(--mono);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--amber);
  margin: 0 0 6px;
}
.check-box ul { margin: 0; padding-left: 18px; }
.check-box li { margin-bottom: 4px; }
.check-box li:last-child { margin-bottom: 0; }
.nav { margin: 0 0 20px; }
.nav a { color: var(--teal); text-decoration: none; font-family: var(--mono); font-size: 13px; }
.nav a:hover { text-decoration: underline; }
.search-form { display: flex; gap: 8px; margin-bottom: 20px; }
.entry { margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
.entry:last-child { border-bottom: none; }
.entry-goal { font-size: 17px; font-weight: 600; margin: 0 0 4px; }
.entry-time { font-family: var(--mono); font-size: 12px; color: var(--muted); margin: 0 0 10px; }
.feedback-form { margin-top: 16px; display: flex; align-items: center; gap: 10px; }
.feedback-form button {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text);
  font-size: 18px;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
}
.feedback-form button:active { border-color: var(--teal); }
.feedback-note { color: var(--teal); font-family: var(--mono); font-size: 13px; margin-top: 16px; }
"""

PAGE_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NEXUS</title>
<style>{style}</style>
</head>
<body>
<div class="wrap">
  <p class="brand">Nexus &middot; local &middot; not hosted anywhere</p>
  <p class="nav"><a href="/history">&larr; History</a></p>
  <h1>What should NEXUS think about?</h1>
  <form method="POST" action="/think">
    <input type="text" name="goal" placeholder="e.g. Design a cheaper cement" value="{goal}" autofocus>
    <button type="submit">Think</button>
  </form>
  <p class="hint">Runs the same pipeline as `python -m core.nexus` &mdash; this is just a window into it.</p>
  {result_html}
</div>
</body>
</html>"""

HISTORY_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NEXUS &middot; History</title>
<style>{style}</style>
</head>
<body>
<div class="wrap">
  <p class="brand">Nexus &middot; local &middot; not hosted anywhere</p>
  <p class="nav"><a href="/">&larr; New question</a></p>
  <h1>History</h1>
  <form class="search-form" method="GET" action="/history">
    <input type="text" name="q" placeholder="Search past questions and answers" value="{query}">
    <button type="submit">Search</button>
  </form>
  {entries_html}
</div>
</body>
</html>"""


def _tag(method):
    return f'<span class="tag {html.escape(method)}">{html.escape(method)}</span>'


def render_result(outcome):
    if outcome is None:
        return ""

    goal = outcome["goal"]
    plan = outcome["plan"]
    reasoning = outcome["reasoning"]
    verification = outcome["verification"]
    ideas = outcome["ideas"]

    steps_html = "".join(f"<li>{html.escape(s)}</li>" for s in plan["steps"])

    issues = verification.get("issues") or []
    issues_html = "".join(f'<li class="issue">{html.escape(i)}</li>' for i in issues)
    confidence = verification.get("confidence")
    conf_html = f" &middot; confidence {confidence}" if confidence is not None else ""

    needs_check = verification.get("needs_external_check") or []
    needs_check_html = "".join(f"<li>{html.escape(i)}</li>" for i in needs_check)
    check_box_html = (
        f'<div class="check-box"><p class="check-box-label">Verify externally before relying on this</p>'
        f"<ul>{needs_check_html}</ul></div>"
        if needs_check_html else ""
    )

    ideas_html = "".join(f"<li>{html.escape(i)}</li>" for i in ideas) or '<li class="empty">none</li>'
    discovery_method = outcome.get("discovery_method", "fallback")

    real = plan["method"] == "llm" or reasoning["method"] == "llm" or discovery_method == "llm"

    used = reasoning.get("knowledge_used") or []
    is_generic = used == ["Memory", "Knowledge Graph", "Planning"]
    context_html = ""
    if used:
        context_label = "first time seeing this topic" if is_generic else "from the Knowledge Graph"
        context_html = f'<p class="meta">Context ({context_label}): {html.escape(", ".join(used))}</p>'

    return f"""
    <div class="stage {'on' if plan['method'] == 'llm' else ''}">
      <div class="label">Plan {_tag(plan['method'])}</div>
      <div class="card"><ol>{steps_html}</ol></div>
    </div>
    <div class="stage {'on' if reasoning['method'] == 'llm' else ''}">
      <div class="label">Reasoning {_tag(reasoning['method'])}</div>
      <div class="card"><p>{html.escape(reasoning['conclusion'])}</p>{context_html}</div>
    </div>
    <div class="stage {'on' if verification['method'] == 'llm' else ''}">
      <div class="label">Verification {_tag(verification['method'])}</div>
      <div class="card">
        <p>Verified: {verification['verified']}{conf_html}</p>
        {f'<ul class="meta">{issues_html}</ul>' if issues_html else ''}
        {check_box_html}
      </div>
    </div>
    <div class="stage {'on' if discovery_method == 'llm' else ''}">
      <div class="label">Discovery {_tag(discovery_method)}</div>
      <div class="card"><ul>{ideas_html}</ul></div>
    </div>
    {'<p class="hint">This ran on a real LLM call.</p>' if real else '<p class="hint">This is the fallback path -- no working LLM key yet, so these are templated, not reasoned.</p>'}
    <form class="feedback-form" method="POST" action="/feedback">
      <input type="hidden" name="goal" value="{html.escape(goal)}">
      <span class="meta">Was this useful?</span>
      <button type="submit" name="rating" value="up">&#128077;</button>
      <button type="submit" name="rating" value="down">&#128078;</button>
    </form>
    """


def render_history_entry(entry):
    goal = entry["key"][len("result::"):]
    value = entry["value"]
    verification = value.get("verification") or {}
    plan = value.get("plan")

    real = verification.get("method") == "llm" or (plan and plan.get("method") == "llm")
    tag_html = _tag("llm") if real else _tag("fallback")

    issues = verification.get("issues") or []
    issues_html = "".join(f'<li class="issue">{html.escape(i)}</li>' for i in issues)

    needs_check = verification.get("needs_external_check") or []
    needs_check_html = "".join(f"<li>{html.escape(i)}</li>" for i in needs_check)
    check_box_html = (
        f'<div class="check-box"><p class="check-box-label">Verify externally before relying on this</p>'
        f"<ul>{needs_check_html}</ul></div>"
        if needs_check_html else ""
    )

    ideas = value.get("ideas") or []
    ideas_html = "".join(f"<li>{html.escape(i)}</li>" for i in ideas)

    return f"""
    <div class="entry">
      <p class="entry-goal">{html.escape(goal)} {tag_html}</p>
      <p class="entry-time">{html.escape(entry['updated_at'])}</p>
      <div class="card"><p>{html.escape(value.get('conclusion', ''))}</p></div>
      {f'<ul class="meta">{issues_html}</ul>' if issues_html else ''}
      {check_box_html}
      {f'<div class="card" style="margin-top:8px"><ul>{ideas_html}</ul></div>' if ideas_html else ''}
    </div>
    """


class Handler(BaseHTTPRequestHandler):
    engine = None  # set by main()

    def _send_html(self, body, status=200):
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._send_html(PAGE_TEMPLATE.format(style=STYLE, goal="", result_html=""))
            return

        if parsed.path == "/history":
            query = parse_qs(parsed.query).get("q", [""])[0]
            entries = self.engine.memory.recent(prefix="result::", contains=query or None, limit=30)
            if entries:
                entries_html = "".join(render_history_entry(e) for e in entries)
            else:
                entries_html = '<p class="empty">Nothing found yet.</p>'
            body = HISTORY_TEMPLATE.format(
                style=STYLE, query=html.escape(query), entries_html=entries_html
            )
            self._send_html(body)
            return

        self.send_response(404)
        self.end_headers()

    def _parse_form(self, raw):
        fields = {}
        for pair in raw.split("&"):
            if "=" in pair:
                key, _, value = pair.partition("=")
                fields[key] = unquote_plus(value)
        return fields

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")
        fields = self._parse_form(raw)

        if self.path == "/think":
            goal = fields.get("goal", "")
            if not goal.strip():
                body = PAGE_TEMPLATE.format(
                    style=STYLE, goal="", result_html='<p class="empty">Type a goal first.</p>'
                )
                self._send_html(body)
                return

            outcome = self.engine.think(goal)
            body = PAGE_TEMPLATE.format(
                style=STYLE, goal=html.escape(goal), result_html=render_result(outcome)
            )
            self._send_html(body)
            return

        if self.path == "/feedback":
            goal = fields.get("goal", "")
            rating = fields.get("rating", "")
            if goal and rating in ("up", "down"):
                self.engine.learning.record_feedback(goal, rating)
            body = PAGE_TEMPLATE.format(
                style=STYLE,
                goal="",
                result_html='<p class="feedback-note">Thanks &mdash; feedback recorded. '
                "It'll be used next time a related question comes up.</p>",
            )
            self._send_html(body)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format_str, *args):
        pass  # keep Termux quiet; real errors still raise normally


class NexusServer(HTTPServer):
    # Lets a restart reuse the port immediately instead of sometimes
    # hitting "Address already in use" while the OS finishes cleaning
    # up the previous process's socket.
    allow_reuse_address = True


def main():
    Handler.engine = ThinkingEngine()
    server = NexusServer(("127.0.0.1", PORT), Handler)
    print(f"NEXUS running at http://localhost:{PORT}")
    print("Open that in your phone's browser while this keeps running. Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        Handler.engine.close()


if __name__ == "__main__":
    main()
