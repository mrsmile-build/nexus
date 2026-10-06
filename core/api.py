"""
NEXUS Cognitive Core - FINAL Production API
All engines + Master Chat Router + thread history + semantic memory + rate limiting.
"""
import os
import json
import time
from collections import defaultdict
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from engines.thinking.src.thinking import ThinkingEngine
from engines.tools.src.math_tool import MathTool
from engines.business.src.business import BusinessEngine
from engines.nature_core.src.nature_core import NatureCore
from engines.materials.src.materials import MaterialsEngine
from engines.reverse_engineering.src.decomposer import Decomposer
from engines.agriculture.src.agriculture import AgricultureEngine
from engines.tools.src.vision_tool import VisionTool
from engines.tools.src.search_tool import SearchTool
from engines.memory_semantic.src.semantic_memory import SemanticMemory
from engines.truth.src.truth_engine import TruthEngine
from engines.blend.src.blend_engine import BlendEngine
from engines.code.src.code_engine import CodeEngine
from engines.skills.src.skills_engine import SkillsEngine
from engines.growth.src.growth_engine import GrowthEngine
from engines.evolution.src.evolution_engine import EvolutionEngine
from engines.briefing.src.briefing_engine import BriefingEngine
from engines.tools.src.telegram_notifier import TelegramNotifier
from core.llm_client import ask

