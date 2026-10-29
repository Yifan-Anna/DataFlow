from typing import Any, Literal

from pydantic import BaseModel, Field


class TraceStep(BaseModel):
    step: int
    type: Literal["tool_call"] = "tool_call"
    tool: str
    input: dict[str, Any]
    output: dict[str, Any] | None = None
    status: Literal["success", "failed"]
    latency_ms: int = Field(ge=0)
    error: str | None = None


class StructuredResult(BaseModel):
    metric: Literal["GMV", "订单量"]
    value: float | int
    unit: Literal["元", "单"]
    year: int
    month: int = Field(ge=1, le=12)
    previous_value: float | int | None = None
    mom_rate: float | None = None


class AgentRun(BaseModel):
    run_id: str
    agent_name: str = "DataPilot"
    agent_version: str
    query: str
    status: Literal["completed", "failed"]
    trace: list[TraceStep]
    final_answer: str
    structured_result: StructuredResult | None = None
    total_latency_ms: int = Field(ge=0)
    error: str | None = None
