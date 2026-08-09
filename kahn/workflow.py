from __future__ import annotations

CHECKLISTS: dict[str, list[str]] = {
    "forces": [
        "Add 8-15 environmental forces spanning multiple PESTEL domains.",
        "Include at least 3-4 high-impact, low-predictability uncertainties.",
        "Include at least 2-3 trends.",
        "Review force list with user: `kahn force list --human`",
        "Lock and advance: `kahn phase advance`",
    ],
    "uncertainty_selection": [
        "Review uncertainty forces: `kahn force list --type uncertainty`",
        "Select 2 independent, high-impact uncertainties: `kahn uncertainty select <id1> <id2>`",
        "Set extreme poles for each: `kahn uncertainty set-poles cu001 --pole-a '...' --pole-b '...'`",
        "Run independence check: `kahn uncertainty check-independence`",
        "Review with user and lock: `kahn phase advance`",
    ],
    "scenario_construction": [
        "Build the 2x2 matrix: `kahn scenario build`",
        "Name each scenario: `kahn scenario name <id> --name '...' --tagline '...'`",
        "Write 200-400 word narrative for each: `kahn scenario narrative set <id> --text '...'`",
        "Add ≥3 early warning signals per scenario: `kahn scenario signals set <id> ...`",
        "Check consistency: `kahn scenario check-consistency`",
        "Review with user and lock: `kahn phase advance`",
    ],
    "option_evaluation": [
        "Propose 4-6 strategic options (at least one hedging option).",
        "Add them: `kahn option add --name '...' --description '...'`",
        "Evaluate each across all scenarios: `kahn option evaluate <id> --scenario sc001 --rating robust --rationale '...' ...`",
        "Review robustness ranking: `kahn option robustness-rank`",
        "Generate report: `kahn report generate`",
    ],
    "complete": [
        "Generate final report: `kahn report generate`",
        "Export for distribution: `kahn report export`",
        "Review executive summary: `kahn report show --section summary`",
    ],
}

_NEXT_STEPS: dict[str, list[dict]] = {
    "init": [
        {"label": "Initialize project", "command": "kahn init --question '...' --domain '...' --horizon '...'"},
    ],
    "forces": [
        {"label": "Add an environmental force", "command": "kahn force add --name '...' --domain technological --type uncertainty --impact high --predictability low --direction '...'"},
        {"label": "List current forces", "command": "kahn force list"},
        {"label": "Build force-research Jobs", "command": "kahn job generate research-forces"},
    ],
    "uncertainty_selection": [
        {"label": "List uncertainty forces", "command": "kahn force list --type uncertainty"},
        {"label": "Select critical uncertainties", "command": "kahn uncertainty select <id1> <id2>"},
    ],
    "scenario_construction": [
        {"label": "Build scenario matrix", "command": "kahn scenario build"},
        {"label": "List scenarios", "command": "kahn scenario list"},
        {"label": "Build narrative-writing Jobs", "command": "kahn job generate write-narrative sc001"},
    ],
    "option_evaluation": [
        {"label": "Add a strategic option", "command": "kahn option add --name '...' --description '...'"},
        {"label": "View robustness ranking", "command": "kahn option robustness-rank"},
        {"label": "Build option-evaluation Jobs", "command": "kahn job generate evaluate-options"},
    ],
    "complete": [
        {"label": "Generate report", "command": "kahn report generate"},
        {"label": "Show summary", "command": "kahn report show --section summary"},
    ],
}


def next_steps(phase: str) -> list[dict]:
    return _NEXT_STEPS.get(phase, [])


def phase_state(store) -> dict:
    if not store.meta_path.exists():
        return {
            "phase": "init",
            "project_exists": False,
            "counts": {},
            "checklist": ["Run `kahn init --question '...' --domain '...' --horizon '...'` to create the project."],
            "recommended_next_steps": next_steps("init"),
        }
    meta = store.read_meta()
    phase = meta.phase
    forces = store.list_forces()
    cus = store.list_critical_uncertainties()
    scenarios = store.list_scenarios()
    options = store.list_options()
    return {
        "phase": phase,
        "project_exists": True,
        "counts": {
            "trends": len([f for f in forces if f.type == "trend"]),
            "uncertainties": len([f for f in forces if f.type == "uncertainty"]),
            "critical_uncertainties": len(cus),
            "scenarios": len(scenarios),
            "options": len(options),
        },
        "phase_locks": meta.phase_locks,
        "checklist": CHECKLISTS.get(phase, []),
        "recommended_next_steps": next_steps(phase),
    }


