from __future__ import annotations

from pathlib import Path

from .models import Force, OptionPerformance, ScenarioEvaluation
from .scorer import compute_robustness_score
from .store import KahnError, ProjectStore, now_utc

VALID_DOMAINS = {"political", "economic", "social", "technological", "environmental", "legal"}
VALID_MAGNITUDES = {"low", "medium", "high"}
VALID_RATINGS = {"robust", "acceptable", "fragile"}


def load_results(path: Path):
    try:
        from edsl import Results
        return Results.git.load(path)
    except ImportError as exc:
        raise KahnError("DEPENDENCY_ERROR", "EDSL is required to load .ep Results.") from exc
    except Exception as exc:
        raise KahnError("VALIDATION_FAILED", "Unable to load EDSL Results.", context=f"{path}: {exc}") from exc


def _require_questions(results, required: set[str]) -> None:
    present = set(results.survey.question_names)
    missing = sorted(required - present)
    if missing:
        raise KahnError("VALIDATION_FAILED", "Results are missing required questions.", context=", ".join(missing))


def _project_id(results) -> str:
    rows = results.select("scenario.project_id").to_dicts(remove_prefix=True)
    return str(rows[0].get("project_id", "")) if rows else ""


def validate_project(results, store: ProjectStore) -> None:
    actual = _project_id(results)
    expected = store.read_meta().id
    if actual != expected:
        raise KahnError(
            "CONFLICT",
            "Results belong to a different Kahn project.",
            context=f"expected {expected}, got {actual or '(missing)'}",
        )


def _normalize_domain(value: str) -> str:
    aliases = {"technology": "technological", "environment": "environmental", "politics": "political"}
    normalized = aliases.get(value.strip().lower(), value.strip().lower())
    return normalized if normalized in VALID_DOMAINS else "technological"


def _normalize_magnitude(value: str, default: str) -> str:
    normalized = value.strip().lower()
    return normalized if normalized in VALID_MAGNITUDES else default


def ingest_forces(store: ProjectStore, results) -> tuple[list[Force], list[str]]:
    _require_questions(results, {"trends", "uncertainties"})
    validate_project(results, store)
    raw = results.select("answer.trends", "answer.uncertainties").to_dicts(remove_prefix=True)
    existing_names = {force.name.strip().lower() for force in store.list_forces()}
    created: list[Force] = []
    warnings: list[str] = []
    with store.locked():
        for force_type, question_name in (("trend", "trends"), ("uncertainty", "uncertainties")):
            values = raw[0].get(question_name, []) if raw else []
            if not isinstance(values, list):
                values = [values]
            for value in values:
                parts = [part.strip() for part in str(value).split("|")]
                if not parts or not parts[0]:
                    continue
                name = parts[0]
                if name.lower() in existing_names:
                    warnings.append(f"Skipped duplicate force: {name}")
                    continue
                while len(parts) < 6:
                    parts.append("")
                force = Force(
                    id=store.next_id("f", [*store.list_force_paths_stems(), *(item.id for item in created)]),
                    name=name,
                    domain=_normalize_domain(parts[1]),
                    type=force_type,
                    impact_magnitude=_normalize_magnitude(parts[2], "high"),
                    predictability=_normalize_magnitude(parts[3], "high" if force_type == "trend" else "low"),
                    direction=parts[4] or ("uncertain" if force_type == "uncertainty" else "continuing"),
                    notes=parts[5] or None,
                    created_at=now_utc(),
                )
                store.save_force(force)
                created.append(force)
                existing_names.add(name.lower())
    return created, warnings


def ingest_narrative(store: ProjectStore, results, scenario_id: str) -> tuple[int, list[str]]:
    _require_questions(results, {"narrative"})
    validate_project(results, store)
    selection = ["scenario.scenario_id", "answer.narrative"]
    if "force_evidence" in results.survey.question_names:
        selection.append("answer.force_evidence")
    rows = results.select(*selection).to_dicts(remove_prefix=True)
    if not rows:
        raise KahnError("VALIDATION_FAILED", "Results contain no narrative answer.")
    result_scenario_id = str(rows[0].get("scenario_id", ""))
    if result_scenario_id != scenario_id:
        raise KahnError(
            "CONFLICT",
            "Results belong to a different scenario.",
            context=f"expected {scenario_id}, got {result_scenario_id or '(missing)'}",
        )
    scenario = store.get_scenario_meta(scenario_id)
    narrative = str(rows[0].get("narrative", "")).strip()
    if not narrative:
        raise KahnError("VALIDATION_FAILED", "Narrative answer is empty.")
    store.save_scenario_narrative(scenario_id, narrative)
    evidence = rows[0].get("force_evidence", {})
    if isinstance(evidence, dict):
        valid_evidence = {str(key): str(value) for key, value in evidence.items() if key in scenario.predetermined_element_ids and str(value).strip()}
        if valid_evidence:
            data = scenario.model_dump()
            data["predetermined_evidence"] = valid_evidence
            from .models import ScenarioMeta

            store.save_scenario_meta(ScenarioMeta.model_validate(data))
    warnings = ["Narrative is under 100 words."] if len(narrative.split()) < 100 else []
    return len(narrative.split()), warnings


def ingest_option_evaluations(store: ProjectStore, results) -> list[OptionPerformance]:
    options = store.list_options()
    scenarios = store.list_scenarios()
    required = {f"eval_{option.id}_{scenario.id}" for option in options for scenario in scenarios}
    _require_questions(results, required)
    validate_project(results, store)
    raw = results.select(*[f"answer.{name}" for name in sorted(required)]).to_dicts(remove_prefix=True)
    row = raw[0] if raw else {}
    created: list[OptionPerformance] = []
    for option in options:
        evaluations = {}
        for scenario in scenarios:
            answer = row.get(f"eval_{option.id}_{scenario.id}", {})
            if not isinstance(answer, dict):
                raise KahnError("VALIDATION_FAILED", "Evaluation answer is not structured.", context=f"{option.id}/{scenario.id}")
            rating = str(answer.get("rating", "")).strip().lower()
            rationale = str(answer.get("rationale", "")).strip()
            if rating not in VALID_RATINGS:
                raise KahnError("VALIDATION_FAILED", "Invalid option rating.", context=f"{option.id}/{scenario.id}: {rating}")
            if not rationale:
                raise KahnError("VALIDATION_FAILED", "Evaluation rationale is empty.", context=f"{option.id}/{scenario.id}")
            evaluations[scenario.id] = ScenarioEvaluation(rating=rating, rationale=rationale)
        performance = OptionPerformance(
            option_id=option.id,
            evaluations=evaluations,
            robustness_score=compute_robustness_score([item.rating for item in evaluations.values()]),
            evaluated_at=now_utc(),
        )
        created.append(performance)
    with store.locked():
        for performance in created:
            store.save_option_performance(performance)
    return created
