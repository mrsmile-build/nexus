import sys

path = 'core/api.py'
try:
    with open(path, 'r') as f:
        s = f.read()
except FileNotFoundError:
    print("ERROR: core/api.py not found")
    sys.exit(1)

# 1. Import
target_import = "from engines.growth.src.growth_engine import GrowthEngine"
new_import = "from engines.growth.src.growth_engine import GrowthEngine\nfrom engines.evolution.src.evolution_engine import EvolutionEngine"
if "EvolutionEngine" not in s and target_import in s:
    s = s.replace(target_import, new_import)
    print("[OK] Import patched")
else:
    print("[SKIP] Import already present or target not found")

# 2. Init
target_init = "growth_engine = GrowthEngine()"
new_init = "growth_engine = GrowthEngine()\nevolution_engine = EvolutionEngine()"
if "evolution_engine =" not in s and target_init in s:
    s = s.replace(target_init, new_init)
    print("[OK] Init patched")
else:
    print("[SKIP] Init already present or target not found")

# 3. Model
target_model = "class TeachRequest(BaseModel):"
new_model = """class UpgradeRequest(BaseModel):
    artifact: str
    goal: str = "next generation"

class TeachRequest(BaseModel):"""
if "class UpgradeRequest" not in s and target_model in s:
    s = s.replace(target_model, new_model)
    print("[OK] Model patched")
else:
    print("[SKIP] Model already present or target not found")

# 4. Endpoint
target_ep = '@app.post("/skills/teach", dependencies=[Depends(require_key)])'
new_ep = """@app.post("/evolution/upgrade", dependencies=[Depends(require_key)])
def evolution_upgrade(request: UpgradeRequest):
    return evolution_engine.upgrade(request.artifact, request.goal)

@app.post("/skills/teach", dependencies=[Depends(require_key)])"""
if "/evolution/upgrade" not in s and target_ep in s:
    s = s.replace(target_ep, new_ep)
    print("[OK] Endpoint patched")
else:
    print("[SKIP] Endpoint already present or target not found")

# 5. Router
target_router = 'SKILLS=teach/learn/explain/master any skill, craft, trade, art or how-to (old or modern, physical or online). THINK=everything else.'
new_router = 'SKILLS=teach/learn/explain/master any skill, craft, trade, art or how-to (old or modern, physical or online). EVOLUTION=upgrade/improve/next-generation/future-proof any product, system, or technology (iPhone, bridge, medicine, car). THINK=everything else.'
if "EVOLUTION=" not in s and target_router in s:
    s = s.replace(target_router, new_router)
    print("[OK] Router patched")
else:
    print("[SKIP] Router already present or target not found")

# 6. Route Dispatch
target_dispatch = '    elif route == "SKILLS": result = skills_engine.teach(request.message)\n    else: result = engine.think(request.message)'
new_dispatch = '    elif route == "SKILLS": result = skills_engine.teach(request.message)\n    elif route == "EVOLUTION": result = evolution_engine.upgrade(request.message)\n    else: result = engine.think(request.message)'
if 'route == "EVOLUTION"' not in s and target_dispatch in s:
    s = s.replace(target_dispatch, new_dispatch)
    print("[OK] Dispatch patched")
else:
    print("[SKIP] Dispatch already present or target not found")

with open(path, 'w') as f:
    f.write(s)

print("Done. Evolution Engine wiring complete.")
