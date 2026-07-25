from __future__ import annotations

from pathlib import Path
from typing import Any

from .store import KahnError


def _imports() -> tuple[Any, ...]:
    try:
        from edsl import Agent, AgentList, Jobs, Scenario, ScenarioList, Survey
        from edsl.questions import QuestionDict, QuestionFreeText, QuestionList
    except ImportError as exc:
        raise KahnError(
            "DEPENDENCY_ERROR",
            "EDSL is required to create or ingest .ep objects.",
            hint="Install Kahn with its declared dependencies.",
        ) from exc
    return Agent, AgentList, Jobs, Scenario, ScenarioList, Survey, QuestionDict, QuestionFreeText, QuestionList


def expected_results_path(output: Path) -> Path:
    if output.name.endswith(".jobs.ep"):
        return output.with_name(f"{output.name[:-8]}-results.ep")
    return output.with_name(f"{output.stem}-results.ep")


def save_jobs(jobs: Any, output: Path) -> Any:
    if output.suffix != ".ep":
        raise KahnError("VALIDATION_FAILED", "--output must use the .ep extension.", context=str(output))
    if output.exists():
        raise KahnError("ALREADY_EXISTS", "Output already exists.", context=str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    return jobs.git.save(output)


def research_forces_jobs(meta: Any, existing_forces: list[Any]) -> Any:
    Agent, AgentList, Jobs, Scenario, ScenarioList, Survey, _, _, QuestionList = _imports()
    format_instruction = (
        "Format each item exactly as: NAME | PESTEL DOMAIN | IMPACT | PREDICTABILITY | DIRECTION | NOTES. "
        "DOMAIN must be political, economic, social, technological, environmental, or legal. "
        "IMPACT and PREDICTABILITY must each be low, medium, or high."
    )
    questions = [
        QuestionList(
            question_name="trends",
            question_text=(
                "Focal question: {{ focal_question }}\nDomain: {{ domain }}\nHorizon: {{ horizon }}\n"
                "Existing forces to avoid duplicating:\n{{ existing_forces }}\n\n"
                "Identify 4-6 external trends with a fairly predictable direction. "
                + format_instruction
            ),
            max_list_items=6,
        ),
        QuestionList(
            question_name="uncertainties",
            question_text=(
                "Focal question: {{ focal_question }}\nDomain: {{ domain }}\nHorizon: {{ horizon }}\n"
                "Existing forces to avoid duplicating:\n{{ existing_forces }}\n\n"
                "Identify 4-6 high-impact external forces with genuinely uncertain outcomes. "
                + format_instruction
            ),
            max_list_items=6,
        ),
    ]
    scenario = Scenario({
        "kahn_phase": "research_forces",
        "project_id": meta.id,
        "focal_question": meta.focal_question,
        "domain": meta.domain,
        "horizon": meta.horizon,
        "existing_forces": "\n".join(f"- {force.name}" for force in existing_forces) or "(none)",
    })
    researcher = Agent(name="kahn_researcher", traits={"persona": "Strategic foresight environmental-scanning analyst"})
    return Jobs(survey=Survey(questions)).by(AgentList([researcher])).by(ScenarioList([scenario]))


def narrative_jobs(meta: Any, scenario_meta: Any, uncertainties: list[Any], forces: list[Any]) -> Any:
    Agent, AgentList, Jobs, Scenario, ScenarioList, _, _, QuestionFreeText, _ = _imports()
    uncertainty_by_id = {item.id: item for item in uncertainties}
    axis_outcomes = []
    for uncertainty_id, pole_key in scenario_meta.axis.items():
        uncertainty = uncertainty_by_id.get(uncertainty_id)
        if uncertainty:
            axis_outcomes.append(
                f"{uncertainty.name}: {uncertainty.pole_a if pole_key == 'pole_a' else uncertainty.pole_b}"
            )
    question = QuestionFreeText(
        question_name="narrative",
        question_text=(
            "Write a 250-350 word scenario narrative in present tense.\n"
            "Focal question: {{ focal_question }}\nDomain: {{ domain }}\nHorizon: {{ horizon }}\n"
            "Scenario: {{ scenario_name }} — {{ scenario_tagline }}\n"
            "Axis outcomes:\n{{ axis_outcomes }}\nPredetermined trends:\n{{ trend_forces }}\n\n"
            "Open with a concrete trigger event, explain how this world emerged, name winners and losers, "
            "include opportunities and threats, and avoid treating this as the good or bad scenario. "
            "Write a story, not a list."
        ),
    )
    scenario = Scenario({
        "kahn_phase": "write_narrative",
        "project_id": meta.id,
        "scenario_id": scenario_meta.id,
        "focal_question": meta.focal_question,
        "domain": meta.domain,
        "horizon": meta.horizon,
        "scenario_name": scenario_meta.name,
        "scenario_tagline": scenario_meta.tagline,
        "axis_outcomes": "\n".join(f"- {item}" for item in axis_outcomes),
        "trend_forces": "\n".join(f"- {force.name}: {force.direction}" for force in forces if force.type == "trend"),
    })
    narrator = Agent(name="kahn_narrator", traits={"persona": "Neutral strategic-foresight scenario writer"})
    return Jobs(survey=question.to_survey()).by(AgentList([narrator])).by(ScenarioList([scenario]))


def evaluate_options_jobs(meta: Any, options: list[Any], scenarios: list[Any], narratives: dict[str, str]) -> Any:
    Agent, AgentList, Jobs, Scenario, ScenarioList, Survey, QuestionDict, _, _ = _imports()
    questions = []
    for option in options:
        for scenario in scenarios:
            questions.append(QuestionDict(
                question_name=f"eval_{option.id}_{scenario.id}",
                question_text=(
                    "Focal question: {{ focal_question }}\n"
                    f"Strategic option: {option.name}\nDescription: {option.description}\n\n"
                    f"Scenario: {scenario.name}\nTagline: {scenario.tagline}\n"
                    f"Narrative: {narratives.get(scenario.id, '')[:1500]}\n\n"
                    "Evaluate this option in this scenario. Use robust when it performs strongly, "
                    "acceptable when viable with manageable drawbacks, or fragile when it depends on assumptions "
                    "this scenario breaks."
                ),
                answer_keys=["rating", "rationale"],
                value_types=[str, str],
                value_descriptions=[
                    "Exactly one of: robust, acceptable, fragile",
                    "One concrete sentence explaining the rating",
                ],
            ))
    execution_scenario = Scenario({
        "kahn_phase": "evaluate_options",
        "project_id": meta.id,
        "focal_question": meta.focal_question,
        "option_ids": [option.id for option in options],
        "scenario_ids": [scenario.id for scenario in scenarios],
    })
    evaluator = Agent(name="kahn_evaluator", traits={"persona": "Strategy analyst evaluating robustness under uncertainty"})
    return Jobs(survey=Survey(questions)).by(AgentList([evaluator])).by(ScenarioList([execution_scenario]))
