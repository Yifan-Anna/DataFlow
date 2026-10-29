from uuid import uuid4

from backend.schemas import AgentRun, Case, EvaluationResult

from .result_evaluator import evaluate_result
from .tool_evaluator import evaluate_tool_selection
from .trajectory_evaluator import evaluate_trajectory


def evaluate_run(case: Case, run: AgentRun) -> EvaluationResult:
    dimensions = {}
    failure_types: list[str] = []
    for name, evaluator in (
        ("result", evaluate_result),
        ("tool_selection", evaluate_tool_selection),
        ("trajectory", evaluate_trajectory),
    ):
        result, failures = evaluator(case, run)
        dimensions[name] = result
        failure_types.extend(failures)
    score = round(sum(item.score for item in dimensions.values()) / len(dimensions), 4)
    return EvaluationResult(
        evaluation_id=f"eval_{uuid4().hex[:10]}",
        run_id=run.run_id,
        case_id=case.case_id,
        overall_pass=all(item.passed for item in dimensions.values()),
        score=score,
        dimensions=dimensions,
        failure_types=list(dict.fromkeys(failure_types)),
    )
