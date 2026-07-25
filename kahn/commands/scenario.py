from __future__ import annotations

from pathlib import Path

import typer

from ..models import ScenarioMeta, ScenarioSignal, ScenarioSignals
from ..renderer import console, render_kv_panel, render_markdown, table
from ..scorer import compute_consistency_score, pairwise_similarity
from ..store import KahnError, now_utc
from .common import HumanOption, ProjectDirOption, QuietOption, fail, finish, should_emit_json, store_for

app = typer.Typer(help="Manage scenarios.")
narrative_app = typer.Typer(help="Scenario narratives.")
signals_app = typer.Typer(help="Scenario signals.")


@app.command("build")
def build_scenarios(
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "scenario build"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        store.assert_phase_locked("uncertainty_selection")
        if store.list_scenarios():
            raise KahnError("ALREADY_EXISTS", "Scenarios already exist.", hint="Use the existing scenario directories or restore a snapshot.")
        uncertainties = store.list_critical_uncertainties()
        if len(uncertainties) != 2 or any(not cu.pole_a or not cu.pole_b for cu in uncertainties):
            raise KahnError("DEPENDENCY_MISSING", "Exactly 2 critical uncertainties with poles set are required.")
        trends = [force.id for force in store.list_forces() if force.type == "trend"]
        created: list[ScenarioMeta] = []
        combinations = [("pole_a", "pole_a"), ("pole_a", "pole_b"), ("pole_b", "pole_a"), ("pole_b", "pole_b")]
        for index, combo in enumerate(combinations, start=1):
            scenario_id = f"sc{index:03d}"
            scenario = ScenarioMeta(
                id=scenario_id,
                name=f"{uncertainties[0].id}:{combo[0]} × {uncertainties[1].id}:{combo[1]}",
                tagline="",
                axis={uncertainties[0].id: combo[0], uncertainties[1].id: combo[1]},
                predetermined_element_ids=trends,
                internal_consistency_score=0.0,
                consistency_notes="",
                created_at=now_utc(),
                updated_at=now_utc(),
            )
            store.save_scenario_meta(scenario)
            store.save_scenario_narrative(scenario_id, "")
            store.save_scenario_signals(ScenarioSignals(scenario_id=scenario_id, signals=[]))
            created.append(scenario)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, [item.model_dump(mode="json") for item in created], next_steps=["kahn scenario name sc001 --name ... --tagline ..."])
        return
    if not quiet:
        rows = [(scenario.id, f"{scenario.name} -> narrative pending") for scenario in created]
        render_kv_panel("Scenario matrix built", rows + [("Next step", "kahn scenario name sc001 --name ... --tagline ...")])


