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
