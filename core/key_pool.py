"""
NEXUS Key Pool v0.1
Provider key rotation.
"""
import os

_SUFFIXES = ("", "_2", "_3")
_BASE = {
    "groq": "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}
_state = {}

def pool(provider):
    base = _BASE[provider]
    return [k for k in (os.environ.get(base + s) for s in _SUFFIXES) if k]

def pool_size(provider):
    return len(pool(provider))

def current(provider):
    keys = pool(provider)
    if not keys: return None
    return keys[_state.get(provider, 0) % len(keys)]

def rotate(provider):
    keys = pool(provider)
    if len(keys) < 2: return current(provider)
    _state[provider] = (_state.get(provider, 0) + 1) % len(keys)
    return keys[_state[provider]]
