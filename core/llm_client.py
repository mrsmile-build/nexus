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
