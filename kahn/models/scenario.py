from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ScenarioMeta(BaseModel):
    id: str
    name: str
    tagline: str
    axis: dict[str, Literal["pole_a", "pole_b"]]
    predetermined_element_ids: list[str] = Field(default_factory=list)
    internal_consistency_score: float = 0.0
    consistency_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ScenarioSignal(BaseModel):
    id: str
    description: str
    observable_in: str


class ScenarioSignals(BaseModel):
    scenario_id: str
    signals: list[ScenarioSignal] = Field(default_factory=list)
