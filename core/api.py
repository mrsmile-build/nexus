import os
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from engines.thinking.src.thinking import ThinkingEngine
from engines.tools.src.math_tool import MathTool
from engines.business.src.business import BusinessEngine
from engines.nature_core.src.nature_core import NatureCore
from engines.materials.src.materials import MaterialsEngine
from engines.reverse_engineering.src.decomposer import Decomposer
from engines.agriculture.src.agriculture import AgricultureEngine

app = FastAPI(title="NEXUS Cognitive Core")
engine = ThinkingEngine()
math_tool = MathTool()
biz_engine = BusinessEngine()
nature_core = NatureCore()
materials_engine = MaterialsEngine()
decomposer = Decomposer()
ag_engine = AgricultureEngine()

NEXUS_API_KEY = os.environ.get("NEXUS_API_KEY", "")
key_header = APIKeyHeader(name="X-NEXUS-Key", auto_error=False)

def require_key(key: str = Depends(key_header)):
    if NEXUS_API_KEY and key != NEXUS_API_KEY:
        raise HTTPException(status_code=401, detail="Missing or wrong X-NEXUS-Key")
    return key

class GoalRequest(BaseModel):
    goal: str
class MathRequest(BaseModel):
    expression: str
class BizRequest(BaseModel):
    situation: str
    goal: str
class NatureRequest(BaseModel):
    subject: str
    tradition: str = "General"
class MaterialRequest(BaseModel):
    target_material: str
    constraints: str
class DecomposeRequest(BaseModel):
    product: str
class AgRequest(BaseModel):
    goal: str
    current_state: str

@app.get("/")
def read_root():
    return {"status": "NEXUS Cognitive Core is online and ready."}

@app.post("/think", dependencies=[Depends(require_key)])
def think(request: GoalRequest): return engine.think(request.goal)

@app.post("/math", dependencies=[Depends(require_key)])
def math(request: MathRequest): return math_tool.calculate(request.expression)

@app.post("/mentor", dependencies=[Depends(require_key)])
def mentor(request: BizRequest): return biz_engine.plan(request.situation, request.goal)

@app.post("/nature", dependencies=[Depends(require_key)])
def nature(request: NatureRequest): return nature_core.investigate(request.subject, request.tradition)

@app.post("/materials", dependencies=[Depends(require_key)])
def materials(request: MaterialRequest): return materials_engine.formulate(request.target_material, request.constraints)

@app.post("/decompose", dependencies=[Depends(require_key)])
def decompose(request: DecomposeRequest): return decomposer.teardown(request.product)

@app.post("/grow", dependencies=[Depends(require_key)])
def grow(request: AgRequest): return ag_engine.optimize(request.goal, request.current_state)

from engines.tools.src.vision_tool import VisionTool
vision_tool = VisionTool()

class VisionRequest(BaseModel):
    image_url: str
    question: str

@app.post("/see", dependencies=[Depends(require_key)])
def see(request: VisionRequest):
    return vision_tool.see(request.image_url, request.question)

from engines.memory_semantic.src.semantic_memory import SemanticMemory
sem_memory = SemanticMemory()

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
