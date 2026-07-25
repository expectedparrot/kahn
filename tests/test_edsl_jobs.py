from __future__ import annotations

from datetime import datetime, timezone

from edsl import Agent, Jobs, Model, Results, Scenario
from edsl.results import Result

from kahn import edsl_jobs
from kahn.ingest import ingest_narrative, ingest_option_evaluations
from kahn.models import (
    CriticalUncertainty,
    Force,
    OptionMeta,
    ProjectMeta,
    ScenarioMeta,
)
from kahn.store import ProjectStore


def fixtures():
    now = datetime(2026, 7, 24, tzinfo=timezone.utc)
    meta = ProjectMeta(
        id="sp_test",
        focal_question="How should we enter the market?",
        domain="energy",
        horizon="2030",
        created_at=now,
        updated_at=now,
    )
    force = Force(
        id="f001",
        name="Falling storage costs",
        domain="technological",
        type="trend",
        direction="decreasing",
        impact_magnitude="high",
        predictability="high",
        created_at=now,
    )
    uncertainties = [
        CriticalUncertainty(
            id="cu001", source_force_id="f002", name="Regulation", description="",
            pole_a="open", pole_b="closed", independence_note="", created_at=now,
        ),
        CriticalUncertainty(
            id="cu002", source_force_id="f003", name="Adoption", description="",
            pole_a="rapid", pole_b="slow", independence_note="", created_at=now,
        ),
    ]
    scenario = ScenarioMeta(
        id="sc001", name="Open acceleration", tagline="Markets expand",
        axis={"cu001": "pole_a", "cu002": "pole_a"}, created_at=now, updated_at=now,
    )
    option = OptionMeta(id="op001", name="Pilot", description="Enter with a pilot.", created_at=now)
    return meta, force, uncertainties, scenario, option


def initialized_store(tmp_path):
    meta, force, uncertainties, scenario, option = fixtures()
    store = ProjectStore(tmp_path / "project")
    store.init_project(meta)
    store.save_force(force)
    for uncertainty in uncertainties:
        store.save_critical_uncertainty(uncertainty)
    store.save_scenario_meta(scenario)
    store.save_scenario_narrative(scenario.id, "Initial narrative")
    store.save_option_meta(option)
    return store


def make_results(jobs, answers):
    result = Result(
        agent=Agent(name="test_agent"),
        scenario=Scenario(dict(jobs.scenarios[0])),
        model=Model("test"),
        iteration=0,
        answer=answers,
    )
    return Results(survey=jobs.survey, data=[result])


def test_all_builders_are_model_free() -> None:
    meta, force, uncertainties, scenario, option = fixtures()
    jobs_objects = [
        edsl_jobs.research_forces_jobs(meta, [force]),
        edsl_jobs.narrative_jobs(meta, scenario, uncertainties, [force]),
        edsl_jobs.evaluate_options_jobs(meta, [option], [scenario], {scenario.id: "A plausible world."}),
    ]
    assert [jobs.survey.question_names for jobs in jobs_objects] == [
        ["trends", "uncertainties"],
        ["narrative"],
        ["eval_op001_sc001"],
    ]
    assert all(len(jobs.models) == 0 for jobs in jobs_objects)


def test_jobs_round_trip_as_portable_ep_package(tmp_path) -> None:
    meta, force, _, _, _ = fixtures()
    output = tmp_path / "research-forces.jobs.ep"
    edsl_jobs.save_jobs(edsl_jobs.research_forces_jobs(meta, [force]), output)
    loaded = Jobs.git.load(output)
    assert loaded.survey.question_names == ["trends", "uncertainties"]
    assert len(loaded.models) == 0
    assert dict(loaded.scenarios[0])["project_id"] == "sp_test"
    assert edsl_jobs.expected_results_path(output).name == "research-forces-results.ep"


def test_narrative_results_ingest_into_matching_scenario(tmp_path) -> None:
    store = initialized_store(tmp_path)
    meta, force, uncertainties, scenario, _ = fixtures()
    jobs = edsl_jobs.narrative_jobs(meta, scenario, uncertainties, [force])
    results = make_results(jobs, {"narrative": "A concrete future unfolds. " * 60})
    word_count, warnings = ingest_narrative(store, results, scenario.id)
    assert word_count >= 100
    assert warnings == []
    assert store.get_scenario_narrative(scenario.id).startswith("A concrete future")


def test_option_results_are_validated_and_ingested(tmp_path) -> None:
    store = initialized_store(tmp_path)
    meta, _, _, scenario, option = fixtures()
    jobs = edsl_jobs.evaluate_options_jobs(meta, [option], [scenario], {scenario.id: "A plausible world."})
    results = make_results(jobs, {
        "eval_op001_sc001": {
            "rating": "robust",
            "rationale": "The pilot limits exposure while preserving access.",
        }
    })
    performances = ingest_option_evaluations(store, results)
    assert performances[0].robustness_score == 1.0
    assert store.get_option_performance("op001").evaluations["sc001"].rating == "robust"
