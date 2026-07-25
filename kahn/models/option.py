from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class OptionMeta(BaseModel):
    id: str
    name: str
    description: str
    hedging_value: bool = False
    created_at: datetime
    notes: str | None = None


class ScenarioEvaluation(BaseModel):
    rating: Literal["robust", "acceptable", "fragile"]
    rationale: str


class OptionPerformance(BaseModel):
    option_id: str
    evaluations: dict[str, ScenarioEvaluation] = Field(default_factory=dict)
    robustness_score: float = 0.0
    evaluated_at: datetime
