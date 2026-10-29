from collections import Counter

from backend.schemas import AgentRun, Case, DimensionResult


def evaluate_tool_selection(case: Case, run: AgentRun) -> tuple[DimensionResult, list[str]]:
    expected = Counter(case.expected.tools)
    actual_tools = [step.tool for step in run.trace if step.status == "success"]
    actual = Counter(actual_tools)
    missing = list((expected - actual).elements())
    passed = not missing
    return (
        DimensionResult(
            **{"pass": passed},
            score=1.0 if passed else max(0.0, 1 - len(missing) / max(1, sum(expected.values()))),
            message="必需工具均已调用" if passed else f"缺少必需工具：{', '.join(missing)}",
            details={"expected": case.expected.tools, "actual": actual_tools, "missing": missing},
        ),
        [] if passed else ["MISSING_REQUIRED_TOOL"],
    )
