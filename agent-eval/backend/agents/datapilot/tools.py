from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any


class ToolError(ValueError):
    pass


class DataPilotTools:
    def __init__(self, database_path: Path, metrics_path: Path) -> None:
        self.database_path = database_path.resolve()
        self.metrics_path = metrics_path.resolve()

    def get_metric_definition(self, metric_name: str) -> dict[str, Any]:
        metrics = json.loads(self.metrics_path.read_text(encoding="utf-8"))
        normalized = metric_name.upper() if metric_name.upper() == "GMV" else metric_name
        if normalized not in metrics:
            raise ToolError(f"不支持的指标：{metric_name}")
        return {"metric_name": normalized, **metrics[normalized]}

    def get_table_schema(self, table_name: str) -> dict[str, Any]:
        if table_name != "orders":
            raise ToolError(f"不允许访问数据表：{table_name}")
        with self._connect_readonly() as connection:
            rows = connection.execute("PRAGMA table_info(orders)").fetchall()
        return {
            "table_name": table_name,
            "columns": [row[1] for row in rows],
        }

    def run_sql(self, sql: str) -> dict[str, Any]:
        normalized = sql.strip().rstrip(";").strip()
        self._validate_sql(normalized)
        with self._connect_readonly() as connection:
            cursor = connection.execute(normalized)
            rows = cursor.fetchmany(101)
            if len(rows) > 100:
                raise ToolError("查询最多返回 100 行")
            columns = [description[0] for description in cursor.description or []]
        return {
            "columns": columns,
            "rows": [list(row) for row in rows],
            "row_count": len(rows),
        }

    def _connect_readonly(self) -> sqlite3.Connection:
        uri = self.database_path.as_uri() + "?mode=ro"
        return sqlite3.connect(uri, uri=True)

    @staticmethod
    def _validate_sql(sql: str) -> None:
        lowered = re.sub(r"\s+", " ", sql.lower())
        if not lowered.startswith("select "):
            raise ToolError("run_sql 只允许执行 SELECT 查询")
        if ";" in sql:
            raise ToolError("run_sql 不允许执行多条 SQL")
        blocked = (
            " insert ", " update ", " delete ", " drop ", " alter ",
            " create ", " attach ", " detach ", " pragma ", " sqlite_",
            "--", "/*", "*/",
        )
        padded = f" {lowered} "
        if any(token in padded for token in blocked):
            raise ToolError("SQL 包含不允许的语句或对象")
        tables = re.findall(r"\b(?:from|join)\s+([a-zA-Z_][\w]*)", lowered)
        if not tables or any(table != "orders" for table in tables):
            raise ToolError("SQL 只能查询 orders 表")
