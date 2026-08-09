from __future__ import annotations

import json
from datetime import datetime, timezone

from typer.testing import CliRunner

from kahn.cli import app
from kahn.models import OptionMeta, ProjectMeta, ScenarioMeta, ScenarioSignals
from kahn.store import ProjectStore
from kahn.validator import validate_project

runner = CliRunner()


def scenario_project(tmp_path):
    project = tmp_path / "project"
    now = datetime.now(timezone.utc)
    store = ProjectStore(project)
    store.init_project(ProjectMeta(id="signals", focal_question="Q?", domain="test", horizon="2030", created_at=now, updated_at=now, phase="scenario_construction", phase_locks=["forces", "uncertainty_selection"]))
    store.save_scenario_meta(ScenarioMeta(id="sc001", name="Future", tagline="Tag", axis={}, created_at=now, updated_at=now))
    store.save_scenario_signals(ScenarioSignals(scenario_id="sc001"))
    store.save_scenario_narrative("sc001", "A sufficiently detailed narrative. " * 40)
    return project, store


def invoke(project, *args):
    return runner.invoke(app, [*args, "--project-dir", str(project)])


def test_repeated_add_preserves_signals_and_validation_requires_three(tmp_path) -> None:
    project, store = scenario_project(tmp_path)
    for index in range(3):
        result = invoke(project, "scenario", "signals", "add", "sc001", "--description", f"Signal {index}", "--observable-in", f"Source {index}")
        assert result.exit_code == 0, result.stdout
    stored = store.get_scenario_signals("sc001")
    assert [item.description for item in stored.signals] == ["Signal 0", "Signal 1", "Signal 2"]
    assert not any("requires at least 3 signals" in error for error in validate_project(store))


def test_set_is_atomic_and_replacement_requires_acknowledgement(tmp_path) -> None:
    project, store = scenario_project(tmp_path)
    first = invoke(project, "scenario", "signals", "set", "sc001", "--signal", "One", "--observable-in", "A", "--signal", "Two", "--observable-in", "B", "--signal", "Three", "--observable-in", "C")
    assert first.exit_code == 0
    refused = invoke(project, "scenario", "signals", "set", "sc001", "--signal", "Replacement", "--observable-in", "D")
    assert refused.exit_code == 1
    assert json.loads(refused.stdout)["errors"][0]["code"] == "REPLACE_CONFIRMATION_REQUIRED"
    assert len(store.get_scenario_signals("sc001").signals) == 3
    replaced = invoke(project, "scenario", "signals", "set", "sc001", "--replace", "--signal", "Replacement", "--observable-in", "D")
    assert replaced.exit_code == 0
    assert [item.description for item in store.get_scenario_signals("sc001").signals] == ["Replacement"]
    assert any("requires at least 3 signals" in error for error in validate_project(store))


def test_locked_signal_add_fails_without_losing_existing_data(tmp_path) -> None:
    project, store = scenario_project(tmp_path)
    invoke(project, "scenario", "signals", "add", "sc001", "--description", "Existing", "--observable-in", "Source")
    meta = store.read_meta()
    meta.phase_locks.append("scenario_construction")
    store.write_meta(meta)
    result = invoke(project, "scenario", "signals", "add", "sc001", "--description", "Late", "--observable-in", "Source")
    assert result.exit_code == 1
    assert json.loads(result.stdout)["errors"][0]["code"] == "PHASE_LOCKED"
    assert [item.description for item in store.get_scenario_signals("sc001").signals] == ["Existing"]


def test_invalid_scenario_rating_is_a_structured_error(tmp_path) -> None:
    project, store = scenario_project(tmp_path)
    meta = store.read_meta()
    meta.phase_locks.append("scenario_construction")
    store.write_meta(meta)
    store.save_option_meta(OptionMeta(id="op001", name="Pilot", description="Pilot first", created_at=datetime.now(timezone.utc)))
    result = invoke(project, "option", "evaluate", "op001", "--scenario", "sc001", "--rating", "great", "--rationale", "Looks good")
    payload = json.loads(result.stdout)
    assert result.exit_code == 1
    assert payload["errors"][0]["code"] == "INVALID_ENUM_VALUE"
    assert payload["errors"][0]["context"]["accepted"] == ["robust", "acceptable", "fragile"]
