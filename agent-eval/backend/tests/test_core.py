from pathlib import Path

import pytest

from backend.agents.datapilot.tools import DataPilotTools, ToolError
from backend.data import DATABASE_PATH, ensure_database
from backend.datasets import load_cases
from backend.evaluators import evaluate_run
from backend.schemas import AgentRun, StructuredResult, TraceStep


METRICS_PATH = Path(__file__).resolve().parents[1] / "data" / "metrics.json"


@pytest.mark.parametrize("http_error", [True, False])
def test_model_errors_do_not_expose_provider_details(monkeypatch, http_error):
    from io import BytesIO
    from urllib.error import HTTPError, URLError

    from backend.agents.datapilot import llm_client
    from backend.config import Settings

    sensitive_detail = "private-credential-and-request-content"
    failure = (
        HTTPError("https://example.invalid", 401, "Unauthorized", {},
                  BytesIO(sensitive_detail.encode()))
        if http_error else URLError(sensitive_detail)
    )

    def fail_request(*args, **kwargs):
        raise failure

    monkeypatch.setattr(llm_client, "urlopen", fail_request)
    client = llm_client.OpenAICompatibleClient(
        Settings("test-key", "https://example.invalid", "test-model", 1)
    )
    with pytest.raises(llm_client.LLMError) as caught:
        client.complete([], [])
    assert sensitive_detail not in str(caught.value)
    if http_error:
        assert "401" in str(caught.value)


def setup_module() -> None:
    ensure_database()


def test_mock_data_ground_truth() -> None:
    summary = ensure_database()
    assert summary["row_count"] == 600
    assert summary["september_gmv"] == 120000
    assert summary["september_orders"] == 200


def test_tools_return_real_data() -> None:
    tools = DataPilotTools(DATABASE_PATH, METRICS_PATH)
    assert tools.get_metric_definition("GMV")["definition"] == "SUM(pay_amount)"
    assert "pay_time" in tools.get_table_schema("orders")["columns"]
    result = tools.run_sql(
        "SELECT SUM(pay_amount) AS gmv FROM orders "
        "WHERE pay_status = 'SUCCESS' AND pay_time >= '2026-09-01' AND pay_time < '2026-10-01'"
    )
    assert result["rows"] == [[120000.0]]


def test_run_sql_rejects_writes() -> None:
    tools = DataPilotTools(DATABASE_PATH, METRICS_PATH)
    try:
        tools.run_sql("DELETE FROM orders")
        assert False, "DELETE should be rejected"
    except ToolError:
        pass


def test_process_failure_when_answer_is_correct() -> None:
    case = load_cases()[0]
    run = AgentRun(
        run_id="run_test",
        agent_version="v0.9-direct",
        query=case.query,
        status="completed",
        trace=[
            TraceStep(step=1, tool="get_table_schema", input={"table_name": "orders"}, output={}, status="success", latency_ms=1),
            TraceStep(step=2, tool="run_sql", input={"sql": "SELECT 1"}, output={"rows": [[120000]]}, status="success", latency_ms=1),
        ],
        final_answer="2026 年 9 月 GMV 为 120000 元。",
        structured_result=StructuredResult(metric="GMV", value=120000, unit="元", year=2026, month=9),
        total_latency_ms=2,
    )
    evaluation = evaluate_run(case, run)
    assert evaluation.dimensions["result"].passed is True
    assert evaluation.dimensions["tool_selection"].passed is False
    assert evaluation.dimensions["trajectory"].passed is False
    assert evaluation.overall_pass is False
    assert "MISSING_REQUIRED_TOOL" in evaluation.failure_types
