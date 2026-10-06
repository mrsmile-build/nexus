"""
NEXUS LLM Client - Ultimate Resilience Edition.
Primary: Groq. Fallback: tries ALL free OpenRouter models sequentially.
Never gives up on first failure.
"""
import os
import json
import time
import urllib.request
from typing import Optional, List

class LLMError(Exception):
    pass

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "openai/gpt-oss-120b"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_LIST_URL = "https://openrouter.ai/api/v1/models"
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Cache the list of free models for 1 hour
_model_cache = {"models": [], "timestamp": 0}

def _get_free_models() -> List[str]:
    """Fetch live list of free models from OpenRouter."""
    global _model_cache
    now = time.time()
    
    # Return cache if less than 1 hour old
    if _model_cache["models"] and (now - _model_cache["timestamp"]) < 3600:
        return _model_cache["models"]
    
    try:
        req = urllib.request.Request(OPENROUTER_LIST_URL)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        
        # Filter for truly free models (pricing == 0)
        free = [m['id'] for m in data.get('data', []) 
                if m.get('pricing', {}).get('prompt') == '0' 
                and m.get('pricing', {}).get('completion') == '0']
        
        if free:
            _model_cache = {"models": free, "timestamp": now}
            print(f"NEXUS: Cached {len(free)} free OpenRouter models")
            return free
        
        raise ValueError("No free models found")
    except Exception as e:
        print(f"NEXUS: Model discovery failed ({e}), using fallback list")
        # Hardcoded backup list of known-free models
        return [
            "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek/deepseek-chat-v3-0324:free",
            "google/gemini-2.0-flash-exp:free",
            "mistralai/mistral-nemo:free",
            "huggingfaceh4/zephyr-7b-beta:free",
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
    
    models = _get_free_models()
    errors = []
    
    # Try EACH model until one succeeds
    for model in models:
        payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
        try:
            result = _post(OPENROUTER_URL, headers, payload)
            print(f"NEXUS: Success with {model}")
            return result
        except urllib.error.HTTPError as e:
            err_msg = f"{model}:{e.code}"
            errors.append(err_msg)
            print(f"NEXUS: {err_msg}, trying next...")
            continue
        except Exception as e:
            errors.append(f"{model}:{type(e).__name__}")
            continue
    
    # All models failed
    raise LLMError(f"All {len(models)} OpenRouter models failed. Errors: {'; '.join(errors[-3:])}")

def ask(prompt, system="", max_tokens=1000):
    result = _call_groq(prompt, system, max_tokens)
    if result is not None:
        return result
    return _call_openrouter(prompt, system, max_tokens)
