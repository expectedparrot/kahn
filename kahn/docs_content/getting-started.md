# Getting Started with kahn

This guide walks through a complete scenario planning exercise from initialization to report.

## Installation

```bash
pip install git+https://github.com/expectedparrot/kahn.git
kahn --help
```

## Step 0: Bootstrap (for agents)

If you are an agent starting a new session, run this first:

```bash
kahn status --project-dir <path>
```

This returns your operating rules, the current project state, and recommended next steps in a single JSON payload.

## Step 1: Initialize the Project

```bash
kahn init \
  --question "What is the future of university education in an AI-powered world?" \
  --domain "higher education" \
  --horizon "10-15 years" \
  --id "2026-future-of-universities" \
  --project-dir ./my_project
```

This creates the project directory and sets the phase to `forces`.

Check your starting state:

```bash
kahn status --project-dir ./my_project
```

## Step 2: Add Environmental Forces (Phase 1)

Identify 8-15 forces spanning multiple PESTEL domains. You need at least:
- 2-3 trends (predictable direction)
- 3-4 uncertainties (high-impact, low-predictability)

```bash
kahn force add \
  --name "Foundation model capability improving exponentially" \
  --domain technological \
  --type trend \
  --impact high \
  --predictability high \
  --direction "AI capability per dollar is doubling annually, commoditizing specialized NLP" \
  --project-dir ./my_project

kahn force add \
  --name "Government regulation of AI in education" \
  --domain political \
  --type uncertainty \
  --impact high \
  --predictability low \
  --direction "Could range from strict accreditation requirements to hands-off permissiveness" \
  --project-dir ./my_project
```

To build and run a portable EDSL Jobs package that identifies forces:

```bash
kahn job generate research-forces --output jobs/research-forces.jobs.ep --project-dir ./my_project
ep run jobs/research-forces.jobs.ep --model <model-name> --output jobs/research-forces-results.ep
kahn ingest forces --from jobs/research-forces-results.ep --project-dir ./my_project
python my_project/scripts/research_forces.py
```

Review the force inventory:

```bash
kahn force list --project-dir ./my_project
kahn force list --type uncertainty --project-dir ./my_project
```

When ready, lock this phase:

```bash
kahn phase advance --project-dir ./my_project
```

## Step 3: Select Critical Uncertainties (Phase 2)

Pick the 2 forces that are most impactful and most independent of each other.
First, list forces to find the IDs of your chosen uncertainties:

```bash
kahn force list --type uncertainty --project-dir ./my_project
```

IDs are assigned sequentially (e.g. `f001`, `f002`, …) and shown in the `ID` column.
Then select the two you want:

```bash
kahn uncertainty select f003 f007 --project-dir ./my_project
```

Set extreme-but-plausible poles for each:

```bash
kahn uncertainty set-poles cu001 \
  --pole-a "Strict federal regulation caps AI use in credentialed programs" \
  --pole-b "Fully permissive: AI tutors replace instructors with no oversight" \
  --project-dir ./my_project

kahn uncertainty set-poles cu002 \
  --pole-a "Public trust in institutions collapses; credentials lose value" \
  --pole-b "Public trust in institutions surges; degrees command premium" \
  --project-dir ./my_project
```

Run the independence check:

```bash
kahn uncertainty check-independence --project-dir ./my_project
```

Lock and advance:

```bash
kahn phase advance --project-dir ./my_project
```

## Step 4: Build Scenarios (Phase 3)

```bash
kahn scenario build --project-dir ./my_project
kahn scenario list --project-dir ./my_project
```

Name each scenario with an evocative, memorable title:

```bash
kahn scenario name sc001 \
  --name "The Fortress Academy" \
  --tagline "Regulation walls off AI; credentials still rule" \
  --project-dir ./my_project
```

Write a 200-400 word narrative for each (or generate and ingest it with EDSL):

```bash
kahn job generate write-narrative sc001 --output jobs/narrative-sc001.jobs.ep --project-dir ./my_project
ep run jobs/narrative-sc001.jobs.ep --model <model-name> --output jobs/narrative-sc001-results.ep
kahn ingest narrative sc001 --from jobs/narrative-sc001-results.ep --project-dir ./my_project
# edit the script, run it, then:
kahn scenario narrative set sc001 --file ./narrative_sc001.md --project-dir ./my_project
```

Add early warning signals:

```bash
kahn scenario signals set sc001 \
  --signal "EU announces binding AI-in-education regulations" --observable-in "EU Official Journal" \
  --signal "3+ accreditors explicitly prohibit AI-generated assessments" --observable-in "CHEA database" \
  --signal "Top-20 university bans AI submission tools campus-wide" --observable-in "Chronicle of Higher Ed" \
  --project-dir ./my_project
```

Check consistency and lock:

```bash
kahn scenario check-consistency --project-dir ./my_project
kahn phase advance --project-dir ./my_project
```

## Step 5: Evaluate Strategic Options (Phase 4)

Propose 4-6 options spanning conservative, aggressive, and hedging postures:

```bash
kahn option add \
  --name "AI-Native Curriculum Overhaul" \
  --description "Rebuild all degree programs with AI tools as core infrastructure" \
  --project-dir ./my_project

kahn option add \
  --name "Credential Hedging" \
  --description "Maintain traditional programs while piloting AI-enhanced micro-credentials" \
  --hedging \
  --project-dir ./my_project
```

Evaluate each option across all 4 scenarios:

```bash
kahn option evaluate op001 \
  --scenario sc001 --rating fragile --rationale "Regulations block AI-native programs" \
  --scenario sc002 --rating robust --rationale "AI-native approach thrives in permissive environment" \
  --scenario sc003 --rating acceptable --rationale "Low trust reduces value but doesn't kill the program" \
  --scenario sc004 --rating robust --rationale "Strong trust + AI capability = strong differentiator" \
  --project-dir ./my_project
```

View the robustness ranking:

```bash
kahn option robustness-rank --project-dir ./my_project
```

## Step 6: Generate Report

```bash
kahn report generate --project-dir ./my_project
kahn report show --section summary --project-dir ./my_project
kahn report export --format json --output report.json --project-dir ./my_project
```

## Next Steps

- `kahn docs show workflow` — detailed phase reference
- `kahn docs show best-practices` — quality standards and common pitfalls
- `kahn docs show cli-reference` — full command syntax
