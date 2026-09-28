"""
NEXUS LLM Client v0.4 (With Key Rotation)
"""
import json
import os
import re
import time
import urllib.error
import urllib.request
from core.key_pool import current, rotate, pool_size

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
        "default_model": "openrouter/free",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "style": "openai",
    },
    "openai": {
        "key_env": "OPENAI_API_KEY",
        "model_env": "NEXUS_OPENAI_MODEL",
        "default_model": "gpt-4o-mini",
        "url": "https://api.openai.com/v1/chat/completions",
        "style": "openai",
    },
    "anthropic": {
        "key_env": "ANTHROPIC_API_KEY",
        "model_env": "NEXUS_ANTHROPIC_MODEL",
        "default_model": "claude-3-5-sonnet-20240620",
        "url": "https://api.anthropic.com/v1/messages",
        "style": "anthropic",
    },
}

PROVIDER_ORDER = ["groq", "openrouter", "openai", "anthropic"]

class LLMError(Exception):
    pass

def _pick_provider():
    forced = os.environ.get("NEXUS_LLM_PROVIDER")
    if forced and forced in PROVIDERS: return forced
    for name in PROVIDER_ORDER:
        if pool_size(name) > 0: return name
    raise LLMError("No API key set.")

_RETRY_HINT_RE = re.compile(r"try again in ([\d.]+)\s*s", re.IGNORECASE)

def ask(prompt, system=None, model=None, max_tokens=2048, timeout=30, _max_retries=3):
    provider_name = _pick_provider()
    provider = PROVIDERS[provider_name]
    
    # Get the active key for this provider (supports rotation)
    api_key = current(provider_name)
    if not api_key: raise LLMError(f"No key for {provider_name}")

    model = model or os.environ.get(provider["model_env"]) or provider["default_model"]

    if provider["style"] == "openai":
        messages = []
        if system: messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        body = {"model": model, "max_tokens": max_tokens, "messages": messages}
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {api_key}",
            "user-agent": "NEXUS-Client/1.0",
        }
    else: # anthropic
        body = {"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
        if system: body["system"] = system
        headers = {
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "user-agent": "NEXUS-Client/1.0",
        }

    attempts_left = _max_retries + 1
    while True:
        attempts_left -= 1
        request = urllib.request.Request(provider["url"], data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            # ROTATION LOGIC: If 429/401/403, try the next key in the pool
            if error.code in (401, 403, 429) and attempts_left > 0:
                new_key = rotate(provider_name)
                if new_key and new_key != api_key:
                    api_key = new_key
                    # Update headers with new key
                    if provider["style"] == "openai": headers["authorization"] = f"Bearer {api_key}"
                    else: headers["x-api-key"] = api_key
                    continue # Retry with new key
                
                # If no spare key, handle rate limit wait for 429
                if error.code == 429:
                    match = _RETRY_HINT_RE.search(detail)
                    if match:
                        wait = float(match.group(1))
                        if wait <= 15:
                            time.sleep(wait + 0.5)
                            continue
            raise LLMError(f"{provider_name} API returned {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise LLMError(f"Could not reach {provider_name} API: {error.reason}") from error
        except TimeoutError:
            raise LLMError(f"{provider_name} API timeout")

    if provider["style"] == "openai":
        text = data["choices"][0]["message"]["content"]
    else:
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    
    return text.strip()
