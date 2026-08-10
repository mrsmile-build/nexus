#!/data/data/com.termux/files/usr/bin/bash
# Recreates every file NEXUS's persistence/reasoning update touched.
# Self-contained: no unzip, no external paths, no rm -rf of your tree.
# Run from inside ~/nexus:  bash apply_nexus_updates.sh
set -e

echo "Removing the accidentally-nested execution engine folder, if it still exists..."
rm -rf engines/knowledge/src/engines

echo "Creating directories..."
mkdir -p 'core'
mkdir -p 'engines'
mkdir -p 'engines/discovery'
mkdir -p 'engines/discovery/src'
mkdir -p 'engines/execution'
mkdir -p 'engines/execution/src'
mkdir -p 'engines/knowledge'
mkdir -p 'engines/knowledge/src'
mkdir -p 'engines/learning'
mkdir -p 'engines/learning/src'
mkdir -p 'engines/memory'
mkdir -p 'engines/memory/src'
mkdir -p 'engines/planning'
mkdir -p 'engines/planning/src'
mkdir -p 'engines/reasoning'
mkdir -p 'engines/reasoning/src'
mkdir -p 'engines/thinking'
mkdir -p 'engines/thinking/src'
mkdir -p 'engines/tools'
mkdir -p 'engines/verification'
mkdir -p 'engines/verification/src'

echo "Writing .gitignore"
cat > '.gitignore' << 'NEXUS_EOF_MARKER'
# Runtime data -- SQLite-backed Memory/Knowledge state, not source
data/
*.db

# Python
__pycache__/
*.pyc

# Editor backups (e.g. vim/nano crash-recovery files)
*.save
*.swp

# Secrets -- nexus.sh already scans for this; keep the promise
.env
NEXUS_EOF_MARKER

echo "Writing CHANGELOG.md"
cat > 'CHANGELOG.md' << 'NEXUS_EOF_MARKER'
# Changelog

## Unreleased

