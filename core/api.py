"""
NEXUS Cognitive Core - Production API
Separates concerns: this serves ONLY the brain. Frontend lives on Vercel.
"""
import os
import json
import time
from collections import defaultdict
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from engines.thinking.src.thinking import ThinkingEngine
from engines.tools.src.math_tool import MathTool
from engines.business.src.business import BusinessEngine
from engines.nature_core.src.nature_core import NatureCore
from engines.materials.src.materials import MaterialsEngine
from engines.reverse_engineering.src.decomposer import Decomposer
from engines.agriculture.src.agriculture import AgricultureEngine
from engines.tools.src.vision_tool import VisionTool
from engines.memory_semantic.src.semantic_memory import SemanticMemory
from core.llm_client import ask

app = FastAPI(title="NEXUS Cognitive Core API", version="1.0")

# ============================================================
# CORS: Allow the Vercel frontend to call this API
# ============================================================
VERCEL_URLS = [
    "https://YOUR-VERCEL-URL.vercel.app",      # Your future Vercel project URL
    "https://nexus-frontend.vercel.app",  # Alternative name
    "http://localhost:3000",              # Local dev
    "http://127.0.0.1:8000",            # Local fallback
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=VERCEL_URLS + ["*"],  # "*" for testing, tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# RATE LIMITER (In-memory token bucket, per API key)
# ============================================================
class RateLimiter:
    def __init__(self, requests_per_minute=20):
        self.rpm = requests_per_minute
        self.history = defaultdict(list)  # key -> list of timestamps
        
    def check(self, key: str) -> bool:
        now = time.time()
        window = now - 60
        # Purge old entries
        self.history[key] = [t for t in self.history[key] if t > window]
        if len(self.history[key]) >= self.rpm:
            return False
        self.history[key].append(now)
        return True

rate_limiter = RateLimiter(requests_per_minute=20)

# Admin keys (unlimited access). Add your own key here.
ADMIN_KEYS = {
    os.environ.get("NEXUS_API_KEY", ""),      # Your main key = admin
    os.environ.get("NEXUS_ADMIN_KEY", ""),    # Optional second admin key
}
ADMIN_KEYS.discard("")  # Remove empty strings

# ============================================================
# Engine Initialization
# ============================================================
engine = ThinkingEngine()
math_tool = MathTool()
biz_engine = BusinessEngine()
nature_core = NatureCore()
materials_engine = MaterialsEngine()
decomposer = Decomposer()
ag_engine = AgricultureEngine()
vision_tool = VisionTool()
sem_memory = SemanticMemory()

NEXUS_API_KEY = os.environ.get("NEXUS_API_KEY", "")
key_header = APIKeyHeader(name="X-NEXUS-Key", auto_error=False)

def require_key(key: str = Depends(key_header)):
    if not key:
        raise HTTPException(status_code=401, detail="Missing X-NEXUS-Key")
    if NEXUS_API_KEY and key != NEXUS_API_KEY:
        # Allow other admin keys too
        if key not in ADMIN_KEYS:
            raise HTTPException(status_code=401, detail="Invalid key")
    return key

# Apply rate limiting as middleware (runs before every request)
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limit for root health check
    if request.url.path == "/":
        return await call_next(request)
    
    key = request.headers.get("X-NEXUS-Key", "")
    if not key:
        return JSONResponse(status_code=401, content={"detail": "Missing key"})
    
    # Admin bypass
    if key in ADMIN_KEYS:
        return await call_next(request)
    
    # Check rate limit for non-admin
    if not rate_limiter.check(key):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again in 60 seconds."}
        )
    
    return await call_next(request)

class ChatRequest(BaseModel):
    message: str
    image_url: str = ""

# Health check
@app.get("/")
def read_root():
    return {"status": "NEXUS Cognitive Core is online", "version": "1.0"}

@app.post("/chat", dependencies=[Depends(require_key)])
def chat(request: ChatRequest):
    # Vision Check
    if request.image_url:
        vision_result = vision_tool.see(request.image_url, request.message)
        return {"response": vision_result.get("analysis", "I couldn't see the image."), "engine": "vision"}
    
    # Smart Routing
    router_prompt = """You are a routing AI. Based on the user's message, output ONLY ONE of these exact words:
    MATH, BUSINESS, NATURE, MATERIALS, DECOMPOSE, GROW, THINK.
    User Message: """ + request.message
    
    try:
        route = ask(router_prompt, max_tokens=10).strip().upper()
        if route not in ["MATH", "BUSINESS", "NATURE", "MATERIALS", "DECOMPOSE", "GROW", "THINK"]:
            route = "THINK"
    except:
        route = "THINK"
    
    # Execute Engine
    result = {}
    engine_used = route
    if route == "MATH": result = math_tool.calculate(request.message)
    elif route == "BUSINESS": result = biz_engine.plan(request.message, "Provide a street-smart strategy")
    elif route == "NATURE": result = nature_core.investigate(request.message)
    elif route == "MATERIALS": result = materials_engine.formulate(request.message, "Optimize for cost and strength")
    elif route == "DECOMPOSE": result = decomposer.teardown(request.message)
    elif route == "GROW": result = ag_engine.optimize("Grow successfully", request.message)
    else: result = engine.think(request.message)
    
    # Summarize
    summary_prompt = f"You are NEXUS, a battle-tested, street-smart AI mentor. The user asked: '{request.message}'. The {engine_used} engine processed it and found this raw data: {json.dumps(result)[:1500]}. Summarize this data into a helpful, conversational, and bluntly honest response. Speak naturally, do not use JSON format."
    try:
        final_text = ask(summary_prompt, max_tokens=1000)
    except:
        final_text = json.dumps(result)
    
    return {"response": final_text, "engine": engine_used}

# Memory endpoints (keep for direct API access)
class StoreRequest(BaseModel):
    title: str
    content: str
    metadata: dict = {}

class SearchRequest(BaseModel):
    query: str
    limit: int = 3

@app.post("/memory/store", dependencies=[Depends(require_key)])
def store_memory(request: StoreRequest):
    return sem_memory.store_discovery(request.title, request.content, request.metadata)

@app.post("/memory/search", dependencies=[Depends(require_key)])
def search_memory(request: SearchRequest):
    return sem_memory.search_similar(request.query, request.limit)
