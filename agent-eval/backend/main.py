from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.agents.datapilot import DataPilot
from backend.agents.datapilot.llm_client import OpenAICompatibleClient
from backend.agents.datapilot.tools import DataPilotTools
from backend.config import get_settings
from backend.data import DATABASE_PATH, ensure_database
from backend.datasets import load_cases
from backend.evaluators import evaluate_run
from backend.schemas import AgentRun, Case, EvaluationResult


BACKEND_DIR = Path(__file__).resolve().parent
METRICS_PATH = BACKEND_DIR / "data" / "metrics.json"

settings = get_settings()
ensure_database()
cases = {case.case_id: case for case in load_cases()}
runs: dict[str, AgentRun] = {}
evaluations: dict[str, EvaluationResult] = {}

tools = DataPilotTools(DATABASE_PATH, METRICS_PATH)
agent = DataPilot(tools, OpenAICompatibleClient(settings))

app = FastAPI(
    title="AgentEval API",
    version="0.1.0",
    description="DataPilot execution and trace-based Agent evaluation API",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class AgentRunRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    agent_version: Literal["v1.0", "v0.9-direct"] = "v1.0"


class EvaluationRunRequest(BaseModel):
    case_id: str
    agent_version: Literal["v1.0", "v0.9-direct"] = "v1.0"


class HealthResponse(BaseModel):
    status: str
    model: str
    provider: str
    api_configured: bool
    cases: int


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model=settings.model,
        provider=settings.base_url,
        api_configured=settings.is_configured,
        cases=len(cases),
    )


@app.post("/api/agent/run", response_model=AgentRun)
def run_agent(request: AgentRunRequest) -> AgentRun:
    run = agent.run(request.query, request.agent_version)
    runs[run.run_id] = run
    return run


@app.get("/api/runs/{run_id}", response_model=AgentRun)
def get_run(run_id: str) -> AgentRun:
    if run_id not in runs:
        raise HTTPException(status_code=404, detail="Run 不存在")
    return runs[run_id]


@app.get("/api/cases", response_model=list[Case])
def get_cases() -> list[Case]:
    return list(cases.values())


@app.post("/api/evaluations/run", response_model=EvaluationResult)
def run_evaluation(request: EvaluationRunRequest) -> EvaluationResult:
    case = cases.get(request.case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case 不存在")
    run = agent.run(case.query, request.agent_version)
    runs[run.run_id] = run
    evaluation = evaluate_run(case, run)
    evaluations[evaluation.evaluation_id] = evaluation
    return evaluation


@app.get("/api/evaluations/{evaluation_id}", response_model=EvaluationResult)
def get_evaluation(evaluation_id: str) -> EvaluationResult:
    if evaluation_id not in evaluations:
        raise HTTPException(status_code=404, detail="Evaluation 不存在")
    return evaluations[evaluation_id]


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "AgentEval API", "docs": "/docs", "health": "/api/health"}
