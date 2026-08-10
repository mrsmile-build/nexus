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
