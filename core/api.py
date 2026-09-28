import os
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from engines.thinking.src.thinking import ThinkingEngine
from engines.tools.src.math_tool import MathTool
from engines.business.src.business import BusinessEngine
from engines.nature_core.src.nature_core import NatureCore

app = FastAPI(title="NEXUS Cognitive Core")
engine = ThinkingEngine()
math_tool = MathTool()
biz_engine = BusinessEngine()
nature_core = NatureCore()

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

@app.get("/")
def read_root():
    return {"status": "NEXUS Cognitive Core is online and ready."}

@app.post("/think", dependencies=[Depends(require_key)])
def think(request: GoalRequest):
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
