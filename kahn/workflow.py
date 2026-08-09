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
    if not store.meta_path.exists():
        return {"stage": "init", "ready": False, "reason": "No Kahn project exists.", "next_command": "kahn init --question '...' --domain '...' --horizon '...'", "guide": "kahn guide"}

    meta = store.read_meta()
    forces = store.list_forces()
    trends = [force for force in forces if force.type == "trend"]
    uncertainties = [force for force in forces if force.type == "uncertainty"]
    critical = store.list_critical_uncertainties()
    scenarios = store.list_scenarios()
    options = store.list_options()
    gates = [
        (not forces, "forces", "No environmental forces have been recorded.", "kahn force add --help"),
        (not trends, "forces", "At least one relatively predictable trend is required.", "kahn force add --help"),
        (len(uncertainties) < 2, "forces", "At least two uncertain forces are required.", "kahn force add --help"),
        ("forces" not in meta.phase_locks, "forces", "Review and lock the force set.", "kahn phase advance"),
        (len(critical) != 2, "uncertainty_selection", "Select exactly two critical uncertainties.", "kahn uncertainty select --help"),
        (any(not item.pole_a or not item.pole_b for item in critical), "uncertainty_selection", "Both critical uncertainties need poles.", "kahn uncertainty set-poles --help"),
        ("Independence check run." not in (meta.notes or ""), "uncertainty_selection", "Run the independence check for the selected axes.", "kahn uncertainty check-independence"),
        ("uncertainty_selection" not in meta.phase_locks, "uncertainty_selection", "Review and lock the selected axes.", "kahn phase advance"),
        (len(scenarios) != 4, "scenario_construction", "Build the four-scenario matrix.", "kahn scenario build"),
        (any(not item.name or not item.tagline for item in scenarios), "scenario_construction", "Every scenario needs a name and tagline.", "kahn scenario name --help"),
        (any(not store.get_scenario_narrative(item.id).strip() for item in scenarios), "scenario_construction", "Every scenario needs a narrative.", "kahn job generate write-narrative --help"),
        (any(not store.get_scenario_signals(item.id).signals for item in scenarios), "scenario_construction", "Every scenario needs early-warning signals.", "kahn scenario signals set --help"),
        ("scenario_construction" not in meta.phase_locks, "scenario_construction", "Review and lock the scenario set.", "kahn phase advance"),
        (not options, "option_evaluation", "Add at least one strategic option.", "kahn option add --help"),
        (any(not (store.option_dir(item.id) / "performance.json").exists() for item in options), "option_evaluation", "Every option needs a cross-scenario evaluation.", "kahn job generate evaluate-options"),
        (not (store.root / "output" / "summary.md").exists(), "reporting", "Generate the final report.", "kahn report generate"),
    ]
    for incomplete, stage, reason, command in gates:
        if incomplete:
            return {"stage": stage, "ready": False, "reason": reason, "next_command": command, "guide": "kahn guide"}
    return {"stage": "complete", "ready": True, "reason": "All workflow artifacts are present.", "next_command": "kahn validate", "guide": "kahn guide"}
