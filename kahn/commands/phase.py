from __future__ import annotations

from pathlib import Path

import typer

from ..renderer import render_kv_panel
from ..store import KahnError, PHASE_ORDER
from .common import HumanOption, ProjectDirOption, QuietOption, fail, finish, should_emit_json, store_for

app = typer.Typer(help="Manage project phases.")


def _phase_validation(store, phase: str) -> list[str]:
    forces = store.list_forces()
    cus = store.list_critical_uncertainties()
    scenarios = store.list_scenarios()
    issues: list[str] = []
    if phase == "forces":
        if len([f for f in forces if f.type == "uncertainty"]) < 2:
            issues.append("At least 2 uncertainty forces are required.")
        if len([f for f in forces if f.type == "trend"]) < 1:
            issues.append("At least 1 trend force is required.")
    elif phase == "uncertainty_selection":
        if len(cus) != 2 or any(not cu.pole_a or not cu.pole_b for cu in cus):
            issues.append("Both critical uncertainties must exist and have poles set.")
        meta = store.read_meta()
        if "Independence check run." not in (meta.notes or ""):
            issues.append("Independence check must be run before locking uncertainty_selection.")
    elif phase == "scenario_construction":
        if not scenarios:
            issues.append("Scenarios have not been built.")
        for scenario in scenarios:
            if not scenario.name or not scenario.tagline:
                issues.append(f"{scenario.id} is missing a name or tagline.")
            if not store.get_scenario_narrative(scenario.id).strip():
                issues.append(f"{scenario.id} is missing a narrative.")
            if len(store.get_scenario_signals(scenario.id).signals) == 0:
                issues.append(f"{scenario.id} is missing signals.")
    return issues


@app.command("status")
def phase_status(
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "phase status"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        meta = store.read_meta()
        data = {"phase": meta.phase, "locks": meta.phase_locks}
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, data)
        return
    if not quiet:
        render_kv_panel("Phase status", [("Current", meta.phase), ("Locks", ", ".join(meta.phase_locks) or "none")])


@app.command("lock")
def phase_lock(
    phase: str,
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "phase lock"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        meta = store.read_meta()
        issues = _phase_validation(store, phase)
        if issues:
            raise KahnError("DEPENDENCY_MISSING", "Pre-lock validation failed.", context="; ".join(issues))
        lock_index = PHASE_ORDER.index(phase)
        meta.phase_locks = PHASE_ORDER[: lock_index + 1]
        store.write_meta(meta)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, {"phase": phase, "locks": meta.phase_locks})
        return
    if not quiet:
        render_kv_panel("Phase locked", [("Phase", phase), ("Locks", ", ".join(meta.phase_locks))])


@app.command("advance")
def phase_advance(
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "phase advance"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        meta = store.read_meta()
        current_index = PHASE_ORDER.index(meta.phase)
        current_phase = meta.phase
        issues = _phase_validation(store, current_phase)
        if issues:
            raise KahnError("DEPENDENCY_MISSING", "Cannot advance phase.", context="; ".join(issues))
        meta.phase_locks = PHASE_ORDER[: current_index + 1]
        meta.phase = PHASE_ORDER[min(current_index + 1, len(PHASE_ORDER) - 1)]
        store.write_meta(meta)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, {"phase": meta.phase, "locks": meta.phase_locks})
        return
    if not quiet:
        render_kv_panel("Phase advanced", [("Current", meta.phase), ("Locks", ", ".join(meta.phase_locks))])
