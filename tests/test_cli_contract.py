from __future__ import annotations

import json

import pytest
from typer.main import get_command
from typer.testing import CliRunner

from kahn.cli import app

runner = CliRunner()
ENVELOPE_KEYS = {"schema_version", "command", "status", "argv", "data", "warnings", "errors", "next_steps"}


@pytest.mark.parametrize(
    "args",
    [
        ["guide"],
        ["docs", "list"],
        ["next"],
        ["status"],
        ["force", "list"],
    ],
)
def test_commands_emit_one_versioned_envelope(args, tmp_path) -> None:
    result = runner.invoke(app, [*args, "--project-dir", str(tmp_path / "project")] if args[0] not in {"guide", "docs"} else args)
    payload = json.loads(result.stdout)
    assert set(payload) == ENVELOPE_KEYS
    assert payload["schema_version"] == "2.0"
    assert payload["status"] in {"ok", "error"}
    assert isinstance(payload["argv"], list)


def test_error_envelope_is_structured_and_nonzero(tmp_path) -> None:
    result = runner.invoke(app, ["status", "--project-dir", str(tmp_path / "missing")])
    payload = json.loads(result.stdout)
    assert result.exit_code == 1
    assert payload["status"] == "error"
    assert payload["errors"][0]["code"] == "ID_NOT_FOUND"


@pytest.mark.parametrize(
    ("flag", "value", "field"),
    [
        ("--domain", "Legal/Political", "domain"),
        ("--type", "maybe", "type"),
        ("--impact", "med", "impact_magnitude"),
        ("--predictability", "certain", "predictability"),
    ],
)
def test_invalid_force_enums_return_structured_envelopes(tmp_path, flag, value, field) -> None:
    project = tmp_path / "project"
    initialized = runner.invoke(app, ["init", "--question", "Q?", "--domain", "test", "--horizon", "2030", "--project-dir", str(project)])
    assert initialized.exit_code == 0
    args = ["force", "add", "--name", "Force", "--domain", "legal", "--type", "trend", "--impact", "high", "--predictability", "high", "--direction", "steady", "--project-dir", str(project)]
    args[args.index(flag) + 1] = value
    result = runner.invoke(app, args)
    payload = json.loads(result.stdout)
    assert result.exit_code == 1
    assert payload["errors"][0]["code"] == "INVALID_ENUM_VALUE"
    assert payload["errors"][0]["context"]["field"] == field
    assert value == payload["errors"][0]["context"]["value"]
    assert payload["errors"][0]["context"]["accepted"]


def test_human_mode_is_not_json() -> None:
    result = runner.invoke(app, ["guide", "--human"])
    assert result.exit_code == 0
    with pytest.raises(json.JSONDecodeError):
        json.loads(result.stdout)
    assert "Agent workflow" in result.stdout


def test_every_leaf_command_offers_human_output() -> None:
    root = get_command(app)
    leaves: list[tuple[str, ...]] = []

    def walk(command, prefix=()):
        if hasattr(command, "commands"):
            for name, child in command.commands.items():
                walk(child, (*prefix, name))
        else:
            leaves.append(prefix)

    walk(root)
    assert leaves
    for prefix in leaves:
        result = runner.invoke(app, [*prefix, "--help"])
        assert result.exit_code == 0, " ".join(prefix)
        assert "--human" in result.stdout, " ".join(prefix)


def test_next_actions_are_absolute_and_isolated_for_nested_projects_with_spaces(tmp_path) -> None:
    projects = [tmp_path / "client one" / "scenario plan", tmp_path / "client two" / "scenario plan"]
    actions = []
    for project in projects:
        result = runner.invoke(app, ["next", "--project-dir", str(project)])
        payload = json.loads(result.stdout)
        action = payload["data"]["action"]
        assert action["project_dir"] == str(project.resolve())
        assert action["cwd"] == str(tmp_path.resolve())
        assert action["argv"][-2:] == ["--project-dir", str(project.resolve())]
        assert {"question", "domain", "horizon"} == set(action["input_schema"])
        actions.append(action)
    assert actions[0]["project_dir"] != actions[1]["project_dir"]
