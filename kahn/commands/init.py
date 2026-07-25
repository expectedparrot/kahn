from __future__ import annotations

from pathlib import Path

import typer

from ..models import ProjectMeta
from ..renderer import render_kv_panel
from ..store import KahnError, now_utc
from .common import HumanOption, ProjectDirOption, QuietOption, fail, should_emit_json, store_for

app = typer.Typer(help="Initialize a new project.")


@app.command("init")
def init_command(
    question: str = typer.Option(..., "--question"),
    domain: str = typer.Option(..., "--domain"),
    horizon: str = typer.Option(..., "--horizon"),
    id: str | None = typer.Option(None, "--id"),
    notes: str | None = typer.Option(None, "--notes"),
    force: bool = typer.Option(False, "--force"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "init"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        timestamp = now_utc()
        project_id = id or f"sp_{timestamp.year}_{timestamp.strftime('%m%d%H%M%S')}"
        meta = ProjectMeta(
            id=project_id,
            focal_question=question,
            domain=domain,
            horizon=horizon,
            created_at=timestamp,
            updated_at=timestamp,
            phase="forces",
            phase_locks=[],
            notes=notes,
        )
        store.init_project(meta, force=force)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        from .common import finish

        finish(command, meta.model_dump(mode="json"), next_steps=["kahn force add"])
        return
    if not quiet:
        render_kv_panel(
            "Project initialized",
            [
                ("Project", meta.id),
                ("Focal question", meta.focal_question),
                ("Domain", f"{meta.domain} | Horizon: {meta.horizon}"),
                ("Next step", "kahn force add"),
            ],
        )
