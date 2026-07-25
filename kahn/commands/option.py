from __future__ import annotations

from pathlib import Path

import typer

from ..models import OptionMeta, OptionPerformance, ScenarioEvaluation
from ..renderer import console, render_kv_panel, table
from ..scorer import compute_robustness_score
from ..store import KahnError, now_utc
from .common import HumanOption, ProjectDirOption, QuietOption, fail, finish, should_emit_json, store_for

app = typer.Typer(help="Manage strategic options.")


@app.command("add")
def add_option(
    name: str = typer.Option(..., "--name"),
    description: str = typer.Option(..., "--description"),
    hedging: bool = typer.Option(False, "--hedging"),
    notes: str | None = typer.Option(None, "--notes"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "option add"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        store.assert_phase_locked("scenario_construction")
        with store.locked():
            option_id = store.next_id("op", store.list_option_ids())
            option = OptionMeta(id=option_id, name=name, description=description, hedging_value=hedging, created_at=now_utc(), notes=notes)
            store.save_option_meta(option)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, option.model_dump(mode="json"))
        return
    if not quiet:
        render_kv_panel("Option added", [("ID", option.id), ("Name", option.name), ("Hedging", str(option.hedging_value))])


@app.command("list")
def list_options(
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "option list"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        options = store.list_options()
        rows = []
        for option in options:
            evaluated = (store.option_dir(option.id) / "performance.json").exists()
            rows.append({"id": option.id, "name": option.name, "hedging_value": option.hedging_value, "evaluated": evaluated})
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, rows)
        return
    if quiet:
        return
    tbl = table("ID", "Name", "Hedging", "Evaluated")
    for row in rows:
        tbl.add_row(row["id"], row["name"], str(row["hedging_value"]), "yes" if row["evaluated"] else "no")
    console.print(tbl)


@app.command("show")
def show_option(
    option_id: str,
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "option show"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        option = store.get_option_meta(option_id)
        data = {"meta": option.model_dump(mode="json")}
        if (store.option_dir(option_id) / "performance.json").exists():
            data["performance"] = store.get_option_performance(option_id).model_dump(mode="json")
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, data)
        return
    if not quiet:
        render_kv_panel("Option", [("ID", option.id), ("Name", option.name), ("Description", option.description)])


@app.command("evaluate")
def evaluate_option(
    option_id: str,
    scenario: list[str] = typer.Option([], "--scenario"),
    rating: list[str] = typer.Option([], "--rating"),
    rationale: list[str] = typer.Option([], "--rationale"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "option evaluate"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        store.assert_phase_locked("scenario_construction")
        if not (len(scenario) == len(rating) == len(rationale)):
            raise KahnError("VALIDATION_FAILED", "Scenario, rating, and rationale counts must match.")
        store.get_option_meta(option_id)
        evaluations = {}
        for scenario_id, scenario_rating, scenario_rationale in zip(scenario, rating, rationale):
            store.get_scenario_meta(scenario_id)
            evaluations[scenario_id] = ScenarioEvaluation(rating=scenario_rating, rationale=scenario_rationale)
        performance = OptionPerformance(
            option_id=option_id,
            evaluations=evaluations,
            robustness_score=compute_robustness_score([item.rating for item in evaluations.values()]),
            evaluated_at=now_utc(),
        )
        store.save_option_performance(performance)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, performance.model_dump(mode="json"))
        return
    if not quiet:
        render_kv_panel("Option evaluated", [("ID", option_id), ("Robustness score", f"{performance.robustness_score:.2f}")])


@app.command("evaluate-all")
def evaluate_all(
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "option evaluate-all"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        scenarios = store.list_scenarios()
        rows = []
        for option in store.list_options():
            evaluations = {}
            perf_path = store.option_dir(option.id) / "performance.json"
            if perf_path.exists():
                evaluations = store.get_option_performance(option.id).evaluations
            rows.append(
                {
                    "option_id": option.id,
                    "option_name": option.name,
                    "ratings": {scenario.id: evaluations.get(scenario.id).rating if scenario.id in evaluations else None for scenario in scenarios},
                }
            )
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, rows)
        return
    if quiet:
        return
    tbl = table("Option", *[scenario.id for scenario in scenarios])
    for row in rows:
        tbl.add_row(f"{row['option_id']} {row['option_name']}", *[(row["ratings"][scenario.id] or "-") for scenario in scenarios])
    console.print(tbl)


@app.command("robustness-rank")
def robustness_rank(
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "option robustness-rank"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    try:
        rankings = []
        for option in store.list_options():
            performance = store.get_option_performance(option.id)
            fragile = any(evaluation.rating == "fragile" for evaluation in performance.evaluations.values())
            rankings.append(
                {
                    "id": option.id,
                    "name": option.name,
                    "score": performance.robustness_score,
                    "fragile": fragile,
                    "hedging": option.hedging_value,
                }
            )
        rankings.sort(key=lambda item: item["score"], reverse=True)
    except KahnError as err:
        fail(command, err, json_flag)
    if json_flag:
        finish(command, rankings)
        return
    if quiet:
        return
    tbl = table("Rank", "ID", "Name", "Score", "Fragile", "Hedging")
    for index, row in enumerate(rankings, start=1):
        tbl.add_row(str(index), row["id"], row["name"], f"{row['score']:.2f}", "YES" if row["fragile"] else "no", "yes" if row["hedging"] else "no")
    console.print(tbl)
