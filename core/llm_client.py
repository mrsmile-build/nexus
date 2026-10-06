"""
NEXUS LLM Client with automatic multi-model fallback.
Primary: Groq. Fallback chain: tries several OpenRouter models until one succeeds.
"""
import os
import json
import urllib.request
from typing import Optional

class LLMError(Exception):
    pass

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "openai/gpt-oss-120b"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
# Try in order; first one that returns 200 wins. All are currently live on OpenRouter.
FALLBACK_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-chat-v3-0324:free",
    "google/gemini-2.0-flash-exp:free",
    "mistralai/mistral-nemo:free",
]

def _post(url, headers, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())["choices"][0]["message"]["content"]

def _call_groq(prompt, system="", max_tokens=1000):
    if not GROQ_KEY:
        return None
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {"model": GROQ_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.7}
    try:
        return _post(GROQ_URL, headers, payload)
    except urllib.error.HTTPError as e:
        if e.code in (429, 403, 503):
            return None  # signal fallback
        raise LLMError(f"Groq {e.code}: {e.read().decode()[:300]}")
    except Exception:
        return None

def _call_openrouter(prompt, system="", max_tokens=1000):
    if not OPENROUTER_KEY:
        raise LLMError("No OpenRouter key and Groq unavailable")
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json",
               "HTTP-Referer": "https://nexus-core.onrender.com", "X-Title": "NEXUS Cognitive Core"}
    last_err = ""
    for model in FALLBACK_MODELS:
        payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
        try:
            return _call_or(model, headers, payload)
        except urllib.error.HTTPError as e:
            last_err = f"{model}->{e.code}"
            continue  # try next model
        except Exception as e:
            last_err = f"{model}->{type(e).__name__}"
            continue
    raise LLMError(f"All OpenRouter models failed. Last: {last_err}")

def _call_or(model, headers, payload):
    req = urllib.request.Request(OPENROUTER_URL, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())["choices"][0]["message"]["content"]

def ask(prompt, system="", max_tokens=1000):
    result = _call_groq(prompt, system, max_tokens)
    if result is not None:
        return result
    return _call_openrouter(prompt, system, max_tokens)
