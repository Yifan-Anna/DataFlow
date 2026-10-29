from typing import Any

from pydantic import BaseModel, Field


class CaseExpected(BaseModel):
    result: dict[str, Any]
    tools: list[str]
    tool_order: list[str]


class Case(BaseModel):
    case_id: str
    name: str
    category: str
    query: str
    expected: CaseExpected
    tags: list[str] = Field(default_factory=list)
