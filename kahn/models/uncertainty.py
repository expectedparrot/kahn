from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CriticalUncertainty(BaseModel):
    id: str
    source_force_id: str
    name: str
    description: str
    pole_a: str
    pole_b: str
    independence_note: str
    created_at: datetime
