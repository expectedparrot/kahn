from __future__ import annotations

from pathlib import Path
from typing import Callable

import typer

from .. import edsl_jobs
from ..renderer import render_kv_panel
from ..store import KahnError
from .common import HumanOption, ProjectDirOption, QuietOption, fail, finish, should_emit_json, store_for

app = typer.Typer(help="Build portable, model-free EDSL Jobs packages.")
generate_app = typer.Typer(help="Build .jobs.ep packages for AI-assisted workflow steps.")
app.add_typer(generate_app, name="generate")


def _default_output(name: str) -> Path:
    return Path("jobs") / f"{name}.jobs.ep"


def _build(
    command: str,
    phase: str,
    output: Path,
    project_dir: Path | None,
    human: bool,
    quiet: bool,
    builder: Callable,
    ingest_command: str,
) -> None:
    json_flag = should_emit_json(human)
    try:
        jobs = builder(store_for(project_dir))
        saved = edsl_jobs.save_jobs(jobs, output)
    except KahnError as err:
        fail(command, err, json_flag)
    except Exception as exc:
        fail(command, KahnError("EDSL_ERROR", str(exc), context=str(output)), json_flag)
    expected = edsl_jobs.expected_results_path(output)
    output = output.resolve()
    expected = expected.resolve()
    run = f"ep run {output} --model <model-name> --output {expected}"
    data = {
        "object_type": "Jobs",
        "phase": phase,
        "output_path": str(output),
        "expected_results_path": str(expected),
        "question_names": list(jobs.survey.question_names),
        "agent_count": len(jobs.agents),
        "scenario_count": len(jobs.scenarios),
        "model_count": len(jobs.models),
        "saved": saved,
        "execution_plan": [
            {"label": "Inspect Jobs", "argv": ["ep", "inspect", str(output)], "may_spend_money": False, "requires_user_approval": False},
            {"label": "Estimate cost", "argv": ["ep", "jobs", "cost", str(output)], "may_spend_money": False, "requires_user_approval": False},
            {"label": "Run Jobs", "argv": ["ep", "run", str(output), "--model"], "output_argv": ["--output", str(expected)], "input_schema": {"model": {"type": "string", "required": True}}, "may_spend_money": True, "requires_user_approval": True},
            {"label": "Ingest Results", "argv": [*ingest_command.split(), "--from", str(expected), "--project-dir", str(store_for(project_dir).root.resolve())], "may_spend_money": False, "requires_user_approval": False},
        ],
    }
    next_steps = [
        f"ep inspect {output}",
        f"ep jobs cost {output}",
        run,
        f"{ingest_command} --from {expected}",
    ]
    if json_flag:
        finish(command, data, next_steps=next_steps)
        return
    if not quiet:
        render_kv_panel("EDSL Jobs package", [
            ("Phase", phase),
            ("Jobs", str(output)),
            ("Inspect", f"ep inspect {output}"),
            ("Run", run),
            ("Ingest", f"{ingest_command} --from {expected}"),
        ])


@generate_app.command("research-forces")
def generate_research_forces(
    output: Path = typer.Option(_default_output("research-forces"), "--output", "-o"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    def builder(store):
        store.require_project()
        return edsl_jobs.research_forces_jobs(store.read_meta(), store.list_forces())
    _build(
        "job generate research-forces", "research_forces", output, project_dir, human, quiet,
        builder, "kahn ingest forces",
    )


@generate_app.command("write-narrative")
def generate_write_narrative(
    scenario_id: str,
    output: Path | None = typer.Option(None, "--output", "-o"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    output = output or _default_output(f"narrative-{scenario_id}")

    def builder(store):
        store.require_project()
        scenario = store.get_scenario_meta(scenario_id)
        uncertainties = store.list_critical_uncertainties()
        if len(uncertainties) != 2:
            raise KahnError("DEPENDENCY_MISSING", "Two critical uncertainties are required.")
        return edsl_jobs.narrative_jobs(store.read_meta(), scenario, uncertainties, store.list_forces())
    _build(
        "job generate write-narrative", "write_narrative", output, project_dir, human, quiet,
        builder, f"kahn ingest narrative {scenario_id}",
    )


@generate_app.command("evaluate-options")
def generate_evaluate_options(
    output: Path = typer.Option(_default_output("evaluate-options"), "--output", "-o"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    def builder(store):
        store.require_project()
        options, scenarios = store.list_options(), store.list_scenarios()
        if not options or not scenarios:
            raise KahnError("DEPENDENCY_MISSING", "Strategic options and scenarios are required.")
        narratives = {scenario.id: store.get_scenario_narrative(scenario.id) for scenario in scenarios}
        return edsl_jobs.evaluate_options_jobs(store.read_meta(), options, scenarios, narratives)
    _build(
        "job generate evaluate-options", "evaluate_options", output, project_dir, human, quiet,
        builder, "kahn ingest option-evaluations",
    )