### Added
- SQLite-backed persistence for the Memory Engine and Knowledge Graph (`data/memory.db`, `data/knowledge.db`) — both now survive a process restart. Public API unchanged.
- `ThinkingEngine` (`engines/thinking/src/thinking.py`) — the coordinator described in `engines/thinking/README.md` now has actual code, wiring Memory, Knowledge, Planning, Reasoning, Discovery, and Verification into one pipeline.
- Persistence tests: `test_memory_persistence.py`, `test_graph_persistence.py` (prove data survives across two separate connections, not just prints within one run).
- `.gitignore` (none existed before — needed now that `data/*.db` shouldn't be committed).

### Changed
- `core/nexus.py` is now a thin entry point delegating to `ThinkingEngine`; the `NEXUS` class and `.run()` method are unchanged so existing usage still works.
- Verifier and DiscoveryEngine are now actually called on every run instead of sitting unused in the codebase.

### Fixed
- Removed a dead `from graph import KnowledgeGraph` import in `query.py` that would have crashed the module the moment it was imported as part of the package rather than run standalone.
- Moved the Execution Engine out of `engines/knowledge/src/engines/execution/` (nested there by accident) to `engines/execution/`, matching every other engine's layout.

### Not yet done
- Learning Engine and Tools Engine are still README-only, no code behind them.
- Planner and Reasoner still return fixed/templated output regardless of the goal — no real reasoning or LLM call yet.
- Verifier only checks for a null/empty result — no real physics/chemistry/math checking yet.
- Top-level README.md, ROADMAP.md, LICENSE are still placeholders.

## Unreleased (2)

### Added
- `core/llm_client.py` — minimal, dependency-free (stdlib only) client for the Anthropic API.
- Planner and Reasoner now call a real LLM for goal-specific plans/reasoning when `ANTHROPIC_API_KEY` is set, and fall back to the old templated behaviour otherwise. Every result now reports `method: "llm"` or `method: "fallback"` so it's visible which one ran.
- `core/test_llm_client.py`, `engines/planning/src/test_planner_parsing.py`, `engines/reasoning/src/test_reasoner_llm.py` — tests using mocked LLM responses, so they need no network access or API key.
- README.md now documents setup, running, and testing instead of being a bare title.

### Known limitation
- This sandbox has no outbound network access, so the real Anthropic API call is untested by me. Fallback behaviour and the response-parsing logic are tested (see above); the live network round-trip is not. Verify it yourself once `ANTHROPIC_API_KEY` is set.

## Unreleased (3)

### Added
- Verifier now calls the LLM for a real plausibility check (internally consistent? contradicts known physics/chemistry/math?) instead of only checking for null/empty. Returns a richer `{verified, confidence, issues, method}` instead of a bare bool -- the null/empty check still runs first either way, unconditionally.
- DiscoveryEngine now calls the LLM for genuinely new angles (patterns, follow-on questions, unnamed risks) instead of templating the plan's own steps back.
- First-ever tests for both engines: `test_verifier.py`, `test_verifier_llm.py`, `test_discovery.py`, `test_discovery_llm.py`.

### Changed (breaking)
- `ThinkingEngine`'s outcome dict now has `outcome["verification"]` (a dict) instead of `outcome["verified"]` (a bool). `core/nexus.py` and `test_thinking.py` are both updated to match.

### Still not wired in
- Learning Engine and Tools Engine: still README-only, no code.
- Execution Engine: works standalone, not yet called from the main Thinking Engine pipeline -- plans are still not actually *executed*, just printed.

## Unreleased (4)

### Added
- `core/llm_client.py` now supports three providers: Groq and OpenAI (both OpenAI-compatible chat-completions shape) alongside the original Anthropic client. Provider is auto-selected by which key is set (Groq first, then OpenAI, then Anthropic), or forced with `NEXUS_LLM_PROVIDER`. Model IDs are overridable per-provider via `NEXUS_GROQ_MODEL` / `NEXUS_OPENAI_MODEL` / `NEXUS_ANTHROPIC_MODEL` since model names go stale fast.
- `core/test_llm_client_providers.py` -- mocked-HTTP tests proving both response shapes parse correctly and provider preference/override logic works.
- Reasoner, Planner, Verifier, and DiscoveryEngine needed zero code changes for this -- they only ever called `ask()`, never touched provider details directly. That boundary held.

### Why
- Anthropic API access costs money per token; Groq and OpenAI were already available at lower/no cost. Real reasoning shouldn't be gated behind a specific paid provider when others work just as well through the same `ask()` interface.

### Still unverified
- No outbound network access in this sandbox, so none of the three providers has been tested against a real network round-trip. The mocked tests prove the code paths are correct; they don't prove Groq's or OpenAI's actual current API still matches the documented shape used here.

## Unreleased (5)

### Fixed
- Corrected a mix-up from my side: "OpenAI" access mentioned earlier was actually OpenRouter. `core/llm_client.py` now has a real `openrouter` provider (was previously conflated with `openai`), using OpenRouter's own `openrouter/free` auto-router as the default model rather than a specific `:free` model ID -- OpenRouter's free lineup rotates out models with little notice, sometimes within days, so pinning a specific one would go stale fast.
- Provider order is now: Groq, OpenRouter, OpenAI, Anthropic.

### Added
- `core/server.py` -- a minimal local web UI (stdlib `http.server`, no pip install) so NEXUS can be used from a phone browser instead of read as terminal text. Run with `python -m core.server`, open `http://localhost:8765`. Same `ThinkingEngine`, same local-only guarantees (nothing hosted, no key ever reaches the browser) as the CLI.
- `core/test_server.py` -- render-logic tests for both the real-LLM and fallback display paths.
- Tested for real this time, not just compiled: ran the actual server and hit it over loopback with curl (GET / and POST /think), confirmed the full pipeline runs and renders correctly end to end.

### Note on hosting
- GitHub Pages can only serve static files -- no Python, no server-side API calls, and it would expose any API key to anyone visiting the page. That's why NEXUS can't be "hosted" there. `core/server.py` is the alternative: it runs locally on your own device, which is the only place your key should ever live anyway.

## Unreleased (6)

### Fixed
- `core/llm_client.py` now sends a custom `User-Agent` header ("NEXUS-Client/1.0") instead of Python urllib's default. A bare HTTP 403 with an unstructured "error code: NNNN" body (not a provider-shaped JSON error) is a Cloudflare block, not a provider auth failure -- it means the request never reached the provider at all. Python's default urllib User-Agent is a common trigger for this.

### Still unverified
- This is a real-world diagnosis (the error shape matches Cloudflare's documented error 1010 exactly), not something confirmed from this sandbox -- still no network access here. Confirmed independently first via a raw `curl` call with a different client signature, to isolate whether it was urllib specifically or something deeper (network-level block, key issue, etc.) before assuming this fix alone would resolve it.

## Unreleased (7)

### Fixed
- `core/llm_client.py` no longer silently accepts empty content from an OpenAI-compatible provider. Reasoning models (e.g. Groq's `openai/gpt-oss-120b`) spend tokens on an internal `reasoning` field before writing the real answer to `content` -- if they run out of budget first, `content` comes back empty with `finish_reason: "length"`. Previously this was treated as a successful `method: "llm"` result with nothing in it; now it raises a specific, diagnosable `LLMError` instead, so it correctly falls back rather than reporting a hollow "success."
- Default `max_tokens` raised from 1024 to 2048 to give reasoning models more headroom before hitting this.

### Confirmed working (real, not mocked)
- Groq connection confirmed live end-to-end via curl: Cloudflare block is gone (custom User-Agent fixed it), and a valid `GROQ_API_KEY` gets a real HTTP 200 with a real completion back. The empty-content edge case above was caught from a real response, not guessed at.

## Unreleased (8)

### Fixed
- `core/server.py` now sets `allow_reuse_address = True`, the standard fix for a server refusing to restart on the same port ("Address already in use") right after a previous instance stops -- especially likely across many quick restarts in one Termux session. Tested for real: started a server, killed it with `-9` (no graceful shutdown), immediately started a new one on the same port, confirmed it binds and serves successfully.

## Unreleased (9)

### Added
- `core/llm_client.py` now retries automatically on HTTP 429 (rate limit), reading the provider's own suggested wait time (from a `Retry-After` header, or parsed from the error message text) instead of failing on the first hit. Caps the automatic wait at 15s -- longer than that, it fails fast rather than blocking the pipeline. Only retries 429s; every other error (auth, bad model, network) still fails immediately as before.

### Why
- NEXUS makes up to 4 LLM calls per single goal (Plan, Reasoning, Verification, Discovery). Groq's free tier caps at 8,000 tokens/minute -- real usage just hit this on the 4th call after the first three had already used 7,731 of that budget. The fallback handled it gracefully, but a 2-3 second automatic retry is strictly better than giving up when the provider is telling you exactly how long to wait.

### Tested
- Mocked: successful retry after a short rate-limit wait, giving up after retries are exhausted, refusing to auto-wait past 15s, and confirming non-429 errors (e.g. 401) are never retried. 12 checks total in this file now.

## Unreleased (10)

### Added
- History page: `/history` in `core/server.py`, with search (`/history?q=cement`). Past questions no longer disappear when you close the tab -- they were already sitting in `data/memory.db`, this just makes them visible and searchable.
- `MemoryEngine.recent(prefix, contains, limit)` -- browse/search without touching store/retrieve/forget/all, which everything else already depends on.
- Fixed a real timestamp bug found while building this: `datetime('now')` in SQLite only has second precision, so multiple stores within the same second couldn't be ordered correctly (caught by the test, which does exactly that). Switched to millisecond precision plus `rowid` as a tie-breaker.
- `ThinkingEngine` now stores the plan alongside conclusion/verification/ideas in each result record, so history entries show the full picture, not a partial one.

### Tested
- Real HTTP requests again, not just the render function in isolation: seeded two results through `/think`, confirmed `/history` lists both most-recent-first, `/history?q=cement` filters to exactly one, and a no-match search shows an empty state instead of an error.

## Unreleased (11)

### Fixed (the important one)
- The Knowledge Graph was empty the entire time, every single answer so far -- while Reasoning's output kept talking about "querying the Knowledge Graph" as though it were populated. Confirmed by re-reading the real history log: the cement, calculus, and soap answers all referenced the graph as a real data source it never actually was. `_gather_context()` only ever did an exact-string match on the full goal, so nothing before this ever hit.

### Added
- Reasoner now asks the LLM to name 2-4 real entity relationships it used, in the form `A -> relation -> B`, parsed out of the prose separately (`test_reasoner_relations.py` covers this, including making sure a stray dash in normal prose is never misparsed as a relation).
- `ThinkingEngine` writes those relations into the real graph after every reasoning call, and context lookup now does keyword search across the goal's significant words instead of requiring an exact repeat of a prior goal string.
- The web UI now shows what context reasoning actually used, labeled either "first time seeing this topic" (the old generic fallback) or "from the Knowledge Graph" (genuine prior content) -- so the effect is visible, not just true in the code.

### Tested for real, not just mocked logic
- `test_thinking_knowledge_loop.py`: confirms the graph starts empty, confirms reasoning's relations are actually written to a real (in-memory) graph, then asks a *second, differently-worded* goal sharing one keyword with the first and confirms it finds the prior context. That's the actual proof the loop closes, not just that the parsing works in isolation.

## Unreleased (12)

### Added
- Verifier now checks two separate things instead of one: internal consistency (as before) and external verifiability -- whether the claim leans on specific real-world facts (named companies/products, current prices, dated specs) that could be outdated or unverified, distinct from general timeless domain knowledge. A claim can be perfectly internally consistent and still need this -- that distinction was the actual gap the Dangote cement result exposed (NEXUS correctly declined to invent a price, but presented "Dangote cement" as one strength figure when it's really a 3-grade product line).
- New `needs_external_check` field on every verification result. Rendered as a visibly distinct amber callout ("Verify externally before relying on this") in both the live result view and history entries -- deliberately different styling from internal-consistency issues, since this isn't a flaw in the reasoning, it's an action item for the person reading it.

### Tested
- Mocked: a consistent-but-unverified claim gets flagged for external check; internal issues and external-check items are tracked independently, not conflated; pure timeless domain knowledge (water boils at 100C) correctly needs no external check; the empty-conclusion and fallback paths both still include the field as an empty list rather than a missing key.
- Render-level: the callout appears when there's something to check and is completely absent (not an empty box) when there isn't, in both the live view and history.

## Unreleased (13)

### Fixed (both found from real use in this session, not hypothesized)
- Verification now receives the plan, not just the reasoning conclusion in isolation. Found because the Dangote cement answer's Plan said "₦13,000 per tonne" while its Reasoning said "13,000 NGN per bag" for the same figure -- a real ~20x unit mismatch that Verification structurally could not catch before, since it never saw the plan at all.
- Context search now filters out generic structural words (formula, method, process, system, result, etc.) before using them as search keys. Found because a calculus question containing "formula" pulled in an unrelated cement answer's "high-clinker Portland formula" node, visibly derailing the reasoning into inventing a nonexistent link between cement chemistry and calculus.
- While testing the fix above: discovered short or multi-word entity names (e.g. "fly ash") never matched via per-word search, since neither "fly" nor "ash" individually clears the length filter. Added whole-node-name matching against the goal text as a first pass, so this class of entity isn't silently invisible to search.

### Tested
- `test_verifier_plan_check.py` and `test_context_filtering.py` both reproduce the exact real scenarios above (same numbers, same wording) rather than inventing simplified stand-ins, so the tests prove these specific bugs are fixed, not just that the code runs.

## Unreleased (14)

### Added -- Learning Engine (the last originally-named engine to get real code, aside from Tools)
- `engines/learning/src/learning.py`: records thumbs up/down (+ optional note) against a goal, and surfaces relevant feedback for related future goals via the same keyword-search approach used for Knowledge Graph context. Lives in the same Memory store, no new persistence layer.
- Wired into `ThinkingEngine`: before reasoning, pulls any related past feedback and passes it to Reasoner, which now includes it in the prompt -- a thumbs-down note actually changes future reasoning instead of sitting in storage unused.
- Web UI: every result now ends with an actual thumbs up/down form (`POST /feedback`), not just a description of the feature. Tested with real HTTP requests: seeded a result, submitted feedback, confirmed it landed in the real database.

### Tests
- `test_learning.py`: recording, exact-match retrieval, keyword-based retrieval for a related-but-differently-worded goal, unrelated goals finding nothing, invalid ratings rejected.
- `test_learning_loop.py`: proves feedback actually reaches the reasoning prompt for a related goal, and confirms an unrelated goal's prompt has no feedback section at all (not just "does it run," but "does it actually change behavior, and only when it should").
- Updated `test_server.py` fixtures to include a `goal` field, since `render_result` now requires one for the feedback form -- the old fixtures correctly failed instead of the check being loosened to fit them.

## Unreleased (15)

### Fixed
- Second instance of the same class of bug, found in real use: "design" pulled an unrelated "New formula design" node (leaked from earlier calculus reasoning) into a cement question's context. Added to the blocklist -- the immediate, guaranteed fix.
- The actual source, not just the symptom: Reasoner's entity-extraction prompt now explicitly discourages vague filler-phrase entity names ("new formula design", "the approach") and asks for specific ones instead (real materials, techniques, standards), with concrete good/bad examples. The blocklist will always be one step behind whatever vague phrase gets generated next; this reduces how often a new one gets created in the first place.

### Tested
- `test_context_filtering.py` now reproduces the exact "design" leak alongside the original "formula" one.
- `test_reasoner_relations.py` confirms the new guidance text is actually in the constructed prompt, not just written in a comment.

## Unreleased (15)

### Fixed
- Same class of bug as before, different word: "design" leaked "New formula design" (from earlier calculus reasoning) into an unrelated cement question's context. Added design/study/plan to the generic-terms blocklist -- the immediate, guaranteed fix.
- The actual source, not just the symptom: Reasoner's RELATIONS extraction prompt now explicitly tells the model to use specific entity names (real materials, techniques, standards -- "Fly ash", "ASTM C150", "Taylor series") and explicitly names vague filler phrases as what NOT to do ("new formula design", "the approach", "this method") -- using the actual phrase just found as the counter-example. Blocklist patches react to specific words after the fact; this addresses new vague entities getting created in the first place. Both are shipped together since the blocklist is guaranteed and the prompt guidance is probabilistic.

## Unreleased (16)

### Fixed (both found from a single real result, not hypothesized)
- Raw `**RELATIONS:**` was showing up in displayed reasoning text. The model wrapped the marker in markdown bold; the exact-string check only recognized the plain form, so the bold version slipped straight through to the user. Marker detection now strips `*` before comparing, and captured entity names get the same treatment in case a relation line itself gets bold-wrapped.
- Discovery could silently fall back to templated output (almost certainly a rate-limit hit, since it runs last after Plan and Reasoning already spent tokens) with zero visible sign it had happened -- the only one of four LLM-backed engines with no method tag at all. `discover()` now returns `{"ideas": [...], "method": ...}` instead of a bare list; the web UI shows Discovery's tag exactly like Plan/Reasoning/Verification already do; `core/nexus.py`'s CLI output does too.

### Tested
- `test_reasoner_relations.py`: reproduces the exact bold-marker response with nothing following it, confirms it's stripped rather than displayed.
- `test_discovery.py` / `test_discovery_llm.py`: updated for the new return shape, explicit assertions that both llm and fallback report their method correctly.
- `test_server.py`: Discovery's tag actually renders in both states, and a result with no `discovery_method` at all (e.g. an old stored entry from before this fix) defaults to showing 'fallback' rather than crashing or falsely claiming 'llm'.
- Confirmed live over real HTTP: ran the actual server, checked the rendered HTML directly for the Discovery tag and for zero remaining RELATIONS text.

## Unreleased (17)

### Fixed
- Verification's plan-consistency check (added two rounds ago) was catching real problems but reporting them uselessly: a real result flagged "plan-mismatch" as the entire issue text, with no explanation. Root cause: my own prompt used the phrase "or plan-mismatch problems" as a category description, and the model echoed the bare word back verbatim instead of describing what actually mismatched -- it genuinely found the plan's example (50% clinker) contradicted the reasoning's stated target (≤30% clinker replacement), it just never said so.
- Fix went through two iterations, both kept: first just negated the word ("not a bare label like X"), but a test written against that immediately failed on the observation that a negated instruction still puts the literal word in front of the model. Removed the string entirely instead, replaced with a concrete worked example (the actual clinker numbers) of what a specific, useful issue description looks like.

### Tested
- `test_verifier_plan_check.py`: confirms the literal problematic string is gone from the prompt, confirms the concrete clinker example is present, and confirms that even a worst-case bare-label response still parses without crashing (a prompt-quality risk, not a parser bug).
NEXUS_EOF_MARKER

echo "Writing README.md"
cat > 'README.md' << 'NEXUS_EOF_MARKER'
# NEXUS

An AI Research Operating System — see `docs/nexus_vision.md` for the full
vision, and each `engines/*/README.md` for what that engine does.

## Setup

Planner, Reasoner, Verifier, and Discovery all call an LLM for real output when a key is available, and fall back to simple deterministic behaviour when it isn't — either way the pipeline runs, but real reasoning needs a key from one of four providers:

```bash
export GROQ_API_KEY="gsk_..."             # console.groq.com
# or
export OPENROUTER_API_KEY="sk-or-..."     # openrouter.ai/keys — free models rotate, so the
                                           # default model routes through openrouter/free
                                           # rather than pinning one that may get delisted
# or
export OPENAI_API_KEY="sk-..."            # platform.openai.com
# or
export ANTHROPIC_API_KEY="sk-ant-api03-..." # console.anthropic.com
```

If more than one is set, this order wins: Groq, then OpenRouter, then OpenAI, then Anthropic. Set `NEXUS_LLM_PROVIDER` (`groq` / `openrouter` / `openai` / `anthropic`) to force a specific one instead. Add whichever `export` line to `~/.bashrc` so it survives closing the terminal — one typed directly into a session only lasts until that session ends.

Model names shift fast on every provider (OpenRouter's free lineup rotates especially often). If you get a "model not found" style error, check that provider's own docs/console for their current model ID and set `NEXUS_GROQ_MODEL` / `NEXUS_OPENROUTER_MODEL` / `NEXUS_OPENAI_MODEL` / `NEXUS_ANTHROPIC_MODEL` rather than editing `core/llm_client.py`.

Never commit a real key to git — `.gitignore` already excludes `.env`.

## Using it in a browser

```bash
python -m core.server
```

Then open `http://localhost:8765` in your phone's browser while that keeps running in Termux. This is the same `ThinkingEngine` as `core/nexus.py` — just a window into it instead of terminal text. Nothing is hosted anywhere; it only exists on your device while the command is running, and no API key ever reaches the browser.

## Running it

```bash
python -m core.nexus
```

Memory and the knowledge graph persist to `data/memory.db` and
`data/knowledge.db` between runs.

## Running tests

Self-contained engines (no dependency outside their own folder) can be
run directly:

```bash
cd engines/knowledge/src && python test_graph.py
```

Engines that reach into `core/` (Reasoner, Planner, the Thinking
Engine) need to run from the repo root instead, so their imports
resolve:

```bash
python -m engines.reasoning.src.test_reasoner
python -m engines.planning.src.test_planner
python -m engines.thinking.src.test_thinking
```
NEXUS_EOF_MARKER

echo "Writing core/__init__.py"
touch 'core/__init__.py'

echo "Writing core/llm_client.py"
cat > 'core/llm_client.py' << 'NEXUS_EOF_MARKER'
"""
NEXUS LLM Client v0.3

Supports three providers, stdlib only (no pip installs, matters on
Termux):

  - Groq      GROQ_API_KEY       openai-compatible; usually the
                                  cheapest option -- check
                                  console.groq.com for current
                                  free-tier terms on your account
  - OpenAI    OPENAI_API_KEY     openai-compatible
  - Anthropic ANTHROPIC_API_KEY  native Claude Messages API

Which one runs: set NEXUS_LLM_PROVIDER to "groq", "openai", or
"anthropic" to force a choice. Otherwise the first of these with a
key actually set wins, checked in this order: groq, openai,
anthropic.

Model names move fast on every provider -- the defaults below were
current as of mid-2026 and WILL go stale eventually. A "model not
found" style error from the provider means: check their docs/console
for the current model ID and set the matching NEXUS_*_MODEL
environment variable (NEXUS_GROQ_MODEL / NEXUS_OPENAI_MODEL /
NEXUS_ANTHROPIC_MODEL) rather than editing this file.

A 403 with a bare "error code: NNNN" (no provider-shaped JSON body)
is Cloudflare, not the provider itself -- it means the request got
blocked before reaching their servers, usually because of Python
urllib's default User-Agent looking obviously automated. That's why
every request below sends a custom one instead of the default.
"""

import json
import os
import re
import time
import urllib.error
import urllib.request

PROVIDERS = {
    "groq": {
        "key_env": "GROQ_API_KEY",
        "model_env": "NEXUS_GROQ_MODEL",
        "default_model": "openai/gpt-oss-120b",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "style": "openai",
    },
    "openrouter": {
        "key_env": "OPENROUTER_API_KEY",
        "model_env": "NEXUS_OPENROUTER_MODEL",
        # OpenRouter's own auto-router: picks from whatever's free right
        # now. Specific ":free" model IDs there rotate out (sometimes
        # within days), so pinning one here would go stale fast --
        # this routes around that instead of guessing today's list.
        "default_model": "openrouter/free",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "style": "openai",
    },
    "openai": {
        "key_env": "OPENAI_API_KEY",
        "model_env": "NEXUS_OPENAI_MODEL",
        "default_model": "gpt-5.4-mini",
        "url": "https://api.openai.com/v1/chat/completions",
        "style": "openai",
    },
    "anthropic": {
        "key_env": "ANTHROPIC_API_KEY",
        "model_env": "NEXUS_ANTHROPIC_MODEL",
        "default_model": "claude-sonnet-5",
        "url": "https://api.anthropic.com/v1/messages",
        "style": "anthropic",
    },
}

PROVIDER_ORDER = ["groq", "openrouter", "openai", "anthropic"]


class LLMError(Exception):
    """Raised for anything that stops a real LLM call from completing:
    no key set, network failure, or a provider-level error. Callers
    (Reasoner, Planner, Verifier, DiscoveryEngine) catch this and fall
    back to non-LLM behaviour instead of crashing the pipeline."""


def _pick_provider():
    forced = os.environ.get("NEXUS_LLM_PROVIDER")
    if forced:
        if forced not in PROVIDERS:
            raise LLMError(
                f"NEXUS_LLM_PROVIDER={forced!r} is not one of {list(PROVIDERS)}"
            )
        return forced

    for name in PROVIDER_ORDER:
        if os.environ.get(PROVIDERS[name]["key_env"]):
            return name

    raise LLMError(
        "No API key set for any provider. Set one of: "
        + ", ".join(PROVIDERS[p]["key_env"] for p in PROVIDER_ORDER)
    )


_RETRY_HINT_RE = re.compile(r"try again in ([\d.]+)\s*s", re.IGNORECASE)
MAX_AUTO_RETRY_WAIT = 15  # seconds -- longer than this, fail instead of blocking the pipeline


def _rate_limit_wait(error, body):
    """How long the provider says to wait, from the Retry-After header
    if present, else parsed from the error message text. None if
    neither is present."""
    header = error.headers.get("Retry-After") if error.headers else None
    if header:
        try:
            return float(header)
        except ValueError:
            pass
    match = _RETRY_HINT_RE.search(body)
    return float(match.group(1)) if match else None


def ask(prompt, system=None, model=None, max_tokens=2048, timeout=30, _max_retries=2):
    provider_name = _pick_provider()
    provider = PROVIDERS[provider_name]
    api_key = os.environ.get(provider["key_env"])
    model = model or os.environ.get(provider["model_env"]) or provider["default_model"]

    if provider["style"] == "openai":
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        body = {"model": model, "max_tokens": max_tokens, "messages": messages}
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {api_key}",
            "user-agent": "NEXUS-Client/1.0",
        }
    else:  # anthropic
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system
        headers = {
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "user-agent": "NEXUS-Client/1.0",
        }

    attempts_left = _max_retries + 1
    while True:
        attempts_left -= 1
        request = urllib.request.Request(
            provider["url"],
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            if error.code == 429 and attempts_left > 0:
                wait = _rate_limit_wait(error, detail)
                if wait is not None and wait <= MAX_AUTO_RETRY_WAIT:
                    time.sleep(wait + 0.5)  # small buffer past what they asked for
                    continue
            raise LLMError(f"{provider_name} API returned {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise LLMError(f"Could not reach the {provider_name} API: {error.reason}") from error
        except TimeoutError as error:
            raise LLMError(f"{provider_name} API call timed out after {timeout}s") from error

    if provider["style"] == "openai":
        try:
            choice = data["choices"][0]
            text = choice["message"]["content"]
        except (KeyError, IndexError) as error:
            raise LLMError(f"Unexpected {provider_name} response shape: {data}") from error

        if not text or not text.strip():
            finish_reason = choice.get("finish_reason")
            if finish_reason == "length":
                raise LLMError(
                    f"{provider_name} model {model!r} used its whole token "
                    f"budget on internal reasoning and never wrote an answer "
                    f"(finish_reason=length, max_tokens={max_tokens}). Try a "
                    f"higher max_tokens or a non-reasoning model."
                )
            raise LLMError(
                f"{provider_name} returned empty content (finish_reason={finish_reason})"
            )
    else:
        text_blocks = [
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        ]
        if not text_blocks:
            raise LLMError(f"No text content in {provider_name} response: {data}")
        text = "".join(text_blocks)

    return text.strip()
NEXUS_EOF_MARKER

echo "Writing core/nexus.py"
cat > 'core/nexus.py' << 'NEXUS_EOF_MARKER'
"""
NEXUS Core v0.2

Thin entry point. The actual coordination logic that used to live
here now lives in the Thinking Engine (engines/thinking/src/thinking.py),
so the code matches what engines/thinking/README.md already documents.
The NEXUS class/run() method are kept so nothing that already calls
them breaks.
"""

from engines.thinking.src.thinking import ThinkingEngine


class NEXUS:
    def __init__(self):
        self.engine = ThinkingEngine()

    def run(self, goal):
        print("=" * 50)
        print("NEXUS AI")
        print("=" * 50)
        print(f"\nGoal: {goal}")

        outcome = self.engine.think(goal)

        print(f"\nPlan (via {outcome['plan']['method']}):")
        for i, step in enumerate(outcome["plan"]["steps"], start=1):
            print(f"{i}. {step}")

        print(f"\nReasoning (via {outcome['reasoning']['method']}):")
        print(outcome["reasoning"]["conclusion"])

        v = outcome["verification"]
        print(f"\nVerification (via {v['method']}):")
        print(f"  Verified: {v['verified']}")
        if v.get("confidence") is not None:
            print(f"  Confidence: {v['confidence']}")
        if v.get("issues"):
            print(f"  Issues: {', '.join(v['issues'])}")

        print(f"\nDiscovery ideas (via {outcome['discovery_method']}):")
        for idea in outcome["ideas"]:
            print(f"- {idea}")

        print("\nMemory:")
        print(self.engine.memory.all())

        self.engine.close()
        return outcome


if __name__ == "__main__":
    nexus = NEXUS()
    nexus.run("Build NEXUS")
NEXUS_EOF_MARKER

echo "Writing core/server.py"
cat > 'core/server.py' << 'NEXUS_EOF_MARKER'
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
NEXUS_EOF_MARKER

echo "Writing core/test_llm_client.py"
cat > 'core/test_llm_client.py' << 'NEXUS_EOF_MARKER'
"""
Tests the "no key set for any provider" error path in
core/llm_client.py -- no real network access needed. Run via:

    python -m core.test_llm_client

A real round-trip against any provider's API can't be verified from
this sandbox -- it has no outbound network access. Once a real key is
set, sanity-check with:

    python3 -c "from core.llm_client import ask; print(ask('Say hi in five words.'))"
"""

import os

from core.llm_client import PROVIDERS, LLMError, ask

# Make this deterministic regardless of whatever the real environment
# has set.
saved = {p["key_env"]: os.environ.pop(p["key_env"], None) for p in PROVIDERS.values()}
saved["NEXUS_LLM_PROVIDER"] = os.environ.pop("NEXUS_LLM_PROVIDER", None)

try:
    ask("test prompt")
    raise AssertionError("Expected LLMError when no provider key is set")
except LLMError as error:
    assert "No API key set" in str(error), error
    print("PASS: ask() raises a clear LLMError when no provider key is set ->", error)
finally:
    for key, value in saved.items():
        if value is not None:
            os.environ[key] = value
NEXUS_EOF_MARKER

echo "Writing core/test_llm_client_providers.py"
cat > 'core/test_llm_client_providers.py' << 'NEXUS_EOF_MARKER'
"""
Tests core/llm_client.py's provider selection and both response
shapes (OpenAI-compatible for Groq/OpenAI, native for Anthropic)
against a mocked HTTP layer -- no real network call, no real key
needed. Run via:

    python -m core.test_llm_client_providers

This proves the request-building and response-parsing logic is
correct for all three providers, and that the free/cheap options
(Groq, then OpenAI) are preferred over Anthropic when multiple keys
are set. It does NOT prove a real network round-trip works -- this
sandbox has no network access, so that part is untested until you run
it yourself with a real key.
"""

import json
import os
from unittest import mock

from core import llm_client


class _FakeHTTPResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _clear_provider_env():
    for provider in llm_client.PROVIDERS.values():
        os.environ.pop(provider["key_env"], None)
    os.environ.pop("NEXUS_LLM_PROVIDER", None)


_clear_provider_env()

# --- Groq: openai-compatible response shape ---
os.environ["GROQ_API_KEY"] = "test-key"
fake = {"choices": [{"message": {"content": "hello from groq"}}]}
with mock.patch("urllib.request.urlopen", return_value=_FakeHTTPResponse(fake)) as mocked:
    result = llm_client.ask("say hi")
assert result == "hello from groq", result
assert "groq.com" in mocked.call_args[0][0].full_url
print("PASS: groq (openai-style) response parsed ->", result)
_clear_provider_env()

# --- OpenAI itself: same response shape, forced explicitly ---
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["NEXUS_LLM_PROVIDER"] = "openai"
fake = {"choices": [{"message": {"content": "hello from openai"}}]}
with mock.patch("urllib.request.urlopen", return_value=_FakeHTTPResponse(fake)) as mocked:
    result = llm_client.ask("say hi")
assert result == "hello from openai", result
assert "openai.com" in mocked.call_args[0][0].full_url
print("PASS: openai response parsed ->", result)
_clear_provider_env()

# --- Anthropic: native response shape ---
os.environ["ANTHROPIC_API_KEY"] = "test-key"
fake = {"content": [{"type": "text", "text": "hello from claude"}]}
with mock.patch("urllib.request.urlopen", return_value=_FakeHTTPResponse(fake)) as mocked:
    result = llm_client.ask("say hi")
assert result == "hello from claude", result
assert "anthropic.com" in mocked.call_args[0][0].full_url
print("PASS: anthropic response parsed ->", result)
_clear_provider_env()

# --- OpenRouter: same response shape, forced explicitly ---
os.environ["OPENROUTER_API_KEY"] = "test-key"
os.environ["NEXUS_LLM_PROVIDER"] = "openrouter"
fake = {"choices": [{"message": {"content": "hello from openrouter"}}]}
with mock.patch("urllib.request.urlopen", return_value=_FakeHTTPResponse(fake)) as mocked:
    result = llm_client.ask("say hi")
assert result == "hello from openrouter", result
assert "openrouter.ai" in mocked.call_args[0][0].full_url
print("PASS: openrouter response parsed ->", result)
_clear_provider_env()

# --- With every key set, groq still wins over openrouter/openai/anthropic ---
os.environ["GROQ_API_KEY"] = "test-key"
os.environ["OPENROUTER_API_KEY"] = "test-key"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
fake = {"choices": [{"message": {"content": "hi"}}]}
with mock.patch("urllib.request.urlopen", return_value=_FakeHTTPResponse(fake)) as mocked:
    llm_client.ask("say hi")
called_url = mocked.call_args[0][0].full_url
assert "groq.com" in called_url, called_url
print("PASS: with every key set, groq is still preferred ->", called_url)
_clear_provider_env()

# --- With no groq key but everything else set, openrouter is next in line ---
os.environ["OPENROUTER_API_KEY"] = "test-key"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
with mock.patch("urllib.request.urlopen", return_value=_FakeHTTPResponse(fake)) as mocked:
    llm_client.ask("say hi")
called_url = mocked.call_args[0][0].full_url
assert "openrouter.ai" in called_url, called_url
print("PASS: without groq, openrouter is preferred next ->", called_url)
_clear_provider_env()

# --- NEXUS_LLM_PROVIDER forces a choice even if a "preferred" key exists ---
os.environ["GROQ_API_KEY"] = "test-key"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["NEXUS_LLM_PROVIDER"] = "anthropic"
fake = {"content": [{"type": "text", "text": "forced to claude"}]}
with mock.patch("urllib.request.urlopen", return_value=_FakeHTTPResponse(fake)) as mocked:
    result = llm_client.ask("say hi")
assert "anthropic.com" in mocked.call_args[0][0].full_url
print("PASS: NEXUS_LLM_PROVIDER=anthropic overrides the default preference")
_clear_provider_env()

# --- Every request sends a non-default User-Agent (avoids the exact
#     Cloudflare-block symptom this was added to fix) ---
os.environ["GROQ_API_KEY"] = "test-key"
fake = {"choices": [{"message": {"content": "hi"}}]}
with mock.patch("urllib.request.urlopen", return_value=_FakeHTTPResponse(fake)) as mocked:
    llm_client.ask("say hi")
sent_headers = mocked.call_args[0][0].headers
assert sent_headers.get("User-agent") == "NEXUS-Client/1.0", sent_headers
print("PASS: requests send a custom User-Agent, not urllib's default")
_clear_provider_env()

print("\nAll provider-selection and response-parsing checks passed.")

# --- Empty content from a reasoning model that ran out of budget mid-thought ---
os.environ["GROQ_API_KEY"] = "test-key"
truncated = {
    "choices": [{"message": {"content": ""}, "finish_reason": "length"}],
}
with mock.patch("urllib.request.urlopen", return_value=_FakeHTTPResponse(truncated)):
    try:
        llm_client.ask("say hi", max_tokens=20, model="openai/gpt-oss-120b")
        raise AssertionError("Expected LLMError for empty content with finish_reason=length")
    except llm_client.LLMError as error:
        assert "whole token budget" in str(error), error
        assert "max_tokens=20" in str(error), error
        print("PASS: truncated reasoning-model response raises a specific, diagnosable error ->", error)
_clear_provider_env()

# --- Empty content for some other reason (not truncation) ---
os.environ["GROQ_API_KEY"] = "test-key"
empty_other = {"choices": [{"message": {"content": ""}, "finish_reason": "stop"}]}
with mock.patch("urllib.request.urlopen", return_value=_FakeHTTPResponse(empty_other)):
    try:
        llm_client.ask("say hi")
        raise AssertionError("Expected LLMError for empty content")
    except llm_client.LLMError as error:
        assert "empty content" in str(error), error
        print("PASS: empty content with a non-length finish_reason is still caught ->", error)
_clear_provider_env()

print("All empty-content checks passed too.")

# --- Rate-limit retry: a 429 with a short retry hint, then success ---
import io
import urllib.error


def _http_error(code, body_dict, headers=None):
    body = json.dumps(body_dict).encode("utf-8")
    return urllib.error.HTTPError(
        url="https://example.test", code=code, msg="error",
        hdrs=headers or {}, fp=io.BytesIO(body),
    )


os.environ["GROQ_API_KEY"] = "test-key"
rate_limited = _http_error(429, {"error": {"message": "Please try again in 0.1s."}})
success = _FakeHTTPResponse({"choices": [{"message": {"content": "worked on retry"}}]})
with mock.patch("urllib.request.urlopen", side_effect=[rate_limited, success]), \
     mock.patch("time.sleep") as mocked_sleep:
    result = llm_client.ask("say hi")
assert result == "worked on retry", result
assert mocked_sleep.call_args[0][0] == 0.6, mocked_sleep.call_args  # 0.1 + 0.5 buffer
print("PASS: a 429 with a short retry hint is retried automatically and succeeds")
_clear_provider_env()

# --- Rate-limit retries exhausted: still 429 after all attempts ---
os.environ["GROQ_API_KEY"] = "test-key"
always_limited = [rate_limited, rate_limited, rate_limited]
with mock.patch("urllib.request.urlopen", side_effect=always_limited), \
     mock.patch("time.sleep"):
    try:
        llm_client.ask("say hi")
        raise AssertionError("Expected LLMError after exhausting retries")
    except llm_client.LLMError as error:
        assert "429" in str(error), error
        print("PASS: gives up cleanly after exhausting retries ->", error)
_clear_provider_env()

# --- Rate limit with a wait too long to block on automatically -- fail fast instead ---
os.environ["GROQ_API_KEY"] = "test-key"
long_wait = _http_error(429, {"error": {"message": "Please try again in 120s."}})
with mock.patch("urllib.request.urlopen", side_effect=[long_wait, success]), \
     mock.patch("time.sleep") as mocked_sleep:
    try:
        llm_client.ask("say hi")
        raise AssertionError("Expected LLMError for a too-long retry wait")
    except llm_client.LLMError as error:
        assert not mocked_sleep.called
        print("PASS: does not block on a rate-limit wait longer than", llm_client.MAX_AUTO_RETRY_WAIT, "s ->", error)
_clear_provider_env()

# --- Non-429 errors are never retried ---
os.environ["GROQ_API_KEY"] = "test-key"
auth_error = _http_error(401, {"error": {"message": "invalid x-api-key"}})
with mock.patch("urllib.request.urlopen", side_effect=[auth_error, success]) as mocked, \
     mock.patch("time.sleep") as mocked_sleep:
    try:
        llm_client.ask("say hi")
        raise AssertionError("Expected LLMError for 401")
    except llm_client.LLMError as error:
        assert mocked.call_count == 1, "401 should not be retried"
        assert not mocked_sleep.called
        print("PASS: a 401 fails immediately, no retry attempted")
_clear_provider_env()

print("\nAll rate-limit retry checks passed.")
NEXUS_EOF_MARKER

echo "Writing core/test_server.py"
cat > 'core/test_server.py' << 'NEXUS_EOF_MARKER'
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
NEXUS_EOF_MARKER

echo "Writing engines/__init__.py"
touch 'engines/__init__.py'

echo "Writing engines/discovery/README.md"
cat > 'engines/discovery/README.md' << 'NEXUS_EOF_MARKER'
# NEXUS Discovery Engine

## Purpose

The Discovery Engine generates new hypotheses, theories, formulas, materials, algorithms and scientific ideas.

## Responsibilities

- Detect gaps in existing knowledge
- Generate hypotheses
- Compare multiple scientific fields
- Suggest cheaper materials
- Suggest stronger materials
- Suggest new chemical combinations
- Design experiments
- Rank discoveries by evidence

## Discovery Process

Observe
↓

Find anomaly
↓

Generate hypothesis
↓

Predict outcome
↓

Design experiment
↓

Verify

↓

Store result

## Future Goals

- Material discovery
- Medicine discovery
- Mathematical discovery
- Engineering discovery
- Physics discovery
- AI architecture discovery
NEXUS_EOF_MARKER

echo "Writing engines/discovery/src/discovery.py"
cat > 'engines/discovery/src/discovery.py' << 'NEXUS_EOF_MARKER'
"""
NEXUS Discovery Engine v0.3

Calls a real LLM to suggest genuinely new angles -- patterns worth
checking, follow-on questions, adjacent ideas, unnamed risks -- when
a provider key is set. Falls back to the v0.1 templated list if the
key is missing, the call fails, or the response can't be parsed.

New in v0.3: returns {"ideas": [...], "method": "llm"/"fallback"}
instead of a bare list. Discovery was the only one of the four LLM-
backed engines with no way to tell whether it actually ran or quietly
fell back -- a real result showed exactly this: Discovery silently
returned the templated fallback (almost certainly a rate-limit hit,
since it runs last after Plan and Reasoning already spent tokens)
with zero visible sign it had happened, while Plan/Reasoning/
Verification all showed their tag correctly.
"""

import re

from core.llm_client import ask, LLMError


class DiscoveryEngine:
    def __init__(self, model=None):
        self.model = model

    def discover(self, observations, goal=None):
        try:
            ideas = self._discover_with_llm(observations, goal)
            if not ideas:
                raise LLMError("LLM response had no parseable numbered ideas")
            return {"ideas": ideas, "method": "llm"}
        except LLMError:
            return {
                "ideas": [f"Possible improvement: {item}" for item in observations],
                "method": "fallback",
            }

    def _discover_with_llm(self, observations, goal):
        context = "; ".join(observations) if observations else "no plan steps yet"

        prompt = (
            (f"Goal: {goal}\n\n" if goal else "")
            + f"Current plan/context: {context}\n\n"
            "Suggest 2-4 genuinely new angles: a pattern worth checking, "
            "a follow-on question, an adjacent idea, or a risk nobody's "
            "named yet. Reply with ONLY a numbered list, one idea per "
            "line, no other text."
        )

        kwargs = {"model": self.model} if self.model else {}
        response = ask(
            prompt,
            system=(
                "You are the Discovery Engine inside NEXUS. Look for "
                "non-obvious connections -- not restatements of what's "
                "already been said."
            ),
            **kwargs,
        )

        ideas = []
        for line in response.splitlines():
            line = line.strip()
            match = re.match(r"^\d+[\.\)]\s*(.+)$", line)
            if match:
                ideas.append(match.group(1).strip())
        return ideas
NEXUS_EOF_MARKER

echo "Writing engines/discovery/src/test_discovery.py"
cat > 'engines/discovery/src/test_discovery.py' << 'NEXUS_EOF_MARKER'
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
NEXUS_EOF_MARKER

echo "Writing engines/discovery/src/test_discovery_llm.py"
cat > 'engines/discovery/src/test_discovery_llm.py' << 'NEXUS_EOF_MARKER'
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
NEXUS_EOF_MARKER

echo "Writing engines/execution/__init__.py"
touch 'engines/execution/__init__.py'

echo "Writing engines/execution/src/__init__.py"
touch 'engines/execution/src/__init__.py'

echo "Writing engines/execution/src/executor.py"
cat > 'engines/execution/src/executor.py' << 'NEXUS_EOF_MARKER'
"""
NEXUS Execution Engine v0.1
"""

class Executor:

    def __init__(self):
        self.history = []

    def execute(self, step):
        result = {
            "step": step,
            "status": "completed"
        }

        self.history.append(result)

        return result

    def execute_plan(self, plan):
        results = []

        for step in plan:
            results.append(self.execute(step))

        return results

    def history_log(self):
        return self.history
NEXUS_EOF_MARKER

echo "Writing engines/execution/src/test_executor.py"
cat > 'engines/execution/src/test_executor.py' << 'NEXUS_EOF_MARKER'
from executor import Executor

executor = Executor()

plan = [
    "Learn Python",
    "Build Memory Engine",
    "Build Knowledge Graph",
    "Run Tests"
]

results = executor.execute_plan(plan)

print("Execution Results:")
for item in results:
    print(item)

print()
print("History:")
print(executor.history_log())
NEXUS_EOF_MARKER

echo "Writing engines/knowledge/README.md"
cat > 'engines/knowledge/README.md' << 'NEXUS_EOF_MARKER'
# NEXUS Knowledge Engine

## Purpose

The Knowledge Engine stores, retrieves, connects, and validates information.

Unlike an LLM, knowledge is separated from reasoning.

Reasoning asks questions.

Knowledge provides evidence.

---

## Responsibilities

- Store facts
- Store concepts
- Store relationships
- Store evidence
- Track confidence
- Track provenance
- Track versions
- Detect conflicts

---

## Inputs

- Research
- User memory
- Documents
- APIs
- Databases
- Internet

---

## Outputs

- Retrieved facts
- Evidence
- Confidence
- Related concepts

---

## Future

- Knowledge Graph
- Vector Search
- Graph Database
- Temporal Knowledge
- Scientific Database
NEXUS_EOF_MARKER

echo "Writing engines/knowledge/__init__.py"
touch 'engines/knowledge/__init__.py'

echo "Writing engines/knowledge/src/__init__.py"
touch 'engines/knowledge/src/__init__.py'

echo "Writing engines/knowledge/src/graph.py"
cat > 'engines/knowledge/src/graph.py' << 'NEXUS_EOF_MARKER'
"""
NEXUS Knowledge Graph Engine v0.3

Backed by SQLite so nodes and edges survive a process restart. All
method names and return shapes match v0.2 exactly, so query.py and
infer.py need no changes beyond their import fix.
"""

import json
import os
import sqlite3


class KnowledgeGraph:
    def __init__(self, db_path="data/knowledge.db"):
        self.db_path = db_path

        if db_path != ":memory:":
            directory = os.path.dirname(db_path)
            if directory:
                os.makedirs(directory, exist_ok=True)

        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nodes (
                name TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                relation TEXT NOT NULL,
                target TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    @property
    def nodes(self):
        rows = self.conn.execute("SELECT name, data FROM nodes").fetchall()
        return {name: json.loads(data) for name, data in rows}

    @property
    def edges(self):
        rows = self.conn.execute(
            "SELECT source, relation, target FROM edges"
        ).fetchall()
        return [{"source": s, "relation": r, "target": t} for s, r, t in rows]

    def add_node(self, name, data=None):
        if not self.exists(name):
            self.conn.execute(
                "INSERT INTO nodes (name, data) VALUES (?, ?)",
                (name, json.dumps(data or {})),
            )
            self.conn.commit()

    def add_edge(self, source, relation, target):
        self.add_node(source)
        self.add_node(target)

        self.conn.execute(
            "INSERT INTO edges (source, relation, target) VALUES (?, ?, ?)",
            (source, relation, target),
        )
        self.conn.commit()

    def neighbors(self, node):
        rows = self.conn.execute(
            "SELECT source, relation, target FROM edges WHERE source = ?",
            (node,),
        ).fetchall()
        return [{"source": s, "relation": r, "target": t} for s, r, t in rows]

    def related(self, node):
        rows = self.conn.execute(
            """
            SELECT target FROM edges WHERE source = ?
            UNION
            SELECT source FROM edges WHERE target = ?
            """,
            (node, node),
        ).fetchall()
        return sorted(row[0] for row in rows)

    def search(self, keyword):
        escaped = keyword.lower().replace("%", r"\%").replace("_", r"\_")
        rows = self.conn.execute(
            "SELECT name FROM nodes WHERE LOWER(name) LIKE ? ESCAPE '\\'",
            (f"%{escaped}%",),
        ).fetchall()
        return sorted(row[0] for row in rows)

    def exists(self, node):
        row = self.conn.execute(
            "SELECT 1 FROM nodes WHERE name = ?", (node,)
        ).fetchone()
        return row is not None

    def relation_exists(self, source, relation, target):
        row = self.conn.execute(
            """
            SELECT 1 FROM edges
            WHERE source = ? AND relation = ? AND target = ?
            """,
            (source, relation, target),
        ).fetchone()
        return row is not None

    def remove_node(self, node):
        self.conn.execute("DELETE FROM nodes WHERE name = ?", (node,))
        self.conn.execute(
            "DELETE FROM edges WHERE source = ? OR target = ?", (node, node)
        )
        self.conn.commit()

    def remove_edge(self, source, relation, target):
        self.conn.execute(
            "DELETE FROM edges WHERE source = ? AND relation = ? AND target = ?",
            (source, relation, target),
        )
        self.conn.commit()

    def show(self):
        return {"nodes": self.nodes, "edges": self.edges}

    def close(self):
        self.conn.close()
NEXUS_EOF_MARKER

echo "Writing engines/knowledge/src/infer.py"
cat > 'engines/knowledge/src/infer.py' << 'NEXUS_EOF_MARKER'
class InferenceEngine:

    def __init__(self, graph):
        self.graph = graph

    def infer(self, start):
        results = []

        for edge in self.graph.edges:
            if edge["source"] == start:
                target = edge["target"]

                for edge2 in self.graph.edges:
                    if edge2["source"] == target:
                        results.append({
                            "from": start,
                            "through": target,
                            "to": edge2["target"]
                        })

        return results
NEXUS_EOF_MARKER

echo "Writing engines/knowledge/src/query.py"
cat > 'engines/knowledge/src/query.py' << 'NEXUS_EOF_MARKER'
class QueryEngine:
    def __init__(self, graph):
        self.graph = graph

    def answer(self, question):
        q = question.lower()

        if "what uses mathematics" in q:
            results = []

            for edge in self.graph.edges:
                if (
                    edge["relation"] == "uses"
                    and edge["target"] == "Mathematics"
                ):
                    results.append(edge["source"])

            return results

        if "what supports physics" in q:
            results = []

            for edge in self.graph.edges:
                if (
                    edge["relation"] == "supports"
                    and edge["target"] == "Physics"
                ):
                    results.append(edge["source"])

            return results

        return "I don't know yet."
NEXUS_EOF_MARKER

echo "Writing engines/knowledge/src/test_graph.py"
cat > 'engines/knowledge/src/test_graph.py' << 'NEXUS_EOF_MARKER'
from graph import KnowledgeGraph

kg = KnowledgeGraph(db_path=":memory:")

kg.add_node("Earth")
kg.add_node("Sun")

kg.add_edge("Earth", "orbits", "Sun")

print(kg.show())
NEXUS_EOF_MARKER

echo "Writing engines/knowledge/src/test_graph_persistence.py"
cat > 'engines/knowledge/src/test_graph_persistence.py' << 'NEXUS_EOF_MARKER'
"""
Proves KnowledgeGraph data survives a restart -- not just a single
process's lifetime. test_graph.py uses ":memory:" for a quick demo;
this test uses a real file and two separate connections to it.
"""

import os

from graph import KnowledgeGraph

TEST_DB = "test_graph_persistence.db"

if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

# "Process" 1: add an edge, then close the connection.
first = KnowledgeGraph(db_path=TEST_DB)
first.add_edge("Earth", "orbits", "Sun")
first.close()

# "Process" 2: open the same file fresh, with no memory of the first
# instance. If this still finds the edge, persistence is real.
second = KnowledgeGraph(db_path=TEST_DB)
assert second.relation_exists("Earth", "orbits", "Sun"), "Edge did not survive a restart"
print("PASS: graph persisted across a restart ->", second.show())
second.close()

os.remove(TEST_DB)
NEXUS_EOF_MARKER

echo "Writing engines/knowledge/src/test_infer.py"
cat > 'engines/knowledge/src/test_infer.py' << 'NEXUS_EOF_MARKER'
from graph import KnowledgeGraph
from infer import InferenceEngine

kg = KnowledgeGraph(db_path=":memory:")

kg.add_node("Artificial Intelligence")
kg.add_node("Mathematics")
kg.add_node("Physics")
kg.add_node("Gravity")

kg.add_edge("Artificial Intelligence", "uses", "Mathematics")
kg.add_edge("Mathematics", "supports", "Physics")
kg.add_edge("Physics", "explains", "Gravity")

engine = InferenceEngine(kg)

print(engine.infer("Artificial Intelligence"))
NEXUS_EOF_MARKER

echo "Writing engines/knowledge/src/test_query.py"
cat > 'engines/knowledge/src/test_query.py' << 'NEXUS_EOF_MARKER'
from graph import KnowledgeGraph
from query import QueryEngine

kg = KnowledgeGraph(db_path=":memory:")

kg.add_node("Artificial Intelligence")
kg.add_node("Mathematics")
kg.add_node("Physics")

kg.add_edge(
    "Artificial Intelligence",
    "uses",
    "Mathematics"
)

kg.add_edge(
    "Mathematics",
    "supports",
    "Physics"
)

engine = QueryEngine(kg)

print(engine.answer("What uses Mathematics?"))
print(engine.answer("What supports Physics?"))
NEXUS_EOF_MARKER

echo "Writing engines/knowledge/src/test_search.py"
cat > 'engines/knowledge/src/test_search.py' << 'NEXUS_EOF_MARKER'
from graph import KnowledgeGraph

kg = KnowledgeGraph(db_path=":memory:")

kg.add_node("Artificial Intelligence")
kg.add_node("Machine Learning")
kg.add_node("Deep Learning")
kg.add_node("Mathematics")
kg.add_node("Physics")

print("Search: Learning")
print(kg.search("Learning"))

print()

print("Search: Math")
print(kg.search("Math"))
NEXUS_EOF_MARKER

echo "Writing engines/learning/README.md"
cat > 'engines/learning/README.md' << 'NEXUS_EOF_MARKER'
# NEXUS Learning Engine

## Purpose
Improve NEXUS over time from verified knowledge and experience.

## Responsibilities

- Learn from successful tasks.
- Store verified discoveries.
- Remove outdated information.
- Improve strategies.
- Track research progress.

## Inputs

- Verification results
- Research findings
- User feedback

## Outputs

- Updated knowledge
- Better reasoning strategies
- Improved workflows

## Future

- Continuous learning
- Knowledge graph evolution
- Automatic pattern discovery
- Research assistant
NEXUS_EOF_MARKER

echo "Writing engines/learning/__init__.py"
touch 'engines/learning/__init__.py'

echo "Writing engines/learning/src/__init__.py"
touch 'engines/learning/src/__init__.py'

echo "Writing engines/learning/src/learning.py"
cat > 'engines/learning/src/learning.py' << 'NEXUS_EOF_MARKER'
"""
NEXUS Learning Engine v0.1

The README lists "User feedback" as an input and "Better reasoning
strategies" as an output -- this is the first actual implementation
of that, and the last of the originally-named engines to get real
code (Tools Engine is still README-only after this).

Stores a thumbs up/down (+ optional note) against a goal, and can
surface relevant past feedback for a related future goal, using the
same keyword-search approach as the Knowledge Graph's context
lookup. Feedback lives in the same Memory store as everything else
-- no new persistence layer needed.
"""

_GENERIC_TERMS = {
    "formula", "formulas", "method", "methods", "approach", "approaches",
    "process", "processes", "system", "systems", "result", "results",
    "structure", "structures", "model", "models", "technique", "techniques",
    "strategy", "strategies", "solution", "solutions", "tool", "tools",
    "framework", "concept", "concepts", "idea", "ideas", "factor", "factors",
    "aspect", "aspects", "element", "elements", "component", "components",
    "type", "types", "kind", "kinds", "form", "forms", "way", "ways",
}


class LearningEngine:
    def __init__(self, memory):
        self.memory = memory

    def record_feedback(self, goal, rating, note=None):
        """rating: 'up' or 'down'."""
        if rating not in ("up", "down"):
            raise ValueError(f"rating must be 'up' or 'down', got {rating!r}")
        self.memory.store(f"feedback::{goal}", {"rating": rating, "note": note})

    def relevant_feedback(self, goal, limit=5):
        """Past feedback for goals related to this one -- same
        keyword-search idea as ThinkingEngine._gather_context, kept
        separate since it searches Memory's feedback entries, not the
        Knowledge Graph."""
        found = []
        seen_goals = set()

        # Exact match first.
        exact = self.memory.retrieve(f"feedback::{goal}")
        if exact:
            seen_goals.add(goal.lower())
            found.append({"goal": goal, **exact})

        for word in goal.split():
            word = word.strip(".,!?:;\"'()").lower()
            if len(word) <= 3 or word in _GENERIC_TERMS:
                continue
            for entry in self.memory.recent(prefix="feedback::", contains=word, limit=limit):
                past_goal = entry["key"][len("feedback::"):]
                if past_goal.lower() not in seen_goals:
                    seen_goals.add(past_goal.lower())
                    found.append({"goal": past_goal, **entry["value"]})

        return found[:limit]
NEXUS_EOF_MARKER

echo "Writing engines/learning/src/test_learning.py"
cat > 'engines/learning/src/test_learning.py' << 'NEXUS_EOF_MARKER'
"""
Tests LearningEngine: recording feedback, exact-match retrieval, and
keyword-based retrieval for a related-but-differently-worded goal.
Run via:

    python -m engines.learning.src.test_learning
"""

from engines.memory.src.memory import MemoryEngine
from engines.learning.src.learning import LearningEngine

memory = MemoryEngine(db_path=":memory:")
learning = LearningEngine(memory)

# Nothing recorded yet -> nothing found.
assert learning.relevant_feedback("Design a cheaper cement") == []
print("PASS: no feedback yet returns an empty list")

# Record feedback, then find it by exact match.
learning.record_feedback(
    "Design a cheaper cement", "down", note="Didn't account for local SCM availability"
)
exact = learning.relevant_feedback("Design a cheaper cement")
assert len(exact) == 1 and exact[0]["rating"] == "down", exact
print("PASS: exact-match retrieval works ->", exact[0]["note"])

# A differently-worded but related goal should still find it via keyword search.
related = learning.relevant_feedback("Cement that is 40% cheaper and stronger")
assert len(related) == 1 and related[0]["goal"] == "Design a cheaper cement", related
print("PASS: a related, differently-worded goal finds the same feedback ->", related[0]["goal"])

# An unrelated goal should find nothing.
unrelated = learning.relevant_feedback("Best way to learn a new language")
assert unrelated == [], unrelated
print("PASS: an unrelated goal finds nothing")

# Bad rating value is rejected rather than silently stored.
try:
    learning.record_feedback("Some goal", "sideways")
    raise AssertionError("Expected ValueError for an invalid rating")
except ValueError as error:
    print("PASS: an invalid rating is rejected ->", error)

memory.close()
print("\nAll learning-engine checks passed.")
NEXUS_EOF_MARKER

echo "Writing engines/memory/README.md"
cat > 'engines/memory/README.md' << 'NEXUS_EOF_MARKER'
# NEXUS Memory Engine

## Purpose

The Memory Engine stores and retrieves information required for intelligent reasoning while preserving accuracy, privacy, and historical context.

Memory is separate from knowledge.

Knowledge represents facts about the world.

Memory represents experiences, users, tasks, and previous reasoning.

---

## Memory Types

### Working Memory
- Current task
- Intermediate reasoning
- Temporary variables

### Episodic Memory
- Previous conversations
- Research sessions
- Experiments
- Decisions

### Semantic Memory
- Learned concepts
- Definitions
- Relationships

### Procedural Memory
- Algorithms
- Workflows
- Tool usage
- Problem-solving methods

---

## Responsibilities

- Store memory
- Retrieve relevant memory
- Rank importance
- Forget obsolete memory
- Detect contradictions
- Version updates

---

## Retrieval Process

Input
↓

Search Memory

↓

Rank by relevance

↓

Verify validity

↓

Return to Reasoning Engine

---

## Future Features

- Temporal memory
- Memory compression
- Long-term memory
- User memory
- Scientific memory
- Distributed memory
NEXUS_EOF_MARKER

echo "Writing engines/memory/__init__.py"
touch 'engines/memory/__init__.py'

echo "Writing engines/memory/src/__init__.py"
touch 'engines/memory/src/__init__.py'

echo "Writing engines/memory/src/memory.py"
cat > 'engines/memory/src/memory.py' << 'NEXUS_EOF_MARKER'
"""
NEXUS Memory Engine v0.3

Backed by SQLite so stored memories survive a process restart.
store/retrieve/forget/all are unchanged from v0.2. New in v0.3:
recent() for browsing/searching history without touching those.
"""

import json
import os
import sqlite3


class MemoryEngine:
    def __init__(self, db_path="data/memory.db"):
        self.db_path = db_path

        if db_path != ":memory:":
            directory = os.path.dirname(db_path)
            if directory:
                os.makedirs(directory, exist_ok=True)

        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def store(self, key, value):
        self.conn.execute(
            """
            INSERT INTO memory (key, value, updated_at)
            VALUES (?, ?, strftime('%Y-%m-%d %H:%M:%f', 'now'))
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, json.dumps(value)),
        )
        self.conn.commit()

    def retrieve(self, key):
        row = self.conn.execute(
            "SELECT value FROM memory WHERE key = ?", (key,)
        ).fetchone()

        return json.loads(row[0]) if row else None

    def forget(self, key):
        self.conn.execute("DELETE FROM memory WHERE key = ?", (key,))
        self.conn.commit()

    def all(self):
        rows = self.conn.execute("SELECT key, value FROM memory").fetchall()
        return {key: json.loads(value) for key, value in rows}

    def recent(self, prefix=None, contains=None, limit=50):
        """Recent entries as [{key, value, updated_at}, ...], most
        recent first. Optionally filtered to keys starting with
        `prefix`, and/or to entries where `contains` appears in the
        key or the value (case-insensitive)."""
        query = "SELECT key, value, updated_at FROM memory WHERE 1=1"
        params = []
        if prefix:
            query += " AND key LIKE ?"
            params.append(f"{prefix}%")
        if contains:
            query += " AND (LOWER(key) LIKE ? OR LOWER(value) LIKE ?)"
            term = f"%{contains.lower()}%"
            params.extend([term, term])
        query += " ORDER BY updated_at DESC, rowid DESC LIMIT ?"
        params.append(limit)

        rows = self.conn.execute(query, params).fetchall()
        return [
            {"key": key, "value": json.loads(value), "updated_at": updated_at}
            for key, value, updated_at in rows
        ]

    def close(self):
        self.conn.close()
NEXUS_EOF_MARKER

echo "Writing engines/memory/src/test_memory.py"
cat > 'engines/memory/src/test_memory.py' << 'NEXUS_EOF_MARKER'
from memory import MemoryEngine

mem = MemoryEngine(db_path=":memory:")

mem.store("planet", "Earth")
mem.store("star", "Sun")

print(mem.retrieve("planet"))
print(mem.retrieve("star"))

mem.forget("planet")

print(mem.all())
NEXUS_EOF_MARKER

echo "Writing engines/memory/src/test_memory_persistence.py"
cat > 'engines/memory/src/test_memory_persistence.py' << 'NEXUS_EOF_MARKER'
"""
Proves MemoryEngine data survives a restart -- not just a single
process's lifetime. test_memory.py uses ":memory:" for a quick demo;
this test uses a real file and two separate connections to it.
"""

import os

from memory import MemoryEngine

TEST_DB = "test_memory_persistence.db"

if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

# "Process" 1: store something, then close the connection.
first = MemoryEngine(db_path=TEST_DB)
first.store("planet", "Earth")
first.close()

# "Process" 2: open the same file fresh, with no memory of the first
# instance. If this still finds the value, persistence is real.
second = MemoryEngine(db_path=TEST_DB)
value = second.retrieve("planet")
assert value == "Earth", f"Value did not survive a restart, got {value!r}"
print("PASS: memory persisted across a restart ->", value)
second.close()

os.remove(TEST_DB)
NEXUS_EOF_MARKER

echo "Writing engines/memory/src/test_memory_recent.py"
cat > 'engines/memory/src/test_memory_recent.py' << 'NEXUS_EOF_MARKER'
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
NEXUS_EOF_MARKER

echo "Writing engines/planning/README.md"
cat > 'engines/planning/README.md' << 'NEXUS_EOF_MARKER'
# NEXUS Planning Engine

## Purpose
Convert a user's goal into an executable plan.

## Responsibilities

- Understand the user's objective.
- Break large goals into smaller tasks.
- Decide which engine or tool is needed.
- Estimate task complexity.
- Re-plan when new information appears.

## Inputs

- User request
- Memory
- Knowledge
- Available tools

## Outputs

- Ordered task list
- Execution strategy
- Required tools
- Success criteria

## Future

- Goal decomposition
- Multi-agent planning
- Long-term planning
- Autonomous scheduling
NEXUS_EOF_MARKER

echo "Writing engines/planning/__init__.py"
touch 'engines/planning/__init__.py'

echo "Writing engines/planning/src/__init__.py"
touch 'engines/planning/src/__init__.py'

echo "Writing engines/planning/src/planner.py"
cat > 'engines/planning/src/planner.py' << 'NEXUS_EOF_MARKER'
"""
NEXUS Planning Engine v0.2

Calls a real LLM to produce a goal-specific plan when
ANTHROPIC_API_KEY is set. Falls back to the v0.1 static 5-step plan
if the key is missing, the call fails, or the response can't be
parsed into steps.
"""

import re

from core.llm_client import ask, LLMError

FALLBACK_STEPS = [
    "Understand the goal",
    "Gather knowledge",
    "Create strategy",
    "Execute tasks",
    "Verify results",
]


class Planner:
    def __init__(self, model=None):
        self.model = model

    def create_plan(self, goal):
        try:
            steps = self._plan_with_llm(goal)
            if not steps:
                raise LLMError("LLM response had no parseable numbered steps")
            method = "llm"
        except LLMError:
            steps = list(FALLBACK_STEPS)
            method = "fallback"

        return {"goal": goal, "steps": steps, "method": method}

    def _plan_with_llm(self, goal):
        prompt = (
            f"Goal: {goal}\n\n"
            "Break this into 4-6 concrete, ordered steps to work toward "
            "it. Reply with ONLY a numbered list, one step per line, no "
            "other text."
        )

        kwargs = {"model": self.model} if self.model else {}

        response = ask(
            prompt,
            system=(
                "You are the Planning Engine inside NEXUS, a research "
                "assistant system. Produce short, concrete, ordered "
                "steps -- no commentary."
            ),
            **kwargs,
        )

        steps = []
        for line in response.splitlines():
            line = line.strip()
            match = re.match(r"^\d+[\.\)]\s*(.+)$", line)
            if match:
                steps.append(match.group(1).strip())

        return steps
NEXUS_EOF_MARKER

echo "Writing engines/planning/src/test_planner.py"
cat > 'engines/planning/src/test_planner.py' << 'NEXUS_EOF_MARKER'
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
NEXUS_EOF_MARKER

echo "Writing engines/planning/src/test_planner_parsing.py"
cat > 'engines/planning/src/test_planner_parsing.py' << 'NEXUS_EOF_MARKER'
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
NEXUS_EOF_MARKER

echo "Writing engines/reasoning/README.md"
cat > 'engines/reasoning/README.md' << 'NEXUS_EOF_MARKER'
# NEXUS Reasoning Engine

## Purpose

The Reasoning Engine transforms knowledge into decisions.

It should:
- Break problems into sub-problems
- Generate hypotheses
- Evaluate evidence
- Detect contradictions
- Estimate uncertainty
- Produce conclusions

## Pipeline

Input
↓

Understand Goal
↓

Retrieve Knowledge
↓

Retrieve Memory
↓

Generate Hypotheses
↓

Evaluate Evidence
↓

Verify
↓

Output

## Future

- Tree Search
- Symbolic Reasoning
- Probabilistic Reasoning
- Causal Reasoning
NEXUS_EOF_MARKER

echo "Writing engines/reasoning/__init__.py"
touch 'engines/reasoning/__init__.py'

echo "Writing engines/reasoning/src/__init__.py"
touch 'engines/reasoning/src/__init__.py'

echo "Writing engines/reasoning/src/reasoner.py"
cat > 'engines/reasoning/src/reasoner.py' << 'NEXUS_EOF_MARKER'
"""
NEXUS Reasoning Engine v0.4

Calls a real LLM to reason about the goal when a provider key is set.
Falls back to the v0.1 templated conclusion if no key is set, the
network call fails, or the API errors.

Extracts entity relationships from its own output (v0.3) so
ThinkingEngine can write them into the Knowledge Graph, and now (v0.4)
accepts optional feedback from LearningEngine on related past goals,
so a thumbs-down note actually changes this reasoning instead of
sitting unused in storage.
"""

import re

from core.llm_client import ask, LLMError

_RELATION_LINE = re.compile(r"^\s*(.+?)\s*->\s*(.+?)\s*->\s*(.+?)\s*$")
_MAX_ENTITY_LEN = 60  # sanity limit -- a real entity name, not a stray sentence


class Reasoner:
    def __init__(self, model=None):
        self.model = model

    def reason(self, goal, knowledge, feedback=None):
        try:
            conclusion, relations = self._reason_with_llm(goal, knowledge, feedback)
            method = "llm"
        except LLMError as error:
            conclusion = (
                f"Using available knowledge, the next action is to work "
                f"toward '{goal}'. (LLM reasoning unavailable: {error})"
            )
            relations = []
            method = "fallback"

        return {
            "goal": goal,
            "knowledge_used": knowledge,
            "conclusion": conclusion,
            "relations": relations,
            "method": method,
        }

    def _reason_with_llm(self, goal, knowledge, feedback):
        known = ", ".join(knowledge) if knowledge else "nothing yet"

        feedback_block = ""
        if feedback:
            notes = "; ".join(
                f"on '{f['goal']}' someone said {f['rating']}"
                + (f" ({f['note']})" if f.get("note") else "")
                for f in feedback
            )
            feedback_block = (
                f"Feedback on related past answers -- take this into "
                f"account, especially anything marked down: {notes}\n\n"
            )

        prompt = (
            f"Goal: {goal}\n\n"
            f"Related knowledge NEXUS already has: {known}.\n\n"
            f"{feedback_block}"
            "Reason step by step about how to approach this goal. State "
            "what's already known, what's uncertain, and one concrete next "
            "action. Under 150 words.\n\n"
            "Then, on their own lines, list 2-4 short entity relationships "
            "your reasoning actually relied on, exactly in this format:\n"
            "RELATIONS:\n"
            "Entity A -> relation -> Entity B\n"
            "Use short, SPECIFIC entity/concept names -- real materials, "
            "techniques, standards, or named things (e.g. 'Fly ash', "
            "'ASTM C150', 'Taylor series') -- not full sentences, and not "
            "vague filler phrases that could apply to any topic (e.g. "
            "'new formula design', 'the approach', 'this method'). Only "
            "entities you genuinely used above."
        )

        kwargs = {"model": self.model} if self.model else {}

        response = ask(
            prompt,
            system=(
                "You are the Reasoning Engine inside NEXUS, a research "
                "assistant system. Be precise, flag uncertainty honestly, "
                "and never state a guess as a fact."
            ),
            **kwargs,
        )

        return self._split(response)

    def _split(self, response):
        """Separates the prose conclusion from RELATIONS lines, so the
        displayed reasoning doesn't show raw 'A -> rel -> B' lines."""
        conclusion_lines = []
        relations = []

        for line in response.splitlines():
            match = _RELATION_LINE.match(line)
            if match:
                a, rel, b = (part.strip().strip("*").strip() for part in match.groups())
                if a and rel and b and max(len(a), len(rel), len(b)) <= _MAX_ENTITY_LEN:
                    relations.append((a, rel, b))
                continue
            # Tolerate markdown emphasis around the marker (**RELATIONS:**,
            # *RELATIONS:*) -- a real response used the bold form and it
            # slipped through an exact-string check straight into the
            # displayed conclusion.
            marker = line.strip().strip("*").strip().upper()
            if marker == "RELATIONS:":
                continue
            conclusion_lines.append(line)

        conclusion = "\n".join(conclusion_lines).strip()
        return conclusion, relations
NEXUS_EOF_MARKER

echo "Writing engines/reasoning/src/test_reasoner.py"
cat > 'engines/reasoning/src/test_reasoner.py' << 'NEXUS_EOF_MARKER'
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
NEXUS_EOF_MARKER

echo "Writing engines/reasoning/src/test_reasoner_llm.py"
cat > 'engines/reasoning/src/test_reasoner_llm.py' << 'NEXUS_EOF_MARKER'
"""
Tests Reasoner against a fake LLM response -- no real network call,
no API key needed. Run via:

    python -m engines.reasoning.src.test_reasoner_llm

This proves the wiring works. It does not prove the real Anthropic
API call works -- this sandbox has no network access, so that part is
untested until you run it yourself with a real key.
"""

from unittest import mock

from engines.reasoning.src.reasoner import Reasoner

FAKE_RESPONSE = (
    "Known: concrete strength mainly comes from the cement-to-water ratio "
    "and aggregate quality. Uncertain: which cheaper substitute binder "
    "keeps compressive strength within spec. Next action: pull three "
    "candidate substitute binders from the knowledge graph and compare "
    "their published compressive strength data."
)

with mock.patch("engines.reasoning.src.reasoner.ask", return_value=FAKE_RESPONSE):
    reasoner = Reasoner()
    result = reasoner.reason(
        "Design a cheaper cement", ["Concrete", "Materials Science"]
    )

assert result["method"] == "llm", result
assert result["conclusion"] == FAKE_RESPONSE, result

print("PASS: Reasoner used the (mocked) LLM response ->")
print(result["conclusion"])
NEXUS_EOF_MARKER

echo "Writing engines/reasoning/src/test_reasoner_relations.py"
cat > 'engines/reasoning/src/test_reasoner_relations.py' << 'NEXUS_EOF_MARKER'
"""
Tests Reasoner's RELATIONS parsing -- separating prose from extracted
entity relationships -- against a mocked LLM response. No real
network call, no API key needed. Run via:

    python -m engines.reasoning.src.test_reasoner_relations
"""

from unittest import mock

from engines.reasoning.src.reasoner import Reasoner

FAKE_RESPONSE = """Known: fly ash is a common Portland cement substitute with pozzolanic properties. Uncertain: regional pricing.
Concrete next action: compare fly ash against slag for this region.

RELATIONS:
Fly ash -> substitutes for -> Portland cement
Fly ash -> reduces -> production cost
This is not a relation line, just prose that happens to have a dash - in it.
"""

with mock.patch("engines.reasoning.src.reasoner.ask", return_value=FAKE_RESPONSE):
    reasoner = Reasoner()
    result = reasoner.reason("Design a cheaper cement", ["Concrete"])

assert result["method"] == "llm", result
assert "RELATIONS:" not in result["conclusion"], result["conclusion"]
assert "Fly ash -> substitutes" not in result["conclusion"], result["conclusion"]
assert "Known: fly ash is a common Portland cement substitute" in result["conclusion"]
print("PASS: RELATIONS lines are stripped out of the displayed conclusion")

assert result["relations"] == [
    ("Fly ash", "substitutes for", "Portland cement"),
    ("Fly ash", "reduces", "production cost"),
], result["relations"]
print("PASS: relation lines are parsed into (source, relation, target) tuples ->", result["relations"])

# A single stray dash in normal prose should never be mistaken for a relation.
assert not any("dash" in r[0].lower() for r in result["relations"])
print("PASS: prose containing a plain dash is not misparsed as a relation")

# Fallback mode should return an empty relations list, not crash.
with mock.patch(
    "engines.reasoning.src.reasoner.ask",
    side_effect=__import__("core.llm_client", fromlist=["LLMError"]).LLMError("no key"),
):
    fallback_result = Reasoner().reason("Build NEXUS", [])
assert fallback_result["relations"] == [], fallback_result
print("PASS: fallback mode returns an empty relations list")

print("\nAll reasoner-relation checks passed.")

# Reproduces the exact real failure: model wrapped the marker in
# markdown bold and provided no actual relations after it, so the
# raw "**RELATIONS:**" showed up in the displayed conclusion.
BOLD_MARKER_RESPONSE = (
    "Known: SCMs can replace clinker. Uncertain: exact blend ratios.\n"
    "Next action: gather local prices.\n\n"
    "**RELATIONS:**"
)
with mock.patch("engines.reasoning.src.reasoner.ask", return_value=BOLD_MARKER_RESPONSE):
    result = Reasoner().reason("Design a cheaper cement", ["Cement"])
assert "RELATIONS" not in result["conclusion"], result["conclusion"]
assert result["relations"] == [], result["relations"]
print("PASS: a bold-wrapped RELATIONS marker with nothing after it is stripped, not displayed")

# The prompt itself should discourage vague filler-phrase entity names,
# not just rely on filtering them out later at search time.
captured = {}
with mock.patch("engines.reasoning.src.reasoner.ask", side_effect=lambda p, **k: (captured.update(text=p), FAKE_RESPONSE)[1]):
    Reasoner().reason("Design a cheaper cement", [])
assert "vague filler phrases" in captured["text"], captured["text"]
assert "new formula design" in captured["text"].lower(), captured["text"]
print("PASS: the prompt explicitly discourages vague entity names, with a concrete bad example")
NEXUS_EOF_MARKER

echo "Writing engines/thinking/README.md"
cat > 'engines/thinking/README.md' << 'NEXUS_EOF_MARKER'
# NEXUS Thinking Engine

## Purpose

The Thinking Engine coordinates all NEXUS engines to solve problems intelligently.

## Thinking Pipeline

1. Receive question
2. Understand intent
3. Retrieve relevant knowledge
4. Search memory
5. Build a reasoning plan
6. Call tools if needed
7. Generate hypotheses
8. Verify conclusions
9. Learn from the result
10. Store useful knowledge
11. Produce the final answer

## Connected Engines

- Knowledge Engine
- Memory Engine
- Reasoning Engine
- Planning Engine
- Discovery Engine
- Verification Engine
- Learning Engine
- Tools Engine

## Goals

- Reduce hallucinations
- Increase logical consistency
- Support scientific discovery
- Improve decision making
- Coordinate all cognitive modules
NEXUS_EOF_MARKER

echo "Writing engines/thinking/__init__.py"
touch 'engines/thinking/__init__.py'

echo "Writing engines/thinking/src/__init__.py"
touch 'engines/thinking/src/__init__.py'

echo "Writing engines/thinking/src/test_context_filtering.py"
cat > 'engines/thinking/src/test_context_filtering.py' << 'NEXUS_EOF_MARKER'
"""
Reproduces the exact bug found in real use: a calculus question
containing the word "formula" pulled in unrelated cement context
because "formula" was a substring of "high-clinker Portland formula".
Proves the fix without breaking genuine topical matches. Run via:

    python -m engines.thinking.src.test_context_filtering
"""

from engines.thinking.src.thinking import ThinkingEngine

engine = ThinkingEngine(memory_db=":memory:", knowledge_db=":memory:")

# Seed the graph exactly as real cement reasoning would have.
engine.knowledge.add_edge("Fly ash", "substitutes for", "high-clinker Portland formula")
engine.knowledge.add_edge("Dangote cement", "uses", "high-clinker Portland formula")

# The exact real query that caused the bug.
context = engine._gather_context("Lets create a new simple formula to solve calculus")
assert "high-clinker Portland formula" not in context, context
assert "Dangote cement" not in context, context
assert context == ["Memory", "Knowledge Graph", "Planning"], context
print("PASS: 'formula' no longer pulls in unrelated cement context ->", context)

# A genuinely relevant match on a specific term should still work --
# this isn't a blunt fix that breaks the feature it's protecting.
context2 = engine._gather_context("What is the cheapest source of fly ash")
assert "high-clinker Portland formula" in context2, context2
print("PASS: a real topical match (fly ash) still works ->", context2)

# The exact second leak found in real use: "design" pulling in an
# unrelated "New formula design" node from a prior calculus answer
# into a cement question.
engine.knowledge.add_edge("Reasoning", "produced", "New formula design")
context3 = engine._gather_context("Design a cheaper cement and give ingredients")
assert "New formula design" not in context3, context3
print("PASS: 'design' no longer pulls in an unrelated node ->", context3)

engine.close()
print("\nAll context-filtering checks passed.")
NEXUS_EOF_MARKER

echo "Writing engines/thinking/src/test_learning_loop.py"
cat > 'engines/thinking/src/test_learning_loop.py' << 'NEXUS_EOF_MARKER'
"""
Proves the Learning Engine's feedback actually reaches a later,
related reasoning call -- not just that recording/retrieving feedback
works in isolation (that's test_learning.py). Run via:

    python -m engines.thinking.src.test_learning_loop
"""

from unittest import mock

from engines.thinking.src.thinking import ThinkingEngine

engine = ThinkingEngine(memory_db=":memory:", knowledge_db=":memory:")

# Someone marks a past cement answer as unhelpful, with a specific note.
engine.learning.record_feedback(
    "Design a cheaper cement",
    "down",
    note="Didn't account for local SCM availability",
)

captured_prompt = {}


def _fake_ask(prompt, **kwargs):
    captured_prompt["text"] = prompt
    return "Building on feedback. Next action: check local SCM sourcing first.\n\nRELATIONS:\n"


with mock.patch("engines.reasoning.src.reasoner.ask", side_effect=_fake_ask):
    engine.think("Cement that is 40% cheaper and stronger")

assert "Feedback on related past answers" in captured_prompt["text"], captured_prompt["text"]
assert "SCM availability" in captured_prompt["text"], captured_prompt["text"]
print("PASS: a thumbs-down note on a related goal actually reached the reasoning prompt")

# A goal with no related feedback should not mention feedback at all.
with mock.patch("engines.reasoning.src.reasoner.ask", side_effect=_fake_ask):
    engine.think("Best way to learn a new language")

assert "Feedback on related past answers" not in captured_prompt["text"], captured_prompt["text"]
print("PASS: an unrelated goal's prompt has no feedback section at all")

engine.close()
print("\nAll feedback-loop checks passed.")
NEXUS_EOF_MARKER

echo "Writing engines/thinking/src/test_thinking.py"
cat > 'engines/thinking/src/test_thinking.py' << 'NEXUS_EOF_MARKER'
"""
Run from the repo root (not this folder), because ThinkingEngine
imports other engines via their full package path:

    python -m engines.thinking.src.test_thinking
"""

from engines.thinking.src.thinking import ThinkingEngine

engine = ThinkingEngine(memory_db=":memory:", knowledge_db=":memory:")

outcome = engine.think("Discover a stronger concrete")

print("Plan steps:", outcome["plan"]["steps"])
print("Conclusion:", outcome["reasoning"]["conclusion"])
print("Verification:", outcome["verification"])
print("Ideas:", outcome["ideas"])

engine.close()
NEXUS_EOF_MARKER

echo "Writing engines/thinking/src/test_thinking_knowledge_loop.py"
cat > 'engines/thinking/src/test_thinking_knowledge_loop.py' << 'NEXUS_EOF_MARKER'
"""
Proves the Knowledge Graph actually grows from real reasoning, and
that a later, differently-worded goal can find prior context via
keyword search -- not just an exact repeat of the same goal string.
Uses a real (in-memory) KnowledgeGraph, only Reasoner's LLM call is
mocked. Run via:

    python -m engines.thinking.src.test_thinking_knowledge_loop
"""

from unittest import mock

from engines.thinking.src.thinking import ThinkingEngine

FIRST_RESPONSE = """Known: fly ash is a common substitute for Portland cement. Uncertain: local pricing.
Next action: compare regional fly ash cost.

RELATIONS:
Fly ash -> substitutes for -> Portland cement
Cement -> requires -> Limestone
"""

engine = ThinkingEngine(memory_db=":memory:", knowledge_db=":memory:")

# Before anything runs, the graph is genuinely empty.
assert engine.knowledge.show()["nodes"] == {}
print("PASS: graph starts empty, as expected")

with mock.patch("engines.reasoning.src.reasoner.ask", return_value=FIRST_RESPONSE):
    first = engine.think("Design a cheaper cement")

# The graph should now actually contain what reasoning just used --
# not stay empty the way it always used to.
assert engine.knowledge.relation_exists("Fly ash", "substitutes for", "Portland cement")
assert engine.knowledge.relation_exists("Cement", "requires", "Limestone")
print("PASS: extracted relations were actually written to the graph")

# A second, differently-worded goal sharing the word "cement" should
# now find that prior context via keyword search -- not just an exact
# repeat of "Design a cheaper cement".
SECOND_RESPONSE = "Building on prior knowledge. Next action: proceed.\n\nRELATIONS:\n"
with mock.patch("engines.reasoning.src.reasoner.ask", return_value=SECOND_RESPONSE) as mocked:
    second = engine.think("Cement that is 40% cheaper and stronger")

knowledge_used = mocked.call_args
# Check what context ThinkingEngine actually looked up before reasoning.
context = engine._gather_context("Cement that is 40% cheaper and stronger")
assert "Portland cement" in context or "Fly ash" in context or "Limestone" in context, context
print("PASS: a differently-worded goal found prior graph context via keyword search ->", context)

engine.close()
print("\nAll knowledge-graph-loop checks passed.")
NEXUS_EOF_MARKER

echo "Writing engines/thinking/src/thinking.py"
cat > 'engines/thinking/src/thinking.py' << 'NEXUS_EOF_MARKER'
"""
NEXUS Thinking Engine v0.1

Implements the pipeline described in engines/thinking/README.md:
Memory -> Knowledge -> Planning -> Reasoning -> Discovery ->
Verification -> Answer.

This is the fifth version. Memory/Knowledge persist; Planning,
Reasoning, Discovery, and Verification all call a real LLM when a
provider key is set and fall back to simple deterministic behaviour
when it isn't. Reasoning's output gets written into the Knowledge
Graph (context lookup uses keyword search, filtered against generic
terms). Verification sees the plan, not just the reasoning in
isolation. New here: LearningEngine -- the last of the originally
named engines to get real code, aside from Tools -- records feedback
on results and surfaces it for related future goals, so a thumbs-down
note actually changes future reasoning instead of sitting unused.
"""

from engines.memory.src.memory import MemoryEngine
from engines.knowledge.src.graph import KnowledgeGraph
from engines.planning.src.planner import Planner
from engines.reasoning.src.reasoner import Reasoner
from engines.discovery.src.discovery import DiscoveryEngine
from engines.verification.src.verifier import Verifier
from engines.learning.src.learning import LearningEngine

# Words too generic to anchor a keyword search -- found from a real
# case where a calculus question containing "formula" pulled in
# "high-clinker Portland formula" from an unrelated cement answer,
# because "formula" is a substring of that node name even though the
# topics have nothing to do with each other. These are structural/
# categorical nouns that show up across any domain's phrasing, not
# specific enough to mean "these two things are actually related."
_GENERIC_TERMS = {
    "formula", "formulas", "method", "methods", "approach", "approaches",
    "process", "processes", "system", "systems", "result", "results",
    "structure", "structures", "model", "models", "technique", "techniques",
    "strategy", "strategies", "solution", "solutions", "tool", "tools",
    "framework", "concept", "concepts", "idea", "ideas", "factor", "factors",
    "aspect", "aspects", "element", "elements", "component", "components",
    "type", "types", "kind", "kinds", "form", "forms", "way", "ways",
    "design", "designs", "study", "studies", "plan", "plans",
}


class ThinkingEngine:
    def __init__(self, memory_db="data/memory.db", knowledge_db="data/knowledge.db"):
        self.memory = MemoryEngine(db_path=memory_db)
        self.knowledge = KnowledgeGraph(db_path=knowledge_db)
        self.planner = Planner()
        self.reasoner = Reasoner()
        self.discovery = DiscoveryEngine()
        self.verifier = Verifier()
        self.learning = LearningEngine(self.memory)

    def think(self, goal):
        # 1. Remember the goal.
        self.memory.store("last_goal", goal)

        # 2. Pull in whatever the knowledge graph already knows that's
        #    related to this goal.
        knowledge_context = self._gather_context(goal)

        # 3. Plan.
        plan = self.planner.create_plan(goal)

        # 3b. Pull in any feedback on related past goals, so a
        #     thumbs-down note actually changes this reasoning
        #     instead of sitting unused in Memory forever.
        feedback = self.learning.relevant_feedback(goal)

        # 4. Reason using whatever knowledge context and feedback is
        #    available.
        result = self.reasoner.reason(goal=goal, knowledge=knowledge_context, feedback=feedback)

        # 4b. Write back whatever entities/relationships the reasoning
        #     actually relied on. Before this, reasoning happened and
        #     then evaporated -- the graph stayed empty forever no
        #     matter how many goals were reasoned about, even though
        #     the reasoning text kept talking about "querying the
        #     Knowledge Graph" as if it already had content. This is
        #     what makes that true over time instead of aspirational.
        for source, relation, target in result.get("relations", []):
            self.knowledge.add_edge(source, relation, target)

        # 5. Verify the reasoning engine actually produced something
        #    plausible -- now checking it against the plan too, not
        #    just in isolation, so a mismatch between the two (same
        #    number treated as different units, say) can actually be
        #    caught instead of silently passing because each half
        #    read fine on its own.
        verification = self.verifier.verify(
            result.get("conclusion"), goal=goal, plan_steps=plan["steps"]
        )

        # 6. Look for follow-on ideas. Discovery now asks the LLM for
        #    genuinely new angles when available, instead of just
        #    templating the plan's own steps back. discover() now
        #    reports its own method too, same as the other three --
        #    it was the one place that could silently fall back with
        #    no visible sign it had happened.
        discovery_result = self.discovery.discover(plan["steps"], goal=goal)
        ideas = discovery_result["ideas"]

        # 7. Remember the outcome so a future run on the same goal has
        #    something to build on.
        self.memory.store(
            f"result::{goal}",
            {
                "plan": plan,
                "conclusion": result["conclusion"],
                "verification": verification,
                "ideas": ideas,
                "discovery_method": discovery_result["method"],
            },
        )

        return {
            "goal": goal,
            "plan": plan,
            "reasoning": result,
            "verification": verification,
            "ideas": ideas,
            "discovery_method": discovery_result["method"],
        }

    def _gather_context(self, goal, limit=15):
        # Exact match first (the same goal asked before).
        if self.knowledge.exists(goal):
            return self.knowledge.related(goal)

        # Otherwise, search by significant words in the goal, so a
        # related-but-differently-worded goal ("cheaper cement" vs.
        # "cement that's 40% cheaper") can still find prior context
        # instead of needing an exact repeat to ever hit.
        found = []
        goal_lower = goal.lower()

        # Check existing whole node names against the goal text first.
        # Catches multi-word or short entities (e.g. "fly ash") that
        # splitting the goal into individual words would miss, since
        # neither "fly" nor "ash" clears the length filter below on
        # its own -- found via a real test case, not hypothesized.
        for node in self.knowledge.nodes:
            node_lower = node.lower()
            if len(node_lower) > 3 and node_lower in goal_lower and node not in found:
                found.append(node)
                for neighbor in self.knowledge.related(node):
                    if neighbor not in found:
                        found.append(neighbor)

        for word in goal.split():
            word = word.strip(".,!?:;\"'()").lower()
            if len(word) <= 3 or word in _GENERIC_TERMS:
                continue
            for node in self.knowledge.search(word):
                if node not in found:
                    found.append(node)
                    for neighbor in self.knowledge.related(node):
                        if neighbor not in found:
                            found.append(neighbor)

        return found[:limit] if found else ["Memory", "Knowledge Graph", "Planning"]

    def close(self):
        self.memory.close()
        self.knowledge.close()
NEXUS_EOF_MARKER

echo "Writing engines/tools/README.md"
cat > 'engines/tools/README.md' << 'NEXUS_EOF_MARKER'
# NEXUS Tool Engine

## Purpose
Provide access to external capabilities beyond language reasoning.

## Responsibilities

- Web search
- Code execution
- Mathematical computation
- Database access
- API integration
- File operations

## Inputs

- Tool request
- Parameters

## Outputs

- Tool results
- Execution logs
- Errors

## Future

- Dynamic tool selection
- Tool creation
- Parallel execution
- Secure sandboxing
NEXUS_EOF_MARKER

echo "Writing engines/verification/README.md"
cat > 'engines/verification/README.md' << 'NEXUS_EOF_MARKER'
# NEXUS Verification Engine

## Purpose
Ensure every important answer is as accurate as possible before it is returned.

## Responsibilities

- Detect contradictions.
- Verify facts.
- Check mathematical calculations.
- Validate code.
- Measure confidence.

## Inputs

- Proposed answer
- Knowledge
- Tool results

## Outputs

- Verified answer
- Confidence level
- Error report
- Suggested corrections

## Future

- Formal logic verification
- Mathematical proof checking
- Cross-source validation
- Self-critique loops
NEXUS_EOF_MARKER

echo "Writing engines/verification/src/test_verifier.py"
cat > 'engines/verification/src/test_verifier.py' << 'NEXUS_EOF_MARKER'
"""
verifier.py now reaches into core/llm_client.py, so run this from the
repo root:

    python -m engines.verification.src.test_verifier
"""

from engines.verification.src.verifier import Verifier

v = Verifier()

print("Empty conclusion:", v.verify(""))
print("None conclusion:", v.verify(None))
print("Real conclusion (no API key in this environment -> fallback):")
print(v.verify("The bridge can hold 40 tons.", goal="Design a bridge"))
NEXUS_EOF_MARKER

echo "Writing engines/verification/src/test_verifier_llm.py"
cat > 'engines/verification/src/test_verifier_llm.py' << 'NEXUS_EOF_MARKER'
"""
Tests Verifier's response parser against fake LLM replies -- no real
network call, no API key needed. Run via:

    python -m engines.verification.src.test_verifier_llm

This proves the parsing/wiring logic works. It does not prove the
real Anthropic API call works -- this sandbox has no network access,
so that part is untested until you run it yourself with a real key.
"""

from unittest import mock

from engines.verification.src.verifier import Verifier

# --- Internally consistent, but leaning on unverified real-world facts ---
FAKE_RESPONSE = (
    "VERIFIED: yes\n"
    "CONFIDENCE: 0.75\n"
    "ISSUES: none\n"
    "NEEDS_EXTERNAL_CHECK: current Dangote cement price in Naira, which Dangote strength grade is being compared"
)
with mock.patch("engines.verification.src.verifier.ask", return_value=FAKE_RESPONSE):
    verifier = Verifier()
    result = verifier.verify(
        "This blend beats standard Dangote cement on cost and strength.",
        goal="Design a cheaper stronger cement than Dangote",
    )

assert result["method"] == "llm", result
assert result["verified"] is True, result
assert result["issues"] == [], result
assert len(result["needs_external_check"]) == 2, result
print("PASS: a consistent-but-unverified claim is flagged for external check ->", result["needs_external_check"])

# --- Both internal issues and external-check items at once ---
FAKE_RESPONSE_2 = (
    "VERIFIED: no\n"
    "CONFIDENCE: 0.3\n"
    "ISSUES: no published data on this binder, cost estimate unsourced\n"
    "NEEDS_EXTERNAL_CHECK: none"
)
with mock.patch("engines.verification.src.verifier.ask", return_value=FAKE_RESPONSE_2):
    result = Verifier().verify("This binder cuts cost by 40% with no strength loss.", goal="Design a cheaper cement")

assert result["verified"] is False, result
assert len(result["issues"]) == 2, result
assert result["needs_external_check"] == [], result
print("PASS: internal issues and external-check are tracked independently, not conflated")

# --- Pure timeless domain knowledge needs no external check ---
FAKE_RESPONSE_3 = "VERIFIED: yes\nCONFIDENCE: 0.95\nISSUES: none\nNEEDS_EXTERNAL_CHECK: none"
with mock.patch("engines.verification.src.verifier.ask", return_value=FAKE_RESPONSE_3):
    result = Verifier().verify("Water boils at 100C at sea level.", goal="Explain boiling point")

assert result["needs_external_check"] == [], result
print("PASS: general domain knowledge correctly needs no external check")

# --- Empty conclusion and fallback paths still include the new field ---
basic = Verifier().verify("")
assert basic["needs_external_check"] == [], basic
assert basic["method"] == "basic", basic
print("PASS: the empty-conclusion path includes needs_external_check as an empty list, not a missing key")

print("\nAll verifier checks passed.")
NEXUS_EOF_MARKER

echo "Writing engines/verification/src/test_verifier_plan_check.py"
cat > 'engines/verification/src/test_verifier_plan_check.py' << 'NEXUS_EOF_MARKER'
"""
Tests that Verifier actually receives and uses the plan, not just the
reasoning conclusion in isolation -- using the real bag-vs-tonne unit
mismatch found in production, not a hypothetical. Run via:

    python -m engines.verification.src.test_verifier_plan_check
"""

from unittest import mock

from engines.verification.src.verifier import Verifier

PLAN_STEPS = ["Formulate a mix design targeting cost below ₦13,000 per tonne"]
CONCLUSION = "Dangote's cement is priced ~13,000 NGN per bag; our blend must beat that."

captured_prompt = {}


def _fake_ask(prompt, **kwargs):
    captured_prompt["text"] = prompt
    return "VERIFIED: no\nCONFIDENCE: 0.85\nISSUES: plan says per tonne, reasoning says per bag for the same figure"


with mock.patch("engines.verification.src.verifier.ask", side_effect=_fake_ask):
    verifier = Verifier()
    result = verifier.verify(CONCLUSION, goal="Beat Dangote's price", plan_steps=PLAN_STEPS)

assert "per tonne" in captured_prompt["text"], "plan steps were never included in the prompt"
assert "13,000 per tonne" in captured_prompt["text"]
print("PASS: the plan is actually included in what gets sent for verification")

assert result["verified"] is False, result
assert any("per bag" in issue for issue in result["issues"]), result
print("PASS: a plan/reasoning unit mismatch is surfaced as an issue ->", result["issues"])

# Without a plan (backward compatible -- e.g. called with no plan_steps
# at all), it should still work exactly as before.
with mock.patch(
    "engines.verification.src.verifier.ask",
    return_value="VERIFIED: yes\nCONFIDENCE: 0.9\nISSUES: none",
):
    no_plan_result = Verifier().verify("A plain conclusion with no plan given.")
assert no_plan_result["verified"] is True, no_plan_result
print("PASS: verification without a plan still works (backward compatible)")

print("\nAll plan-consistency checks passed.")

# Reproduces the exact real bug: the old prompt said "...or
# plan-mismatch problems" as a category description, and a real
# model echoed the bare word "plan-mismatch" back as its entire
# ISSUES answer -- true, but useless, since it never said what
# actually mismatched.
assert "plan-mismatch" not in captured_prompt["text"], (
    "the old bare category word is still in the prompt -- it's exactly "
    "the kind of phrase a model can echo back verbatim as a non-answer"
)
print("PASS: the prompt no longer contains the bare 'plan-mismatch' label a model echoed back")

assert "50% clinker" in captured_prompt["text"] and "30% clinker replacement" in captured_prompt["text"], (
    "the concrete worked example should be in the prompt, showing what a "
    "SPECIFIC issue description looks like"
)
print("PASS: the prompt shows a concrete example of a specific, useful issue description")

# If a model still returns only a bare label despite the improved
# prompt (never fully guaranteed), parsing must not crash -- it just
# won't be a very useful issue string, which is a prompt-quality
# problem, not a parsing bug.
with mock.patch(
    "engines.verification.src.verifier.ask",
    return_value="VERIFIED: no\nCONFIDENCE: 0.8\nISSUES: plan-mismatch",
):
    bare_result = Verifier().verify("Some claim", plan_steps=["Some step"])
assert bare_result["issues"] == ["plan-mismatch"], bare_result
print("PASS: even a bare-label response still parses without crashing (a prompt problem, not a parser one)")
NEXUS_EOF_MARKER

echo "Writing engines/verification/src/verifier.py"
cat > 'engines/verification/src/verifier.py' << 'NEXUS_EOF_MARKER'
"""
NEXUS Verification Engine v0.4

Calls a real LLM to assess a conclusion three separate ways when a
provider key is set:
  1. Internal consistency -- logically sound, doesn't contradict
     well-established physics/chemistry/math.
  2. Consistency with the plan -- if a plan is given, does the
     reasoning use the same numbers, units, and assumptions as the
     plan, or does it quietly contradict it (e.g. the plan says
     "per tonne" and the reasoning says "per bag" for the same
     figure)? Verification previously only ever saw the reasoning's
     conclusion in isolation -- it had no way to catch this class of
     bug because it never saw the plan at all.
  3. External verifiability -- does it lean on specific real-world
     facts (named companies/products, current prices, dated specs,
     statistics) that the model can't actually know are current or
     accurate, as opposed to general, timeless domain knowledge.

The v0.1 null/empty check still runs first regardless of any of this.
Falls back to the old "any non-empty conclusion passes" behaviour if
the key is missing or the call fails.
"""

from core.llm_client import ask, LLMError


class Verifier:
    def __init__(self, model=None):
        self.model = model

    def verify(self, conclusion, goal=None, plan_steps=None):
        if conclusion is None or (isinstance(conclusion, str) and conclusion.strip() == ""):
            return {
                "verified": False,
                "confidence": 0.0,
                "issues": ["No conclusion to verify"],
                "needs_external_check": [],
                "method": "basic",
            }

        try:
            parsed = self._verify_with_llm(conclusion, goal, plan_steps)
            parsed["method"] = "llm"
            return parsed
        except LLMError as error:
            return {
                "verified": True,  # matches v0.1: any non-empty conclusion passed
                "confidence": None,
                "issues": [f"LLM verification unavailable: {error}"],
                "needs_external_check": [],
                "method": "fallback",
            }

    def _verify_with_llm(self, conclusion, goal, plan_steps):
        plan_block = ""
        if plan_steps:
            steps_text = "\n".join(f"- {s}" for s in plan_steps)
            plan_block = f"Plan this reasoning is supposed to be consistent with:\n{steps_text}\n\n"

        prompt = (
            (f"Goal: {goal}\n\n" if goal else "")
            + plan_block
            + f"Claim to check: {conclusion}\n\n"
            "Assess this claim three separate ways:\n"
            "1. Internal consistency: is it logically sound, and does it "
            "contradict well-established physics, chemistry, or "
            "mathematics?\n"
            "2. Consistency with the plan above, if one is given: does the "
            "claim use the same numbers, units, and assumptions as the "
            "plan? A mismatch here (e.g. one says a price is per tonne, "
            "the other treats the same number as per bag) is a real "
            "issue even if each half reads fine on its own.\n"
            "3. External verifiability: does it state or rely on specific "
            "facts about real, named entities -- companies, products, "
            "current prices, dated specs, statistics -- that could be "
            "outdated or unverified, as opposed to general, timeless "
            "domain knowledge? A claim can be internally consistent and "
            "still need this.\n\n"
            "Reply in EXACTLY this format, nothing else:\n"
            "VERIFIED: yes or no\n"
            "CONFIDENCE: a number from 0 to 1\n"
            "ISSUES: comma-separated list of SPECIFIC problems you found -- "
            "describe what's actually wrong in a few words (e.g. \"plan's "
            "example uses 50% clinker but reasoning's target is at most "
            "30% clinker replacement\"), never just a one- or two-word "
            "category tag with no explanation. Or 'none' if there are no issues.\n"
            "NEEDS_EXTERNAL_CHECK: short comma-separated list of specific "
            "real-world facts that need independent verification (e.g. "
            "\"current market price\", \"named competitor's actual spec\"), or none"
        )

        kwargs = {"model": self.model} if self.model else {}
        response = ask(
            prompt,
            system=(
                "You are the Verification Engine inside NEXUS. Be "
                "skeptical by default. Flag anything unproven as "
                "unproven, flag any mismatch between the plan and the "
                "reasoning even if each sounds fine alone, and never let "
                "internal consistency stand in for factual currency."
            ),
            **kwargs,
        )

        return self._parse(response)

    def _parse(self, response):
        verified = None
        confidence = None
        issues = []
        needs_external_check = []

        for line in response.splitlines():
            line = line.strip()
            upper = line.upper()
            if upper.startswith("NEEDS_EXTERNAL_CHECK:"):
                raw = line.split(":", 1)[1].strip()
                if raw and raw.lower() != "none":
                    needs_external_check = [i.strip() for i in raw.split(",") if i.strip()]
            elif upper.startswith("VERIFIED:"):
                verified = "yes" in line.split(":", 1)[1].strip().lower()
            elif upper.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":", 1)[1].strip())
                except (ValueError, IndexError):
                    confidence = None
            elif upper.startswith("ISSUES:"):
                raw = line.split(":", 1)[1].strip()
                if raw and raw.lower() != "none":
                    issues = [i.strip() for i in raw.split(",") if i.strip()]

        if verified is None:
            raise LLMError(f"Could not parse verification response: {response!r}")

        return {
            "verified": verified,
            "confidence": confidence,
            "issues": issues,
            "needs_external_check": needs_external_check,
        }
NEXUS_EOF_MARKER

echo
echo "Done. Verifying every file compiles cleanly..."
find core engines -name '*.py' | xargs -n1 python3 -m py_compile
echo "All good. Review with: git status"
echo "Then try:  python -m core.nexus"
