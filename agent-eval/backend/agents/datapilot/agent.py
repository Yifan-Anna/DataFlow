from __future__ import annotations

import json
import re
from datetime import datetime
from time import perf_counter
from typing import Any, Callable
from uuid import uuid4

from backend.schemas import AgentRun, StructuredResult, TraceStep

from .llm_client import OpenAICompatibleClient
from .prompts import LEGACY_SYSTEM_PROMPT, SYSTEM_PROMPT
from .tools import DataPilotTools


class DataPilot:
    SUPPORTED_VERSIONS = ("v1.0", "v0.9-direct")
    MAX_LLM_ROUNDS = 8

    def __init__(self, tools: DataPilotTools, client: OpenAICompatibleClient) -> None:
        self.tools = tools
        self.client = client
        self.tool_functions: dict[str, Callable[..., dict[str, Any]]] = {
            "get_metric_definition": self.tools.get_metric_definition,
            "get_table_schema": self.tools.get_table_schema,
            "run_sql": self.tools.run_sql,
        }

    def run(self, query: str, agent_version: str = "v1.0") -> AgentRun:
        started = perf_counter()
        trace: list[TraceStep] = []
        run_id = f"run_{datetime.now():%Y%m%d}_{uuid4().hex[:8]}"

        try:
            if agent_version not in self.SUPPORTED_VERSIONS:
                raise ValueError(f"不支持的 Agent 版本：{agent_version}")
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": SYSTEM_PROMPT if agent_version == "v1.0" else LEGACY_SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ]
            seen_calls: set[str] = set()
            final_content = ""

            for _ in range(self.MAX_LLM_ROUNDS):
                message = self.client.complete(messages, self._tool_definitions())
                tool_calls = message.get("tool_calls") or []
                if not tool_calls:
                    final_content = message.get("content") or ""
                    break

                messages.append({
                    "role": "assistant",
                    "content": message.get("content"),
                    "tool_calls": tool_calls,
                })
                for tool_call in tool_calls:
                    function = tool_call.get("function") or {}
                    tool_name = function.get("name", "")
                    raw_arguments = function.get("arguments") or "{}"
                    signature = f"{tool_name}:{raw_arguments}"
                    if signature in seen_calls:
                        raise RuntimeError(f"检测到重复工具调用，已停止：{tool_name}")
                    seen_calls.add(signature)
                    try:
                        tool_input = json.loads(raw_arguments)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"工具参数不是合法 JSON：{tool_name}") from exc
                    output = self._call_tool(trace, tool_name, tool_input)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id"),
                        "content": json.dumps(output, ensure_ascii=False),
                    })
            else:
                raise RuntimeError(f"模型超过 {self.MAX_LLM_ROUNDS} 轮仍未完成，已主动停止")

            parsed = self._parse_final_content(final_content, query, trace)
            final_answer = str(parsed.pop("final_answer", ""))
            structured = StructuredResult.model_validate(parsed)
            if not final_answer:
                final_answer = self._format_answer(structured)
            status = "completed"
            error = None
        except Exception as exc:
            structured = None
            final_answer = f"无法完成查询：{exc}"
            status = "failed"
            error = str(exc)

        return AgentRun(
            run_id=run_id,
            agent_version=agent_version,
            query=query,
            status=status,
            trace=trace,
            final_answer=final_answer,
            structured_result=structured,
            total_latency_ms=max(1, round((perf_counter() - started) * 1000)),
            error=error,
        )

    def _call_tool(self, trace: list[TraceStep], tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        if tool_name not in self.tool_functions:
            raise ValueError(f"模型请求了未知工具：{tool_name}")
        started = perf_counter()
        try:
            output = self.tool_functions[tool_name](**tool_input)
            trace.append(TraceStep(
                step=len(trace) + 1,
                tool=tool_name,
                input=tool_input,
                output=output,
                status="success",
                latency_ms=max(1, round((perf_counter() - started) * 1000)),
            ))
            return output
        except Exception as exc:
            trace.append(TraceStep(
                step=len(trace) + 1,
                tool=tool_name,
                input=tool_input,
                output=None,
                status="failed",
                latency_ms=max(1, round((perf_counter() - started) * 1000)),
                error=str(exc),
            ))
            raise

    @staticmethod
    def _parse_final_content(content: str, query: str, trace: list[TraceStep]) -> dict[str, Any]:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        metric = "GMV" if re.search(r"gmv", query, re.IGNORECASE) else "订单量"
        date_match = re.search(r"(20\d{2})\s*年\s*(1[0-2]|0?[1-9])\s*月", query)
        sql_outputs = [step.output for step in trace if step.tool == "run_sql" and step.status == "success" and step.output]
        if not date_match or not sql_outputs:
            raise ValueError("模型未返回可解析的结构化结果")
        values = [output["rows"][0][0] for output in sql_outputs if output.get("rows")]
        if not values:
            raise ValueError("SQL 没有返回结果")
        previous_value = values[1] if len(values) > 1 else None
        mom_rate = None if previous_value in (None, 0) else round((values[0] - previous_value) / previous_value, 4)
        return {
            "final_answer": content.strip(),
            "metric": metric,
            "value": values[0],
            "unit": "元" if metric == "GMV" else "单",
            "year": int(date_match.group(1)),
            "month": int(date_match.group(2)),
            "previous_value": previous_value,
            "mom_rate": mom_rate,
        }

    @staticmethod
    def _format_answer(result: StructuredResult) -> str:
        base = f"{result.year} 年 {result.month} 月{result.metric}为 {result.value:,} {result.unit}"
        if result.previous_value is None:
            return base + "。"
        if result.mom_rate is None:
            return f"{base}；上月为 {result.previous_value:,} {result.unit}，无法计算环比。"
        direction = "增长" if result.mom_rate >= 0 else "下降"
        return f"{base}；上月为 {result.previous_value:,} {result.unit}，环比{direction} {abs(result.mom_rate):.2%}。"

    @staticmethod
    def _tool_definitions() -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_metric_definition",
                    "description": "获取 GMV 或订单量的业务定义、过滤条件和来源表。",
                    "parameters": {
                        "type": "object",
                        "properties": {"metric_name": {"type": "string", "enum": ["GMV", "订单量"]}},
                        "required": ["metric_name"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_table_schema",
                    "description": "读取 orders 表结构，避免猜测字段。",
                    "parameters": {
                        "type": "object",
                        "properties": {"table_name": {"type": "string", "enum": ["orders"]}},
                        "required": ["table_name"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_sql",
                    "description": "在只读 SQLite 数据库中执行单条 SELECT 查询。",
                    "parameters": {
                        "type": "object",
                        "properties": {"sql": {"type": "string"}},
                        "required": ["sql"],
                        "additionalProperties": False,
                    },
                },
            },
        ]
