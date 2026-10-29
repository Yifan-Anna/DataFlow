from __future__ import annotations

import json
from pathlib import Path

from backend.schemas import Case


DATASET_PATH = Path(__file__).resolve().parent / "benchmark.json"


def load_cases() -> list[Case]:
    raw_cases = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    return [Case.model_validate(item) for item in raw_cases]


__all__ = ["load_cases"]
