from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ForceDomain = Literal[
    "political",
    "economic",
    "social",
    "technological",
    "environmental",
    "legal",
]
ForceType = Literal["trend", "uncertainty"]
Magnitude = Literal["low", "medium", "high"]


class Force(BaseModel):
    id: str
    name: str
    domain: ForceDomain
    type: ForceType
    direction: str
    impact_magnitude: Magnitude
    predictability: Magnitude
    created_at: datetime
    notes: str | None = None
