from __future__ import annotations

from pathlib import Path

import typer

from ..models import Force
from ..renderer import render_kv_panel
from ..store import KahnError, now_utc
from .common import HumanOption, ProjectDirOption, QuietOption, fail, finish, should_emit_json, store_for

app = typer.Typer(help="Manage environmental forces.")


@app.command("add")
def add_force(
    name: str = typer.Option(..., "--name"),
    domain: str = typer.Option(..., "--domain"),
    type: str = typer.Option(..., "--type"),
    impact: str = typer.Option(..., "--impact"),
    predictability: str = typer.Option(..., "--predictability"),
    direction: str = typer.Option(..., "--direction"),
    notes: str | None = typer.Option(None, "--notes"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "force add"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        store.assert_phase_unlocked("forces")
        with store.locked():
            force_id = store.next_id("f", [force.id for force in store.list_forces()])
            force = Force(
                id=force_id,
                name=name,
                domain=domain,
                type=type,
                direction=direction,
                impact_magnitude=impact,
                predictability=predictability,
                created_at=now_utc(),
                notes=notes,
            )
            store.save_force(force)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, force.model_dump(mode="json"), next_steps=["kahn force list"])
        return
    if not quiet:
        render_kv_panel(
            "Force added",
            [
                ("ID", force.id),
                ("Name", f"{force.name} [{force.domain} | {force.type}]"),
                ("Impact", f"{force.impact_magnitude} | Predictability: {force.predictability}"),
            ],
        )


@app.command("list")
def list_forces(
    type: str | None = typer.Option(None, "--type"),
    impact: str | None = typer.Option(None, "--impact"),
    domain: str | None = typer.Option(None, "--domain"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "force list"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        forces = store.list_forces()
    except KahnError as err:
        fail(command, err, json_flag)
    if type:
        forces = [force for force in forces if force.type == type]
    if impact:
        forces = [force for force in forces if force.impact_magnitude == impact]
    if domain:
        forces = [force for force in forces if force.domain == domain]
    if json_flag:
        finish(command, [force.model_dump(mode="json") for force in forces])
        return
    if quiet:
        return
    from rich.table import Table

    from ..renderer import console

    tbl = Table(show_header=True, header_style="bold cyan")
    tbl.add_column("ID")
    tbl.add_column("Name", overflow="fold", min_width=20)
    tbl.add_column("Domain")
    tbl.add_column("Type")
    tbl.add_column("Impact")
    tbl.add_column("Predictability")
    for force in forces:
        tbl.add_row(force.id, force.name, force.domain, force.type, force.impact_magnitude, force.predictability)
    console.print(tbl)


@app.command("show")
def show_force(
    force_id: str,
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "force show"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        force = store.get_force(force_id)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, force.model_dump(mode="json"))
        return
    if not quiet:
        render_kv_panel(
            force.id,
            [
                ("Name", force.name),
                ("Domain", force.domain),
                ("Type", force.type),
                ("Direction", force.direction),
                ("Impact", force.impact_magnitude),
                ("Predictability", force.predictability),
                ("Notes", force.notes or ""),
            ],
        )


@app.command("edit")
def edit_force(
    force_id: str,
    name: str | None = typer.Option(None, "--name"),
    impact: str | None = typer.Option(None, "--impact"),
    predictability: str | None = typer.Option(None, "--predictability"),
    direction: str | None = typer.Option(None, "--direction"),
    notes: str | None = typer.Option(None, "--notes"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "force edit"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        store.assert_phase_unlocked("forces")
        force = store.get_force(force_id)
        updates = force.model_dump()
        if name is not None:
            updates["name"] = name
        if impact is not None:
            updates["impact_magnitude"] = impact
        if predictability is not None:
            updates["predictability"] = predictability
        if direction is not None:
            updates["direction"] = direction
        if notes is not None:
            updates["notes"] = notes
        force = Force.model_validate(updates)
        store.save_force(force)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, force.model_dump(mode="json"))
        return
    if not quiet:
        render_kv_panel("Force updated", [("ID", force.id), ("Name", force.name)])


@app.command("delete")
def delete_force(
    force_id: str,
    confirm: bool = typer.Option(False, "--confirm"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "force delete"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        store.assert_phase_unlocked("forces")
        if not confirm:
            raise KahnError("VALIDATION_FAILED", "Deletion requires --confirm.", hint="Re-run with `--confirm`.")
        warnings: list[str] = []
        for cu in store.list_critical_uncertainties():
            if cu.source_force_id == force_id:
                warnings.append(f"{force_id} is referenced by {cu.id}")
        store.delete_force(force_id)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, {"deleted": force_id}, warnings=warnings)
        return
    if not quiet:
        render_kv_panel("Force deleted", [("ID", force_id), ("Warnings", "; ".join(warnings) or "none")])
