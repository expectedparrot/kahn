from __future__ import annotations

import json

from typer.testing import CliRunner

from kahn.cli import app

runner = CliRunner()


def run(project, *args):
    result = runner.invoke(app, [*args, "--project-dir", str(project)])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok", payload
    return payload


def test_complete_agent_workflow_reaches_report(tmp_path) -> None:
    project = tmp_path / "market-entry"
    assert run(project, "next")["data"]["stage"] == "init"
    run(project, "init", "--question", "How should we enter?", "--domain", "energy", "--horizon", "2030")
    run(project, "force", "add", "--name", "Storage costs", "--domain", "technological", "--type", "trend", "--impact", "high", "--predictability", "high", "--direction", "falling")
    run(project, "force", "add", "--name", "Regulation", "--domain", "legal", "--type", "uncertainty", "--impact", "high", "--predictability", "low", "--direction", "uncertain")
    run(project, "force", "add", "--name", "Adoption", "--domain", "social", "--type", "uncertainty", "--impact", "high", "--predictability", "low", "--direction", "uncertain")
    assert run(project, "next")["data"]["action"]["argv"][1:4] == ["snapshot", "save", "forces-reviewed"]
    run(project, "snapshot", "save", "forces-reviewed")
    assert run(project, "next")["data"]["action"]["argv"][1:3] == ["phase", "advance"]
    run(project, "phase", "advance")
    run(project, "uncertainty", "select", "f002", "f003")
    run(project, "uncertainty", "set-poles", "cu001", "--pole-a", "permissive", "--pole-b", "restrictive")
    run(project, "uncertainty", "set-poles", "cu002", "--pole-a", "rapid", "--pole-b", "slow")
    assert run(project, "next")["data"]["action"]["argv"][1:3] == ["uncertainty", "check-independence"]
    run(project, "uncertainty", "check-independence")
    run(project, "snapshot", "save", "uncertainty_selection-reviewed")
    run(project, "phase", "advance")
    run(project, "scenario", "build")
    for index in range(1, 5):
        scenario = f"sc{index:03d}"
        run(project, "scenario", "name", scenario, "--name", f"Future {index}", "--tagline", f"Plausible future {index}")
        run(project, "scenario", "narrative", "set", scenario, "--text", (f"Future {index} unfolds with concrete strategic consequences. " * 45))
        run(
            project,
            "scenario", "signals", "set", scenario,
            "--signal", "A measurable policy shift", "--observable-in", "Public policy data",
            "--signal", "A measurable market shift", "--observable-in", "Market data",
            "--signal", "A measurable customer shift", "--observable-in", "Customer research",
        )
    run(project, "snapshot", "save", "scenario_construction-reviewed")
    run(project, "phase", "advance")
    run(project, "option", "add", "--name", "Staged entry", "--description", "Pilot before committing fully", "--hedging")
    evaluation_args = []
    for index in range(1, 5):
        evaluation_args.extend(["--scenario", f"sc{index:03d}", "--rating", "robust", "--rationale", "Limits exposure while retaining upside."])
    run(project, "option", "evaluate", "op001", *evaluation_args)
    before_report = run(project, "next")
    assert before_report["data"]["stage"] == "reporting"
    run(project, "report", "generate")
    complete = run(project, "next")
    assert complete["data"]["ready"] is True
    assert (project / "output" / "summary.md").exists()
