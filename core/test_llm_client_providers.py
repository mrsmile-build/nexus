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