@app.command("name")
def name_scenario(
    scenario_id: str,
    name: str = typer.Option(..., "--name"),
    tagline: str = typer.Option(..., "--tagline"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "scenario name"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        store.assert_phase_unlocked("scenario_construction")
        scenario = store.get_scenario_meta(scenario_id)
        data = scenario.model_dump()
        data["name"] = name
        data["tagline"] = tagline
        scenario = ScenarioMeta.model_validate(data)
        store.save_scenario_meta(scenario)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, scenario.model_dump(mode="json"))
        return
    if not quiet:
        render_kv_panel("Scenario named", [("ID", scenario.id), ("Name", scenario.name), ("Tagline", scenario.tagline)])


@narrative_app.command("set")
def set_narrative(
    scenario_id: str,
    file: Path | None = typer.Option(None, "--file"),
    text: str | None = typer.Option(None, "--text"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "scenario narrative set"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    warnings: list[str] = []
    try:
        store.assert_phase_unlocked("scenario_construction")
        if bool(file) == bool(text):
            raise KahnError("VALIDATION_FAILED", "Provide exactly one of --file or --text.")
        narrative = file.read_text() if file else text or ""
        store.get_scenario_meta(scenario_id)
        store.save_scenario_narrative(scenario_id, narrative)
        if len(narrative.split()) < 100:
            warnings.append("Narrative is under 100 words.")
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, {"scenario_id": scenario_id, "word_count": len(narrative.split())}, warnings=warnings)
        return
    if not quiet:
        render_kv_panel("Narrative saved", [("Scenario", scenario_id), ("Word count", str(len(narrative.split()))), ("Warnings", "; ".join(warnings) or "none")])


@narrative_app.command("show")
def show_narrative(
    scenario_id: str,
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "scenario narrative show"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        narrative = store.get_scenario_narrative(scenario_id)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, {"scenario_id": scenario_id, "narrative": narrative})
        return
    if not quiet:
        render_markdown(narrative or "_No narrative set._")


@signals_app.command("set")
def set_signals(
    scenario_id: str,
    signal: list[str] = typer.Option([], "--signal"),
    observable_in: list[str] = typer.Option([], "--observable-in"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "scenario signals set"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        store.assert_phase_unlocked("scenario_construction")
        if len(signal) != len(observable_in):
            raise KahnError("VALIDATION_FAILED", "Each --signal must have a matching --observable-in.")
        store.get_scenario_meta(scenario_id)
        signals = ScenarioSignals(
            scenario_id=scenario_id,
            signals=[
                ScenarioSignal(id=f"sig{index:03d}", description=description, observable_in=observed)
                for index, (description, observed) in enumerate(zip(signal, observable_in), start=1)
            ],
        )
        store.save_scenario_signals(signals)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, signals.model_dump(mode="json"))
        return
    if not quiet:
        render_kv_panel("Signals saved", [("Scenario", scenario_id), ("Count", str(len(signals.signals)))])


@signals_app.command("show")
def show_signals(
    scenario_id: str,
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "scenario signals show"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        signals = store.get_scenario_signals(scenario_id)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, signals.model_dump(mode="json"))
        return
    if quiet:
        return
    tbl = table("ID", "Description", "Observable in")
    for item in signals.signals:
        tbl.add_row(item.id, item.description, item.observable_in)
    console.print(tbl)


@app.command("list")
def list_scenarios(
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "scenario list"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        scenarios = store.list_scenarios()
        data = []
        for scenario in scenarios:
            signals = store.get_scenario_signals(scenario.id)
            try:
                narrative = store.get_scenario_narrative(scenario.id)
            except KahnError:
                narrative = ""
            data.append(
                {
                    "id": scenario.id,
                    "name": scenario.name,
                    "tagline": scenario.tagline,
                    "axis": scenario.axis,
                    "narrative_status": "set" if narrative.strip() else "pending",
                    "signal_count": len(signals.signals),
                }
            )
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, data)
        return
    if quiet:
        return
    tbl = table("ID", "Name", "Tagline", "Narrative", "Signals")
    for item in data:
        tbl.add_row(item["id"], item["name"], item["tagline"], item["narrative_status"], str(item["signal_count"]))
    console.print(tbl)


@app.command("show")
def show_scenario(
    scenario_id: str,
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "scenario show"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        scenario = store.get_scenario_meta(scenario_id)
        narrative = store.get_scenario_narrative(scenario_id)
        signals = store.get_scenario_signals(scenario_id)
        data = {
            "meta": scenario.model_dump(mode="json"),
            "narrative": narrative,
            "signals": signals.model_dump(mode="json"),
        }
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, data)
        return
    if not quiet:
        render_kv_panel("Scenario", [("ID", scenario.id), ("Name", scenario.name), ("Tagline", scenario.tagline)])
        render_markdown(narrative or "_No narrative set._")
        show_signals(scenario_id, project_dir, False, False)


@app.command("check-consistency")
def check_consistency(
    scenario: str | None = typer.Option(None, "--scenario"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "scenario check-consistency"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        forces = store.list_forces()
        scenarios = [store.get_scenario_meta(scenario)] if scenario else store.list_scenarios()
        results = []
        for item in scenarios:
            narrative = store.get_scenario_narrative(item.id)
            score, notes = compute_consistency_score(item, narrative, forces)
            data = item.model_dump()
            data["internal_consistency_score"] = score
            data["consistency_notes"] = notes
            updated = ScenarioMeta.model_validate(data)
            store.save_scenario_meta(updated)
            results.append({"id": item.id, "score": score, "notes": notes})
        similarity = [] if scenario else pairwise_similarity(scenarios)
    except KahnError as err:
        fail(command, err, json_flag)
    PASSING_THRESHOLD = 0.70
    payload = {"scenarios": results, "pairwise_similarity": similarity, "passing_threshold": PASSING_THRESHOLD}
    if json_flag:
        finish(command, payload)
        return
    if quiet:
        return
    tbl = table("Scenario", "Score", "Pass (≥0.70)", "Notes")
    for result in results:
        passing = "yes" if result["score"] >= PASSING_THRESHOLD else "no"
        tbl.add_row(result["id"], f"{result['score']:.2f}", passing, result["notes"])
    console.print(tbl)
    if similarity:
        sim_table = table("Left", "Right", "Similarity")
        for left, right, label in similarity:
            sim_table.add_row(left, right, label)
        console.print(sim_table)


app.add_typer(narrative_app, name="narrative")
app.add_typer(signals_app, name="signals")
