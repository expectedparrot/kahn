from __future__ import annotations

from itertools import combinations

from .models import Force, ScenarioMeta

RATING_SCORE = {"robust": 1.0, "acceptable": 0.5, "fragile": 0.0}


def compute_robustness_score(ratings: list[str]) -> float:
    if not ratings:
        return 0.0
    return round(sum(RATING_SCORE[r] for r in ratings) / len(ratings), 2)


def compute_consistency_score(
    scenario: ScenarioMeta,
    narrative: str,
    forces: list[Force],
) -> tuple[float, str]:
    notes: list[str] = []
    score = 1.0
    text = narrative.lower()

    for cu_id, pole in scenario.axis.items():
        counterpart = "pole_b" if pole == "pole_a" else "pole_a"
        if counterpart in text and pole not in text:
            score -= 0.2
            notes.append(f"Narrative references {counterpart} language for {cu_id}.")

    trend_names = {force.id: force.name.lower() for force in forces}
    missing = [
        force_id
        for force_id in scenario.predetermined_element_ids
        if trend_names.get(force_id) and trend_names[force_id] not in text
    ]
    if missing:
        score -= min(0.3, 0.1 * len(missing))
        notes.append(f"Predetermined forces not reflected in narrative: {', '.join(missing)}.")

    word_count = len(narrative.split())
    if word_count < 100:
        score -= 0.15
        notes.append("Narrative is under the 100 word guideline.")

    return max(0.0, round(score, 2)), " ".join(notes) or "No obvious contradictions detected."


def pairwise_similarity(scenarios: list[ScenarioMeta]) -> list[tuple[str, str, str]]:
    results: list[tuple[str, str, str]] = []
    for left, right in combinations(scenarios, 2):
        overlap = sum(1 for key in left.axis if left.axis.get(key) == right.axis.get(key))
        label = "high" if overlap == len(left.axis) else "medium" if overlap else "low"
        results.append((left.id, right.id, label))
    return results
