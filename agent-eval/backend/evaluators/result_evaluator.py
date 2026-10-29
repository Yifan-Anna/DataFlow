from __future__ import annotations

import math

from backend.schemas import AgentRun, Case, DimensionResult


def evaluate_result(case: Case, run: AgentRun) -> tuple[DimensionResult, list[str]]:
    if run.status != "completed" or run.structured_result is None:
        return (
            DimensionResult(**{"pass": False}, score=0, message="Agent 未成功返回结构化结果"),
            ["AGENT_RUN_FAILED"],
        )

    result = run.structured_result
    actual: dict[str, float | int | None] = {
        "gmv": result.value if result.metric == "GMV" else None,
        "order_count": result.value if result.metric == "订单量" else None,
        "current_gmv": result.value if result.metric == "GMV" else None,
        "previous_gmv": result.previous_value if result.metric == "GMV" else None,
        "current_order_count": result.value if result.metric == "订单量" else None,
        "previous_order_count": result.previous_value if result.metric == "订单量" else None,
        "mom_rate": result.mom_rate,
    }
    mismatches = {}
    for key, expected_value in case.expected.result.items():
        actual_value = actual.get(key)
        if actual_value is None or not math.isclose(float(actual_value), float(expected_value), rel_tol=1e-6, abs_tol=1e-6):
            mismatches[key] = {"expected": expected_value, "actual": actual_value}

    passed = not mismatches
    return (
        DimensionResult(
            **{"pass": passed},
            score=1.0 if passed else 0.0,
            message="核心结果与 Ground Truth 一致" if passed else "核心结果与 Ground Truth 不一致",
            details={"expected": case.expected.result, "actual": {key: actual.get(key) for key in case.expected.result}, "mismatches": mismatches},
        ),
        [] if passed else ["INCORRECT_RESULT"],
    )
