from __future__ import annotations

from pathlib import Path

import typer

from ..renderer import render_kv_panel
from ..store import KahnError
from ..workflow import workflow_assessment
from .common import HumanOption, ProjectDirOption, QuietOption, fail, finish, should_emit_json, store_for

app = typer.Typer(help="Project status.")


@app.command("status")
def status_command(
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "status"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        meta = store.read_meta()
        forces = store.list_forces()
        scenarios = store.list_scenarios()
        options = store.list_options()
        cus = store.list_critical_uncertainties()
        data = {
            "project": meta.model_dump(mode="json"),
            "forces": {
                "trend": len([f for f in forces if f.type == "trend"]),
                "uncertainty": len([f for f in forces if f.type == "uncertainty"]),
            },
            "critical_uncertainties": len(cus),
            "scenarios": len(scenarios),
            "options": len(options),
            "workflow": workflow_assessment(store),
        }
        data["next_action"] = data["workflow"]["next_command"]
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, data, next_steps=[data["next_action"]])
        return
    if not quiet:
        render_kv_panel(
            "Project status",
            [
                ("Project", meta.id),
                ("Question", meta.focal_question),
                ("Phase", meta.phase),
                ("Locks", ", ".join(meta.phase_locks) or "none"),
                ("Forces", f"{data['forces']['trend']} trends / {data['forces']['uncertainty']} uncertainties"),
                ("Critical uncertainties", str(data["critical_uncertainties"])),
                ("Scenarios", str(data["scenarios"])),
                ("Strategic options", str(data["options"])),
                ("Next step", data["next_action"]),
            ],
        )


def _next_action(phase: str, locks: list[str], cus: list[object], scenarios: list[object], options: list[object]) -> str:
    if phase == "forces":
        return "kahn force add"
    if phase == "uncertainty_selection" or "forces" in locks and len(cus) < 2:
        return "kahn uncertainty select"
    if phase == "scenario_construction" and not scenarios:
        return "kahn scenario build"
    if phase == "option_evaluation" and not options:
        return "kahn option add"
    return "kahn report generate" if phase == "complete" else "kahn status"
