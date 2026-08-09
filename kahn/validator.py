from __future__ import annotations

from .models import ScenarioMeta
from .store import KahnError, ProjectStore


def validate_project(store: ProjectStore) -> list[str]:
    errors: list[str] = []
    forces = {force.id for force in store.list_forces()}
    scenarios = {scenario.id for scenario in store.list_scenarios()}
    options = {option.id for option in store.list_options()}

    for cu in store.list_critical_uncertainties():
        if cu.source_force_id not in forces:
            errors.append(f"{cu.id} references missing force {cu.source_force_id}")

    for scenario in store.list_scenarios():
        _validate_scenario_refs(scenario, forces, errors)
        signals = store.get_scenario_signals(scenario.id)
        if signals.scenario_id != scenario.id:
            errors.append(f"{scenario.id} signals file has mismatched scenario_id {signals.scenario_id}")
        if len(signals.signals) < 3:
            errors.append(f"{scenario.id} requires at least 3 signals; found {len(signals.signals)}")

    for option in store.list_options():
        perf_path = store.option_dir(option.id) / "performance.json"
        if perf_path.exists():
            performance = store.get_option_performance(option.id)
            if performance.option_id not in options:
                errors.append(f"{option.id} performance references missing option {performance.option_id}")
            for scenario_id in performance.evaluations:
                if scenario_id not in scenarios:
                    errors.append(f"{option.id} performance references missing scenario {scenario_id}")

    return errors


def _validate_scenario_refs(scenario: ScenarioMeta, forces: set[str], errors: list[str]) -> None:
    for force_id in scenario.predetermined_element_ids:
        if force_id not in forces:
            errors.append(f"{scenario.id} references missing predetermined element {force_id}")


def assert_valid_project(store: ProjectStore) -> None:
    errors = validate_project(store)
    if errors:
        raise KahnError("INTEGRITY_ERROR", "Project validation failed.", context="; ".join(errors))
