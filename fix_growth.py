import sys

path = 'core/api.py'
try:
    with open(path, 'r') as f:
        s = f.read()
except FileNotFoundError:
    print("ERROR: core/api.py not found")
    sys.exit(1)

# 1. Import
target_import = "from engines.skills.src.skills_engine import SkillsEngine"
new_import = "from engines.skills.src.skills_engine import SkillsEngine\nfrom engines.growth.src.growth_engine import GrowthEngine"
if "GrowthEngine" not in s and target_import in s:
    s = s.replace(target_import, new_import)
    print("[OK] Import patched")
else:
    print("[SKIP] Import already present or target not found")

# 2. Init
target_init = "skills_engine = SkillsEngine()"
new_init = "skills_engine = SkillsEngine()\ngrowth_engine = GrowthEngine()"
if "growth_engine =" not in s and target_init in s:
    s = s.replace(target_init, new_init)
    print("[OK] Init patched")
else:
    print("[SKIP] Init already present or target not found")

# 3. Models
target_models = "class TeachRequest(BaseModel):"
new_models = """class SEORequest(BaseModel):
    topic: str
    target_keyword: str = ""

class ForumRequest(BaseModel):
    question: str
    forum: str = "generic"

class NewsletterRequest(BaseModel):
    days_back: int = 7

class TeachRequest(BaseModel):"""
if "class SEORequest" not in s and target_models in s:
    s = s.replace(target_models, new_models)
    print("[OK] Models patched")
else:
    print("[SKIP] Models already present or target not found")

# 4. Endpoints
target_ep = '@app.post("/skills/teach", dependencies=[Depends(require_key)])'
new_ep = """@app.post("/growth/seo", dependencies=[Depends(require_key)])
def growth_seo(request: SEORequest):
    return growth_engine.seo_article(request.topic, request.target_keyword)

@app.post("/growth/forum", dependencies=[Depends(require_key)])
def growth_forum(request: ForumRequest):
    return growth_engine.forum_answer(request.question, request.forum)

@app.post("/growth/newsletter", dependencies=[Depends(require_key)])
def growth_newsletter(request: NewsletterRequest):
    return growth_engine.newsletter_digest(request.days_back)

@app.post("/skills/teach", dependencies=[Depends(require_key)])"""
if "/growth/seo" not in s and target_ep in s:
    s = s.replace(target_ep, new_ep)
    print("[OK] Endpoints patched")
else:
    print("[SKIP] Endpoints already present or target not found")

# 5. Scheduled Run
target_sched = '@app.get("/")'
new_sched = """@app.post("/scheduled/run", dependencies=[Depends(require_key)])
def scheduled_run():
    # Daily autonomous work
    import random
    topics = [
        ("How to start a palm oil refining business in Nigeria", "palm oil business Nigeria"),
        ("10 proven farm-to-table business ideas in Lagos 2026", "farm business Lagos"),
        ("Why soap making is the most recession-proof small business", "soap making business"),
        ("How to export Nigerian agricultural products to Europe", "export agriculture Nigeria"),
        ("Cheapest cement formula for small-scale builders", "cement formula cheap"),
    ]
    topic, kw = random.choice(topics)
    article = growth_engine.seo_article(topic, kw)
    forum_q = random.choice([
        "What's the best small business to start in Nigeria with 100k naira?",
        "How do I start exporting from Nigeria?",
        "Is AI useful for small businesses in Africa?",
    ])
    answer = growth_engine.forum_answer(forum_q, forum="nairaland")
    return {"article": article, "forum_answer": answer, "method": "scheduled_run"}

@app.get("/")"""
if "/scheduled/run" not in s and target_sched in s:
    s = s.replace(target_sched, new_sched)
    print("[OK] Scheduled run patched")
else:
    print("[SKIP] Scheduled run already present or target not found")

with open(path, 'w') as f:
    f.write(s)

print("Done. Patching complete.")
