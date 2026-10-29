from backend.schemas import AgentRun, Case, DimensionResult


def evaluate_trajectory(case: Case, run: AgentRun) -> tuple[DimensionResult, list[str]]:
    actual = [step.tool for step in run.trace if step.status == "success"]
    expected = case.expected.tool_order
    passed = actual == expected
    matching_prefix = 0
    for expected_tool, actual_tool in zip(expected, actual):
        if expected_tool != actual_tool:
            break
        matching_prefix += 1
    score = 1.0 if passed else matching_prefix / max(1, len(expected))
    return (
        DimensionResult(
            **{"pass": passed},
            score=score,
            message="工具调用顺序符合预期" if passed else "工具调用顺序不符合预期",
            details={"expected": expected, "actual": actual},
        ),
        [] if passed else ["INVALID_TOOL_ORDER"],
    )
