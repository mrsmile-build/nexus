"""
NEXUS LLM Client with automatic fallback.
Primary: Groq (openai/gpt-oss-120b)
Fallback: OpenRouter (google/gemini-flash-1.5) when Groq rate-limited
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
OPENROUTER_MODEL = "google/gemini-flash-1.5"

def _call_groq(prompt: str, system: str = "", max_tokens: int = 1000) -> Optional[str]:
    if not GROQ_KEY:
        return None
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json",
    }
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = json.dumps({
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }).encode()
    req = urllib.request.Request(GROQ_URL, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        if e.code == 429:
            return None  # Signal fallback
        raise LLMError(f"Groq {e.code}: {body[:300]}")
    except Exception as e:
        return None  # Signal fallback on any network error

def _call_openrouter(prompt: str, system: str = "", max_tokens: int = 1000) -> str:
    if not OPENROUTER_KEY:
        raise LLMError("OpenRouter key missing and Groq rate-limited")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://nexus-core.onrender.com",
        "X-Title": "NEXUS Cognitive Core",
    }
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = json.dumps({
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(OPENROUTER_URL, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        raise LLMError(f"OpenRouter {e.code}: {body[:300]}")
    except Exception as e:
        raise LLMError(f"OpenRouter network error: {e}")

def ask(prompt: str, system: str = "", max_tokens: int = 1000) -> str:
    """Try Groq first, fall back to OpenRouter on rate limit."""
    result = _call_groq(prompt, system, max_tokens)
    if result is not None:
        return result
    # Groq failed — fall back silently to OpenRouter
    return _call_openrouter(prompt, system, max_tokens)
