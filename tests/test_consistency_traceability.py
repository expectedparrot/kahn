from __future__ import annotations

from datetime import datetime, timezone

from kahn.models import Force, ScenarioMeta
from kahn.scorer import compute_consistency_score


def test_explicit_evidence_mapping_accepts_paraphrased_trend() -> None:
    now = datetime.now(timezone.utc)
    force = Force(id="f001", name="Falling storage costs", domain="technological", type="trend", direction="down", impact_magnitude="high", predictability="high", created_at=now)
    scenario = ScenarioMeta(id="sc001", name="Future", tagline="Tag", axis={}, predetermined_element_ids=["f001"], predetermined_evidence={"f001": "Batteries become dramatically cheaper."}, created_at=now, updated_at=now)
    narrative = "Batteries become dramatically cheaper, changing the economics of the market. " * 20
    score, notes = compute_consistency_score(scenario, narrative, [force])
    assert score == 1.0
    assert "Explicit evidence mappings accepted for: f001" in notes


def test_unmapped_omission_explains_lexical_matching_basis() -> None:
    now = datetime.now(timezone.utc)
    force = Force(id="f001", name="Falling storage costs", domain="technological", type="trend", direction="down", impact_magnitude="high", predictability="high", created_at=now)
    scenario = ScenarioMeta(id="sc001", name="Future", tagline="Tag", axis={}, predetermined_element_ids=["f001"], created_at=now, updated_at=now)
    score, notes = compute_consistency_score(scenario, "A different market development unfolds. " * 25, [force])
    assert score < 1.0
    assert "lack explicit evidence and exact-name lexical matches" in notes
