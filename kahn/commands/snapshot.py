from __future__ import annotations

from pathlib import Path

import typer

from ..renderer import console, render_kv_panel, table
from ..store import KahnError
from .common import HumanOption, ProjectDirOption, QuietOption, fail, finish, should_emit_json, store_for

app = typer.Typer(help="Manage project snapshots.")


@app.command("save")
def save_snapshot(
    label: str,
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "snapshot save"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        destination = store.save_snapshot(label)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, {"label": label, "path": str(destination)})
        return
    if not quiet:
        render_kv_panel("Snapshot saved", [("Label", label), ("Path", str(destination))])


@app.command("list")
def list_snapshots(
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "snapshot list"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        snapshot_root = store.root / "snapshots"
        rows = [{"label": path.name, "timestamp": path.stat().st_mtime} for path in sorted(snapshot_root.iterdir()) if path.is_dir()]
    except FileNotFoundError:
        rows = []
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, rows)
        return
    if quiet:
        return
    tbl = table("Label", "Timestamp")
    for row in rows:
        tbl.add_row(row["label"], str(row["timestamp"]))
    console.print(tbl)


@app.command("restore")
def restore_snapshot(
    label: str,
    confirm: bool = typer.Option(False, "--confirm"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "snapshot restore"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        if not confirm:
            raise KahnError("VALIDATION_FAILED", "Restore requires --confirm.", hint="Re-run with `--confirm`.")
        store.restore_snapshot(label)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, {"restored": label})
        return
    if not quiet:
        render_kv_panel("Snapshot restored", [("Label", label)])
