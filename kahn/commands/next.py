from __future__ import annotations

from pathlib import Path

import typer

from ..renderer import render_kv_panel
from ..workflow import workflow_assessment
from .common import HumanOption, ProjectDirOption, QuietOption, finish, should_emit_json, store_for

app = typer.Typer(help="Inspect project state and return the next workflow action.")


@app.command("next")
def next_command(
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    """Return the first incomplete workflow gate and its command."""
    assessment = workflow_assessment(store_for(project_dir))
    if should_emit_json(human):
        finish("next", assessment, next_steps=[assessment["next_command"]])
        return
    if not quiet:
        render_kv_panel("Kahn next", [("Stage", assessment["stage"]), ("State", assessment["reason"]), ("Next step", assessment["next_command"])])
