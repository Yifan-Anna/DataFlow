from typing import Any

from pydantic import BaseModel, Field


class DimensionResult(BaseModel):
    passed: bool = Field(alias="pass")
    score: float = Field(ge=0, le=1)
    message: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True, "serialize_by_alias": True}


class EvaluationResult(BaseModel):
    evaluation_id: str
    run_id: str
    case_id: str
    overall_pass: bool
    score: float = Field(ge=0, le=1)
    dimensions: dict[str, DimensionResult]
    failure_types: list[str] = Field(default_factory=list)
