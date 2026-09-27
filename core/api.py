import os

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from engines.thinking.src.thinking import ThinkingEngine
from engines.tools.src.math_tool import MathTool

app = FastAPI(title="NEXUS Cognitive Core")
engine = ThinkingEngine()
math_tool = MathTool()

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


@app.get("/")
def read_root():
    return {"status": "NEXUS Cognitive Core is online and ready."}


@app.post("/think", dependencies=[Depends(require_key)])
def think(request: GoalRequest):
    return engine.think(request.goal)


@app.post("/math", dependencies=[Depends(require_key)])
def math(request: MathRequest):
    return math_tool.calculate(request.expression)
