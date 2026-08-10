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
