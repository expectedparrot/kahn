from __future__ import annotations

from pathlib import Path

import typer

from ..ingest import ingest_forces, ingest_narrative, ingest_option_evaluations, load_results
from ..renderer import render_kv_panel
from ..store import KahnError
from .common import HumanOption, ProjectDirOption, QuietOption, fail, finish, should_emit_json, store_for

app = typer.Typer(help="Ingest EDSL Results into the Kahn project store.")


@app.command("forces")
def ingest_forces_command(
    from_file: Path = typer.Option(..., "--from", help="Path to an EDSL Results .ep file."),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "ingest forces"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        store.require_project()
        created, warnings = ingest_forces(store, load_results(from_file))
    except KahnError as err:
        fail(command, err, json_flag)
    payload = {"created": len(created), "forces": [item.model_dump(mode="json") for item in created]}
    if json_flag:
        finish(command, payload, warnings=warnings, next_steps=["kahn force list"])
        return
    if not quiet:
        render_kv_panel("Forces ingested", [("Created", str(len(created))), ("Warnings", "; ".join(warnings) or "none")])


@app.command("narrative")
def ingest_narrative_command(
    scenario_id: str,
    from_file: Path = typer.Option(..., "--from", help="Path to an EDSL Results .ep file."),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "ingest narrative"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        store.require_project()
        word_count, warnings = ingest_narrative(store, load_results(from_file), scenario_id)
    except KahnError as err:
        fail(command, err, json_flag)
    payload = {"scenario_id": scenario_id, "word_count": word_count, "source_results": str(from_file)}
    if json_flag:
        finish(command, payload, warnings=warnings, next_steps=[f"kahn scenario narrative show {scenario_id}"])
        return
    if not quiet:
        render_kv_panel("Narrative ingested", [("Scenario", scenario_id), ("Words", str(word_count))])


@app.command("option-evaluations")
def ingest_option_evaluations_command(
    from_file: Path = typer.Option(..., "--from", help="Path to an EDSL Results .ep file."),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "ingest option-evaluations"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        store.require_project()
        created = ingest_option_evaluations(store, load_results(from_file))
    except KahnError as err:
        fail(command, err, json_flag)
    payload = {"created": len(created), "performances": [item.model_dump(mode="json") for item in created]}
    if json_flag:
        finish(command, payload, next_steps=["kahn option robustness-rank"])
        return
    if not quiet:
        render_kv_panel("Option evaluations ingested", [("Options", str(len(created)))])
