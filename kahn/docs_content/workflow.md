# Workflow Phases

kahn implements Herman Kahn's structured scenario planning method as five sequential phases. Each phase must be locked before the next can begin.

## Phase Flow

```
forces → uncertainty_selection → scenario_construction → option_evaluation → complete
```

Phase locks are **irreversible**. Always run `kahn snapshot save <label>` before locking a phase.

---

## Phase 0: Initialization

Before any phase begins, initialize the project with a focal question.

**Required inputs:**
- `--question` — the central strategic question (specific, actionable, time-bounded)
- `--domain` — the industry or organization context
- `--horizon` — the planning time horizon (e.g. "10-15 years")

**Command:**
```bash
kahn init --question "..." --domain "..." --horizon "..." --project-dir <dir>
```

**Good focal questions:**
- "What is the future of clinical trial design in an AI-powered regulatory environment?"
- "How will the global semiconductor supply chain evolve over the next 15 years?"

**Weak focal questions:**
- "What will the future look like?" (too vague)
- "Should we invest in AI?" (too narrow; a strategy, not a question)

---

## Phase 1: Forces (Environmental Scanning)

**Goal:** Catalog 8-15 forces acting on the focal domain from the outside.

**Requirements to lock:**
- At least 2 uncertainty forces
- At least 1 trend force

**Quality targets:**
- 8-15 forces total
- At least 3 PESTEL domains represented
- 3-4+ high-impact, low-predictability uncertainties
- 2-3 trends (directional, predictable forces)

**Key commands:**
```bash
kahn force add --name "..." --domain <pestel> --type <trend|uncertainty> \
               --impact <low|medium|high> --predictability <low|medium|high> \
               --direction "..." --project-dir <dir>
kahn force list --project-dir <dir>
kahn force list --type uncertainty --project-dir <dir>
kahn force edit <id> --name "..." --project-dir <dir>
kahn force delete <id> --confirm --project-dir <dir>
```

**Generate AI-assisted force research:**
```bash
kahn job generate research-forces --output jobs/research-forces.jobs.ep --project-dir <dir>
ep run jobs/research-forces.jobs.ep --model <model-name> --output jobs/research-forces-results.ep
kahn ingest forces --from jobs/research-forces-results.ep --project-dir <dir>
python <dir>/scripts/research_forces.py
```

**Lock:**
```bash
kahn snapshot save pre-phase2 --project-dir <dir>
kahn phase advance --project-dir <dir>
```

---

## Phase 2: Critical Uncertainty Selection

**Goal:** Select the 2 forces that will form the axes of the 2×2 scenario matrix.

**Selection criteria:**
- High impact (essential: things hinge on how they resolve)
- Low predictability (genuinely uncertain: neither pole is obviously more likely)
- Logically independent (resolution of one does not imply resolution of the other)

**Requirements to lock:**
- Exactly 2 critical uncertainties exist
- Both have pole_a and pole_b set
- Independence check has been run

**Key commands:**
```bash
kahn force list --type uncertainty --project-dir <dir>
kahn uncertainty select <force_id_1> <force_id_2> --project-dir <dir>
kahn uncertainty set-poles cu001 --pole-a "..." --pole-b "..." --project-dir <dir>
kahn uncertainty set-poles cu002 --pole-a "..." --pole-b "..." --project-dir <dir>
kahn uncertainty check-independence --project-dir <dir>
kahn uncertainty list --project-dir <dir>
```

**Pole guidelines:**
- Extreme but plausible — not a mild variation
- Value-neutral — avoid "success" vs. "failure" framing
- Specific — name concrete conditions, not abstract states

**Lock:**
```bash
kahn snapshot save pre-phase3 --project-dir <dir>
kahn phase advance --project-dir <dir>
```

---

## Phase 3: Scenario Construction

**Goal:** Build 4 vivid, internally consistent scenarios from the 2×2 matrix.

The 4 scenarios map to the quadrants:
- sc001: cu001 pole_a × cu002 pole_a
- sc002: cu001 pole_a × cu002 pole_b
- sc003: cu001 pole_b × cu002 pole_a
- sc004: cu001 pole_b × cu002 pole_b

**Requirements to lock:**
- `kahn scenario build` has been run
- Every scenario has a name, tagline, non-empty narrative, and ≥1 signal set

**Key commands:**
```bash
kahn scenario build --project-dir <dir>
kahn scenario list --project-dir <dir>
kahn scenario name sc001 --name "..." --tagline "..." --project-dir <dir>
kahn scenario narrative set sc001 --text "..." --project-dir <dir>
kahn scenario narrative set sc001 --file narrative.md --project-dir <dir>
kahn scenario signals set sc001 \
  --signal "..." --observable-in "..." \
  --signal "..." --observable-in "..." \
  --project-dir <dir>
kahn scenario check-consistency --project-dir <dir>
```

**Generate AI-assisted narratives:**
```bash
kahn job generate write-narrative sc001 --output jobs/narrative-sc001.jobs.ep --project-dir <dir>
ep run jobs/narrative-sc001.jobs.ep --model <model-name> --output jobs/narrative-sc001-results.ep
kahn ingest narrative sc001 --from jobs/narrative-sc001-results.ep --project-dir <dir>
python <dir>/scripts/write_narrative_sc001.py
```

**Narrative quality:**
- Written in present tense ("It is 2040. Universities operate…")
- 200-400 words; tells a story, not a bullet list
- Internally consistent with its axis positions
- Includes all trend forces (predetermined elements appear in every scenario)
- Contains both opportunities and threats
- Distinct enough that a reader can tell them apart

**Lock:**
```bash
kahn snapshot save pre-phase4 --project-dir <dir>
kahn phase advance --project-dir <dir>
```

---

## Phase 4: Option Evaluation

**Goal:** Identify strategic options and stress-test each against all 4 scenarios.

**Design criteria for options:**
- 4-6 options total
- At least one hedging option (flexible, preserves future choices)
- At least one bold bet
- Options should represent genuinely different strategic postures

**Rating scale:**
- `robust` — option thrives in this scenario
- `acceptable` — option survives; not optimal but doesn't fail
- `fragile` — option backfires; core assumptions contradicted

**Key commands:**
```bash
kahn option add --name "..." --description "..." [--hedging] --project-dir <dir>
kahn option list --project-dir <dir>
kahn option evaluate op001 \
  --scenario sc001 --rating robust --rationale "..." \
  --scenario sc002 --rating acceptable --rationale "..." \
  --scenario sc003 --rating fragile --rationale "..." \
  --scenario sc004 --rating robust --rationale "..." \
  --project-dir <dir>
kahn option robustness-rank --project-dir <dir>
kahn option evaluate-all --project-dir <dir>
```

**Robustness score interpretation:**
- Score > 0.75: Highly robust — strong core strategy candidate
- Score 0.50-0.75: Moderately robust — viable with hedging
- Score < 0.50: Fragile overall — only pursue with strong scenario conviction

**Report:**
```bash
kahn report generate --project-dir <dir>
kahn report show --section summary --project-dir <dir>
kahn report show --section recommendations --project-dir <dir>
kahn report show --section signals --project-dir <dir>
```

---

## Utilities (any phase)

```bash
kahn validate --project-dir <dir>              # full referential integrity check
kahn snapshot save <label> --project-dir <dir> # checkpoint before risky operations
kahn snapshot list --project-dir <dir>
kahn snapshot restore <label> --confirm --project-dir <dir>
kahn phase status --project-dir <dir>
```

## Next Steps

- `kahn docs show best-practices` — quality standards and common pitfalls
- `kahn docs show cli-reference` — full command syntax reference
