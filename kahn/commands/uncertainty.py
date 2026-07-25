from __future__ import annotations

from pathlib import Path

import typer

from ..models import CriticalUncertainty
from ..renderer import render_kv_panel, table
from ..store import KahnError, now_utc
from .common import HumanOption, ProjectDirOption, QuietOption, fail, finish, should_emit_json, store_for

app = typer.Typer(help="Manage critical uncertainties.")


@app.command("select")
def select_uncertainties(
    force_id_a: str,
    force_id_b: str,
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "uncertainty select"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    warnings: list[str] = []
    try:
        store.assert_phase_unlocked("uncertainty_selection")
        if store.list_critical_uncertainties():
            raise KahnError("ALREADY_EXISTS", "Critical uncertainties already exist.", hint="Edit the existing files or restore a snapshot.")
        selected = [store.get_force(force_id_a), store.get_force(force_id_b)]
        for force in selected:
            if force.type != "uncertainty" or force.impact_magnitude != "high":
                raise KahnError("VALIDATION_FAILED", "Selected forces must be high-impact uncertainties.", context=force.id)
            if force.predictability != "low":
                warnings.append(f"{force.id} predictability is {force.predictability}, not low.")
        created: list[CriticalUncertainty] = []
        for index, force in enumerate(selected, start=1):
            cu = CriticalUncertainty(
                id=f"cu{index:03d}",
                source_force_id=force.id,
                name=force.name,
                description=force.direction,
                pole_a="",
                pole_b="",
                independence_note="",
                created_at=now_utc(),
            )
            store.save_critical_uncertainty(cu)
            created.append(cu)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, [cu.model_dump(mode="json") for cu in created], warnings=warnings, next_steps=["kahn uncertainty set-poles cu001 --pole-a ... --pole-b ..."])
        return
    if not quiet:
        render_kv_panel(
            "Critical uncertainties selected",
            [
                (created[0].id, f"{created[0].source_force_id} ({created[0].name})"),
                (created[1].id, f"{created[1].source_force_id} ({created[1].name})"),
                ("Next step", "kahn uncertainty set-poles cu001 --pole-a ... --pole-b ..."),
            ],
        )


@app.command("set-poles")
def set_poles(
    cu_id: str,
    pole_a: str = typer.Option(..., "--pole-a"),
    pole_b: str = typer.Option(..., "--pole-b"),
    description: str | None = typer.Option(None, "--description"),
    independence_note: str | None = typer.Option(None, "--independence-note"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "uncertainty set-poles"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        store.assert_phase_unlocked("uncertainty_selection")
        cu = store.get_critical_uncertainty(cu_id)
        data = cu.model_dump()
        data["pole_a"] = pole_a
        data["pole_b"] = pole_b
        if description is not None:
            data["description"] = description
        if independence_note is not None:
            data["independence_note"] = independence_note
        cu = CriticalUncertainty.model_validate(data)
        store.save_critical_uncertainty(cu)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, cu.model_dump(mode="json"))
        return
    if not quiet:
        render_kv_panel("Critical uncertainty updated", [("ID", cu.id), ("Name", cu.name)])


@app.command("list")
def list_uncertainties(
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "uncertainty list"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        uncertainties = store.list_critical_uncertainties()
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, [cu.model_dump(mode="json") for cu in uncertainties])
        return
    if quiet:
        return
    tbl = table("ID", "Name", "Pole A", "Pole B")
    for cu in uncertainties:
        tbl.add_row(cu.id, cu.name, cu.pole_a or "-", cu.pole_b or "-")
    from ..renderer import console

    console.print(tbl)


@app.command("show")
def show_uncertainty(
    cu_id: str,
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "uncertainty show"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        cu = store.get_critical_uncertainty(cu_id)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, cu.model_dump(mode="json"))
        return
    if not quiet:
        render_kv_panel(
            cu.id,
            [
                ("Name", cu.name),
                ("Description", cu.description),
                ("Pole A", cu.pole_a),
                ("Pole B", cu.pole_b),
                ("Independence note", cu.independence_note),
            ],
        )


@app.command("check-independence")
def check_independence(
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "uncertainty check-independence"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        uncertainties = store.list_critical_uncertainties()
        if len(uncertainties) != 2:
            raise KahnError("DEPENDENCY_MISSING", "Exactly 2 critical uncertainties are required.")
        left, right = uncertainties
        correlated = any(token and token in right.description.lower() for token in left.name.lower().split())
        if correlated:
            message = f"Possible correlation detected: {left.name} may influence {right.name}."
            status = "advisory"
            remediation = (
                f"This is an advisory warning — you may still proceed. "
                f"If the axes are too closely related, scenarios will not be sufficiently distinct. "
                f"Consider replacing {left.id} or {right.id} with a more independent force. "
                f"Run `kahn force list --type uncertainty` to review alternatives."
            )
        else:
            message = f"No obvious correlation detected between {left.name} and {right.name}."
            status = "pass"
            remediation = "Safe to proceed."
    except KahnError as err:
        fail(command, err, json_flag)
    meta = store.read_meta()
    if "uncertainty_selection" not in meta.phase_locks:
        meta.notes = ((meta.notes or "").rstrip() + "\nIndependence check run.").strip()
        store.write_meta(meta)
    data = {"assessment": message, "correlated": correlated, "status": status, "remediation": remediation}
    if json_flag:
        finish(command, data)
        return
    if not quiet:
        render_kv_panel(
            "Independence check",
            [
                ("Assessment", message),
                ("Status", status),
                ("Remediation", remediation),
            ],
        )