app = FastAPI(title="NEXUS Cognitive Core API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RateLimiter:
    def __init__(self, rpm=20):
        self.rpm = rpm
        self.history = defaultdict(list)
    def check(self, key):
        now = time.time()
        self.history[key] = [t for t in self.history[key] if t > now - 60]
        if len(self.history[key]) >= self.rpm:
            return False
        self.history[key].append(now)
        return True

rate_limiter = RateLimiter(20)
ADMIN_KEYS = {os.environ.get("NEXUS_API_KEY", ""), os.environ.get("NEXUS_ADMIN_KEY", "")}
ADMIN_KEYS.discard("")

engine = ThinkingEngine()
math_tool = MathTool()
biz_engine = BusinessEngine()
nature_core = NatureCore()
materials_engine = MaterialsEngine()
decomposer = Decomposer()
ag_engine = AgricultureEngine()
vision_tool = VisionTool()
search_tool = SearchTool()
sem_memory = SemanticMemory()
truth_engine = TruthEngine()
blend_engine = BlendEngine()
code_engine = CodeEngine()
skills_engine = SkillsEngine()
growth_engine = GrowthEngine()
evolution_engine = EvolutionEngine()
briefing_engine = BriefingEngine()
telegram = TelegramNotifier()

NEXUS_API_KEY = os.environ.get("NEXUS_API_KEY", "")
key_header = APIKeyHeader(name="X-NEXUS-Key", auto_error=False)

def require_key(key: str = Depends(key_header)):
    if not key or (NEXUS_API_KEY and key not in ADMIN_KEYS):
        raise HTTPException(status_code=401, detail="Missing or wrong X-NEXUS-Key")
    return key

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path == "/" or request.method == "OPTIONS":
        return await call_next(request)
    key = request.headers.get("X-NEXUS-Key", "")
    if not key:
        return JSONResponse(status_code=401, content={"detail": "Missing key"})
    if key in ADMIN_KEYS:
        return await call_next(request)
    if not rate_limiter.check(key):
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Wait 60s."})
    return await call_next(request)

# ---------- Request Models ----------
class ChatRequest(BaseModel):
    message: str
    image_url: str = ""
    history: list = []

class ThinkRequest(BaseModel):
    goal: str

class MathRequest(BaseModel):
    expression: str

class BizRequest(BaseModel):
    situation: str
    goal: str

class NatureRequest(BaseModel):
    subject: str
    tradition: str = ""

class MaterialRequest(BaseModel):
    target_material: str
    constraints: str = ""

class DecomposeRequest(BaseModel):
    product: str

class AgRequest(BaseModel):
    goal: str
    current_state: str = ""

class VisionRequest(BaseModel):
    image_url: str
    question: str

class SEORequest(BaseModel):
    topic: str
    target_keyword: str = ""

class ForumRequest(BaseModel):
    question: str
    forum: str = "generic"

class NewsletterRequest(BaseModel):
    days_back: int = 7

class UpgradeRequest(BaseModel):
    artifact: str
    goal: str = "next generation"

class TeachRequest(BaseModel):
    skill: str
    level: str = "beginner"
    context: str = ""

class ReviewRequest(BaseModel):
    code: str
    context: str = ""

class FixRequest(BaseModel):
    code: str
    error: str = ""

class ScaffoldRequest(BaseModel):
    spec: str

class StoreRequest(BaseModel):
    title: str
    content: str
    metadata: dict = {}

class SearchRequest(BaseModel):
    query: str
    limit: int = 3

# ---------- Original Engine Endpoints (kept for Uncle projects) ----------
@app.post("/scheduled/run", dependencies=[Depends(require_key)])
def scheduled_run():
    """Autonomous daily work: research, generate content, create briefing, notify user."""
    import random
    from datetime import datetime

    # 1. Pick a research topic (rotate through themes)
    themes = [
        ("Nigerian business opportunities", "business"),
        ("Agricultural innovations", "agriculture"),
        ("Materials science breakthroughs", "materials"),
        ("Traditional medicine research", "nature"),
    ]
    theme, domain = random.choice(themes)

    # 2. Generate content and store discoveries
    topics = [
        f"Latest {theme} {datetime.now().year}",
        f"Emerging trends in {theme}",
        f"Cost-effective strategies for {theme}",
    ]
    topic = random.choice(topics)

    article = growth_engine.seo_article(topic, theme)
    if article.get("data"):
        try:
            sem_memory.store_discovery(
                title=f"SEO Research: {topic}",
                content=json.dumps(article["data"])[:2000],
                metadata={"domain": domain, "type": "seo_research"}
            )
        except Exception:
            pass

    forum_q = random.choice([
        f"What are the best opportunities in {theme} right now?",
        f"How to succeed in {theme} with limited capital?",
        f"What mistakes do people make in {theme}?",
    ])
    answer = growth_engine.forum_answer(forum_q, forum="generic")
    if answer.get("data"):
        try:
            sem_memory.store_discovery(
                title=f"Forum Insight: {forum_q[:50]}",
                content=json.dumps(answer["data"])[:1500],
                metadata={"domain": domain, "type": "forum_insight"}
            )
        except Exception:
            pass

    # 3. Generate morning briefing
    briefing = briefing_engine.generate_briefing(days_back=7)

    # 4. Send Telegram notification
    telegram_sent = False
    if briefing.get("data"):
        msg = f"<b>🌅 NEXUS Morning Briefing</b>\n\n"
        msg += f"<b>Summary:</b> {briefing['data'].get('summary', 'No summary')}\n\n"
        msg += f"<b>Key Findings:</b>\n"
        for f in briefing['data'].get('key_findings', [])[:3]:
            msg += f"• {f}\n"
        if briefing['data'].get('opportunities'):
            msg += f"\n<b>Opportunities:</b>\n"
            for o in briefing['data'].get('opportunities', [])[:2]:
                msg += f"• {o}\n"
        msg += f"\n<i>Open NEXUS to see full details.</i>"

        result = telegram.send(msg)
        telegram_sent = result.get("sent", False)

    return {
        "article": article,
        "forum_answer": answer,
        "briefing": briefing,
        "telegram_sent": telegram_sent,
        "method": "autonomous_daily_run"
    }

@app.get("/")
def read_root():
    return {"status": "NEXUS Cognitive Core is online and ready.", "version": "2.0"}

@app.post("/think", dependencies=[Depends(require_key)])
def think(request: ThinkRequest):
    return engine.think(request.goal)

@app.post("/math", dependencies=[Depends(require_key)])
def math(request: MathRequest):
    return math_tool.calculate(request.expression)

@app.post("/mentor", dependencies=[Depends(require_key)])
def mentor(request: BizRequest):
    return biz_engine.plan(request.situation, request.goal)

@app.post("/nature", dependencies=[Depends(require_key)])
def nature(request: NatureRequest):
    return nature_core.investigate(request.subject, request.tradition)

@app.post("/materials", dependencies=[Depends(require_key)])
def materials(request: MaterialRequest):
    return materials_engine.formulate(request.target_material, request.constraints)

@app.post("/decompose", dependencies=[Depends(require_key)])
def decompose(request: DecomposeRequest):
    return decomposer.teardown(request.product)

@app.post("/grow", dependencies=[Depends(require_key)])
def grow(request: AgRequest):
    return ag_engine.optimize(request.goal, request.current_state)

@app.post("/see", dependencies=[Depends(require_key)])
def see(request: VisionRequest):
    return vision_tool.see(request.image_url, request.question)

@app.post("/growth/seo", dependencies=[Depends(require_key)])
def growth_seo(request: SEORequest):
    return growth_engine.seo_article(request.topic, request.target_keyword)

@app.post("/growth/forum", dependencies=[Depends(require_key)])
def growth_forum(request: ForumRequest):
    return growth_engine.forum_answer(request.question, request.forum)

@app.post("/growth/newsletter", dependencies=[Depends(require_key)])
def growth_newsletter(request: NewsletterRequest):
    return growth_engine.newsletter_digest(request.days_back)

@app.post("/briefing", dependencies=[Depends(require_key)])
def get_briefing():
    return briefing_engine.generate_briefing(days_back=7)

@app.post("/evolution/upgrade, dependencies=[Depends(require_key)])
def evolution_upgrade(request: UpgradeRequest):
    return evolution_engine.upgrade(request.artifact, request.goal)

@app.post("/skills/teach", dependencies=[Depends(require_key)])
def skills_teach(request: TeachRequest):
    return skills_engine.teach(request.skill, request.level, request.context)

@app.post("/code/review", dependencies=[Depends(require_key)])
def code_review(request: ReviewRequest):
    return code_engine.review(request.code, request.context)

@app.post("/code/fix", dependencies=[Depends(require_key)])
def code_fix(request: FixRequest):
    return code_engine.fix(request.code, request.error)

@app.post("/code/scaffold", dependencies=[Depends(require_key)])
def code_scaffold(request: ScaffoldRequest):
    return code_engine.scaffold(request.spec)

@app.post("/memory/store", dependencies=[Depends(require_key)])
def store_memory(request: StoreRequest):
    return sem_memory.store_discovery(request.title, request.content, request.metadata)

@app.post("/memory/search", dependencies=[Depends(require_key)])
def search_memory(request: SearchRequest):
    return sem_memory.search_similar(request.query, request.limit)

# ---------- Master Chat Router ----------
@app.post("/chat", dependencies=[Depends(require_key)])
def chat(request: ChatRequest):
    if request.image_url:
        vision_result = vision_tool.see(request.image_url, request.message or "Describe this image.")
        return {"response": vision_result.get("analysis", "I couldn't see the image."), "engine": "vision"}

    router_prompt = """You are a routing AI. Choose the single best engine.
MATH=calculations. BUSINESS=money/startups/pricing/profit/selling/broke. NATURE=plants/herbs/medicine/charms. MATERIALS=cement/alloys/chemicals/manufacturing/formulations. DECOMPOSE=teardowns/how-made/supply-chain. GROW=farming/soil/crops. BLEND=substitutes/ratios/combining/‘I don't have X’/recreating something from parts (moringa, limestone, water). CODE=programming/debug/review/fix/scaffold/build software. SKILLS=teach/learn/explain/master any skill, craft, trade, art or how-to (old or modern, physical or online). EVOLUTION=upgrade/improve/next-generation/future-proof any product, system, or technology (iPhone, bridge, medicine, car). THINK=everything else.
Reply with ONLY the engine word.
User Message: """ + request.message
    try:
        raw_route = ask(router_prompt, max_tokens=12).strip().upper()
        route = "THINK"
        for cand in ["MATERIALS", "DECOMPOSE", "BUSINESS", "NATURE", "MATH", "GROW", "BLEND", "CODE", "SKILLS", "THINK"]:
            if cand in raw_route:
                route = cand
                break
    except Exception:
        route = "THINK"

    result = {}
    engine_used = route
    if route == "MATH": result = math_tool.calculate(request.message)
    elif route == "BUSINESS": result = biz_engine.plan(request.message, "Provide a street-smart scored strategy")
    elif route == "NATURE": result = nature_core.investigate(request.message)
    elif route == "MATERIALS": result = materials_engine.formulate(request.message, "Optimize for cost and strength")
    elif route == "DECOMPOSE": result = decomposer.teardown(request.message)
    elif route == "GROW": result = ag_engine.optimize("Grow successfully", request.message)
    elif route == "BLEND": result = blend_engine.blend(request.message)
    elif route == "CODE": result = {"note": "Use /code/review, /code/fix or /code/scaffold for full power", "quick": engine.think(request.message)}
    elif route == "SKILLS": result = skills_engine.teach(request.message)
    elif route == "EVOLUTION": result = evolution_engine.upgrade(request.message)
    else: result = engine.think(request.message)

    try:
        hits = sem_memory.search_similar(request.message, limit=2)
        mem_lines = [f"- {h['title']}: {h['preview']}" for h in hits.get("results", []) if h.get("score", 0) > 0.35]
        memory_context = "\n".join(mem_lines) if mem_lines else "None"
    except Exception:
        memory_context = "None"

    thread_hist = "\n".join([f"{m.get('role','User')}: {str(m.get('text',''))[:400]}" for m in request.history[-4:]])

    summary_prompt = f"""You are NEXUS, a battle-tested, street-smart AI mentor.
RECENT THREAD HISTORY:
{thread_hist if thread_hist else '(none)'}

The user just asked: '{request.message}'
YOUR RELEVANT MEMORY:
{memory_context}

The {engine_used} engine processed it and found this raw data: {json.dumps(result)[:6000]}.
Summarize into a helpful, conversational, bluntly honest response. Speak naturally, do not use JSON format. COMPLETE your answer fully - never cut off mid-sentence. If the user asks a follow-up, reference the thread history. If memory already contains a relevant answer, build on it."""
    try:
        final_text = ask(summary_prompt, max_tokens=4000)
    except Exception:
        final_text = json.dumps(result)[:3000]

    # TRUTH ENGINE: adversarial verification on every answer
    truth_checked = False
    try:
        final_text, critique = truth_engine.verify(request.message, final_text)
        truth_checked = True
    except Exception:
        pass

    return {"response": final_text, "engine": engine_used, "truth_checked": truth_checked}
