"""
NEXUS LLM Client with Dynamic Model Discovery.
Primary: Groq. Fallback: Asks OpenRouter for live list of free models.
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
OPENROUTER_LIST_URL = "https://openrouter.ai/api/v1/models"
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Cache the discovered model so we don't fetch the list every time
_cached_fallback_model = None

def _get_best_free_model():
    """Fetch live list from OpenRouter and find a working free model."""
    global _cached_fallback_model
    if _cached_fallback_model:
        return _cached_fallback_model
    
    try:
        req = urllib.request.Request(OPENROUTER_LIST_URL)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            
        # Filter for free models (pricing 0)
        free_models = [m['id'] for m in data.get('data', []) 
                       if m.get('pricing', {}).get('prompt') == '0' 
                       and m.get('pricing', {}).get('completion') == '0']
        
        if not free_models:
            raise ValueError("No free models found on OpenRouter")
            
        # Pick the first one (usually llama or deepseek)
        _cached_fallback_model = free_models[0]
        print(f"NEXUS: Discovered fallback model {_cached_fallback_model}")
        return _cached_fallback_model
        
    except Exception as e:
        print(f"NEXUS: Failed to discover models ({e}), using default")
        _cached_fallback_model = "meta-llama/llama-3.3-70b-instruct:free"
        return _cached_fallback_model

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
    
    model = _get_best_free_model()
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json",
               "HTTP-Referer": "https://nexus-core.onrender.com", "X-Title": "NEXUS Cognitive Core"}
    
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
    
    try:
        return _post(OPENROUTER_URL, headers, payload)
    except urllib.error.HTTPError as e:
        # If the dynamic model fails, clear cache and try again once
        global _cached_fallback_model
        _cached_fallback_model = None
        model = _get_best_free_model()
        payload["model"] = model
        try:
            return _post(OPENROUTER_URL, headers, payload)
        except Exception as e2:
            raise LLMError(f"OpenRouter failed even after refresh: {e2}")

def ask(prompt, system="", max_tokens=1000):
    result = _call_groq(prompt, system, max_tokens)
    if result is not None:
        return result
    return _call_openrouter(prompt, system, max_tokens)