def workflow_assessment(store) -> dict:
    """Return the first incomplete workflow gate based on persisted artifacts."""
    project = store.root.resolve()

    def action(
        label: str,
        args: list[str],
        *,
        input_schema: dict | None = None,
        mutates: bool = True,
        approval: bool = False,
        transition: str,
        prerequisites: list[dict] | None = None,
        alternatives: list[dict] | None = None,
    ) -> dict:
        argv = ["kahn", *args, "--project-dir", str(project)]
        return {
            "label": label,
            "argv": argv,
            "cwd": str(project),
            "project_dir": str(project),
            "input_schema": input_schema or {},
            "mutates_state": mutates,
            "requires_user_approval": approval,
            "may_spend_money": False,
            "expected_state_transition": transition,
            "prerequisites": prerequisites or [],
            "alternatives": alternatives or [],
        }

    def result(stage: str, reason: str, selected: dict, ready: bool = False) -> dict:
        return {
            "stage": stage,
            "ready": ready,
            "reason": reason,
            "action": selected,
            "next_command": " ".join(selected["argv"]),
            "guide": "kahn guide",
        }

    if not store.meta_path.exists():
        selected = action(
            "Initialize the scenario project",
            ["init"],
            input_schema={
                "question": {"type": "string", "required": True, "flag": "--question"},
                "domain": {"type": "string", "required": True, "flag": "--domain"},
                "horizon": {"type": "string", "required": True, "flag": "--horizon"},
            },
            transition="Create the project and enter the forces stage.",
        )
        return result("init", "No Kahn project exists.", selected)

    meta = store.read_meta()
    forces = store.list_forces()
    trends = [force for force in forces if force.type == "trend"]
    uncertainties = [force for force in forces if force.type == "uncertainty"]
    critical = store.list_critical_uncertainties()
    scenarios = store.list_scenarios()
    options = store.list_options()
    force_schema = {
        "name": {"type": "string", "required": True, "flag": "--name"},
        "domain": {"enum": ["political", "economic", "social", "technological", "environmental", "legal"], "required": True, "flag": "--domain"},
        "type": {"enum": ["trend", "uncertainty"], "required": True, "flag": "--type"},
        "impact": {"enum": ["low", "medium", "high"], "required": True, "flag": "--impact"},
        "predictability": {"enum": ["low", "medium", "high"], "required": True, "flag": "--predictability"},
        "direction": {"type": "string", "required": True, "flag": "--direction"},
    }
    if not forces or not trends or len(uncertainties) < 2:
        return result("forces", "Add forces until at least one trend and two uncertainties exist.", action("Add an environmental force", ["force", "add"], input_schema=force_schema, transition="Add one force and remain in forces until completeness thresholds pass."))

    def phase_action(phase: str, label: str) -> dict:
        snapshot_label = f"{phase}-reviewed"
        snapshot = store.root / "snapshots" / snapshot_label
        validation = action("Validate before milestone review", ["validate"], mutates=False, transition="Confirm project invariants before snapshotting and locking.")
        if not snapshot.exists():
            return action("Save the reviewed milestone", ["snapshot", "save", snapshot_label], prerequisites=[validation], transition=f"Preserve the {phase} state before locking it.")
        return action(label, ["phase", "advance"], approval=True, prerequisites=[validation], transition=f"Lock {phase} and enter the next phase.")

    if "forces" not in meta.phase_locks:
        return result("forces", "Review, snapshot, and lock the force set.", phase_action("forces", "Approve and lock the force set"))
    if len(critical) != 2:
        schema = {"force_id_a": {"enum": [item.id for item in uncertainties], "required": True, "position": 1}, "force_id_b": {"enum": [item.id for item in uncertainties], "required": True, "position": 2}}
        return result("uncertainty_selection", "Select exactly two critical uncertainties.", action("Select the two scenario axes", ["uncertainty", "select"], input_schema=schema, transition="Create two critical-uncertainty records."))
    incomplete_poles = next((item for item in critical if not item.pole_a or not item.pole_b), None)
    if incomplete_poles:
        schema = {"pole_a": {"type": "string", "required": True, "flag": "--pole-a"}, "pole_b": {"type": "string", "required": True, "flag": "--pole-b"}}
        return result("uncertainty_selection", f"{incomplete_poles.id} needs two poles.", action("Define uncertainty poles", ["uncertainty", "set-poles", incomplete_poles.id], input_schema=schema, transition=f"Complete poles for {incomplete_poles.id}."))
    if "Independence check run." not in (meta.notes or ""):
        return result("uncertainty_selection", "Run the independence check for the selected axes.", action("Check axis independence", ["uncertainty", "check-independence"], mutates=True, transition="Record the independence review."))
    if "uncertainty_selection" not in meta.phase_locks:
        return result("uncertainty_selection", "Review, snapshot, and lock the selected axes.", phase_action("uncertainty_selection", "Approve and lock the selected axes"))
    if len(scenarios) != 4:
        return result("scenario_construction", "Build the four-scenario matrix.", action("Build the scenario matrix", ["scenario", "build"], transition="Create four scenario records."))
    unnamed = next((item for item in scenarios if not item.name or not item.tagline), None)
    if unnamed:
        schema = {"name": {"type": "string", "required": True, "flag": "--name"}, "tagline": {"type": "string", "required": True, "flag": "--tagline"}}
        return result("scenario_construction", f"{unnamed.id} needs a name and tagline.", action("Name the scenario", ["scenario", "name", unnamed.id], input_schema=schema, transition=f"Name {unnamed.id}."))
    missing_narrative = next((item for item in scenarios if not store.get_scenario_narrative(item.id).strip()), None)
    if missing_narrative:
        jobs_path = (project / "jobs" / f"narrative-{missing_narrative.id}.jobs.ep").resolve()
        alternative = action("Generate narrative-writing Jobs", ["job", "generate", "write-narrative", missing_narrative.id, "--output", str(jobs_path)], transition="Create a model-free Jobs package; remote execution remains approval-gated.")
        schema = {"text": {"type": "string", "required": True, "flag": "--text"}}
        return result("scenario_construction", f"{missing_narrative.id} needs a narrative.", action("Set the scenario narrative", ["scenario", "narrative", "set", missing_narrative.id], input_schema=schema, transition=f"Store the narrative for {missing_narrative.id}.", alternatives=[alternative]))
    signal_scenario = next((item for item in scenarios if len(store.get_scenario_signals(item.id).signals) < 3), None)
    if signal_scenario:
        observed = len(store.get_scenario_signals(signal_scenario.id).signals)
        schema = {"description": {"type": "string", "required": True, "flag": "--description"}, "observable_in": {"type": "string", "required": True, "flag": "--observable-in"}}
        return result("scenario_construction", f"{signal_scenario.id} has {observed} of 3 required signals.", action("Add an early-warning signal", ["scenario", "signals", "add", signal_scenario.id], input_schema=schema, transition=f"Add one signal to {signal_scenario.id}; {2 - observed} will remain afterward."))
    if "scenario_construction" not in meta.phase_locks:
        return result("scenario_construction", "Review, snapshot, and lock the scenarios.", phase_action("scenario_construction", "Approve and lock the scenarios"))
    if not options:
        schema = {"name": {"type": "string", "required": True, "flag": "--name"}, "description": {"type": "string", "required": True, "flag": "--description"}, "hedging": {"type": "boolean", "required": False, "flag": "--hedging"}}
        return result("option_evaluation", "Add at least one strategic option.", action("Add a strategic option", ["option", "add"], input_schema=schema, transition="Add one option for cross-scenario evaluation."))
    unevaluated = next((item for item in options if not (store.option_dir(item.id) / "performance.json").exists()), None)
    if unevaluated:
        jobs_path = (project / "jobs" / "evaluate-options.jobs.ep").resolve()
        return result("option_evaluation", f"{unevaluated.id} needs cross-scenario evaluation.", action("Generate option-evaluation Jobs", ["job", "generate", "evaluate-options", "--output", str(jobs_path)], transition="Create a model-free Jobs package; inspect and cost it before approval-gated execution."))
    if not (store.root / "output" / "summary.md").exists():
        return result("reporting", "Generate the final report.", action("Generate the final report", ["report", "generate"], prerequisites=[action("Validate the complete project", ["validate"], mutates=False, transition="Confirm report prerequisites.")], transition="Write the report artifact bundle."))
    return result("complete", "All workflow artifacts are present.", action("Validate the completed project", ["validate"], mutates=False, transition="Confirm the completed project remains valid."), ready=True)
