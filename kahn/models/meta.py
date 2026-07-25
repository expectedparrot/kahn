from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Phase = Literal[
    "forces",
    "uncertainty_selection",
    "scenario_construction",
    "option_evaluation",
    "complete",
]


class ProjectMeta(BaseModel):
    id: str
    focal_question: str
    domain: str
    horizon: str
    created_at: datetime
    updated_at: datetime
    phase: Phase = "forces"
    phase_locks: list[Phase] = Field(default_factory=list)
    notes: str | None = None
