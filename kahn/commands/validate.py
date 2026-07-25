from __future__ import annotations

from pathlib import Path

import typer

from ..renderer import render_kv_panel
from ..store import KahnError
from ..validator import validate_project
from .common import HumanOption, ProjectDirOption, QuietOption, fail, finish, should_emit_json, store_for

app = typer.Typer(help="Validate the project.")


@app.command("validate")
def validate_command(
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "validate"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        store.read_meta()
        errors = validate_project(store)
    except KahnError as err:
        fail(command, err, json_flag)
    data = {"valid": not errors, "errors": errors}
    if json_flag:
        finish(command, data)
        return
    if not quiet:
        render_kv_panel("Validation", [("Status", "PASS" if not errors else "FAIL"), ("Errors", "; ".join(errors) or "none")])
