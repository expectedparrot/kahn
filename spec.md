# `kahn` — Strategic Scenario Planning CLI
## Full Technical Specification

Named after Herman Kahn (1922–1983), RAND futurist, pioneer of scenario-based strategic thinking,
and intellectual forefather of modern scenario planning.

---

## Overview

`kahn` is a Python-based CLI tool for structured strategic scenario planning. It manages a
filesystem-based project store, enforces phase discipline, and exposes a command surface designed
to be called by both humans and LM agents. All state is durable JSON/Markdown on disk. The tool
is stateless between invocations — no daemon, no database.

---

## Installation & Entrypoint

```
pip install kahn
```

Entrypoint: `kahn`  
Python version: 3.11+  
Dependencies: `typer`, `rich`, `pydantic`, `jinja2`

Primary library choices:
- **typer** — CLI framework, supports subcommand groups cleanly
- **rich** — terminal output (tables, markdown rendering, status indicators)
- **pydantic** — schema validation for all JSON files on read/write
- **jinja2** — narrative and report templating

---

## Project Storage

Every `kahn` project lives in a directory. By default this is `./kahn_project/` but can be
overridden with `--project-dir` on any command or the env var `KAHN_PROJECT_DIR`.

### Directory Structure

```
kahn_project/
│
├── meta.json
│
├── forces/
│   ├── trends/
│   │   └── {id}.json
│   └── uncertainties/
│       └── {id}.json
│
├── critical_uncertainties/
│   └── {id}.json
│
├── scenarios/
│   └── {id}/
│       ├── meta.json
│       ├── narrative.md
│       └── signals.json
│
├── strategic_options/
│   └── {id}/
│       ├── meta.json
│       └── performance.json
│
├── snapshots/
│   └── {label}/          # copies of full project state
│
└── output/
    ├── summary.md
    ├── strategy_matrix.json
    ├── robust_recommendations.md
    └── signal_dashboard.json
```

### ID Format

All entities use short, sequential, prefixed IDs:
- Forces: `f001`, `f002`, ...
- Critical uncertainties: `cu001`, `cu002`
- Scenarios: `sc001`, `sc002`, ...
- Strategic options: `op001`, `op002`, ...

IDs are assigned by the tool on creation and never change.

---

## Schema Definitions

All files are validated against Pydantic models on read and write. Invalid files produce a clear
error message identifying the file and field.

### `meta.json`

```json
{
  "id": "string",
  "focal_question": "string",
  "domain": "string",
  "horizon": "string",
  "created_at": "ISO date string",
  "updated_at": "ISO date string",
  "phase": "forces | uncertainty_selection | scenario_construction | option_evaluation | complete",
  "phase_locks": ["forces", "uncertainty_selection"],
  "notes": "string (optional)"
}
```

**Phases in order:**
1. `forces` — adding and classifying environmental forces
2. `uncertainty_selection` — selecting and defining critical uncertainties
3. `scenario_construction` — building scenario matrix and narratives
4. `option_evaluation` — stress-testing strategic options
5. `complete` — output generated, project closed

Phase locks are cumulative. Locking `scenario_construction` also locks all prior phases.

---

### `forces/{type}/{id}.json`

```json
{
  "id": "f001",
  "name": "string",
  "domain": "political | economic | social | technological | environmental | legal",
  "type": "trend | uncertainty",
  "direction": "string — what this force is doing or could do",
  "impact_magnitude": "low | medium | high",
  "predictability": "low | medium | high",
  "created_at": "ISO date string",
  "notes": "string (optional)"
}
```

---

### `critical_uncertainties/{id}.json`

```json
{
  "id": "cu001",
  "source_force_id": "f003",
  "name": "string",
  "description": "string",
  "pole_a": "string — one extreme of how this resolves",
  "pole_b": "string — opposite extreme",
  "independence_note": "string — reasoning that these axes are independent",
  "created_at": "ISO date string"
}
```

Exactly 2 critical uncertainties must exist before scenario construction can begin.

---

### `scenarios/{id}/meta.json`

```json
{
  "id": "sc001",
  "name": "string — evocative, memorable",
  "tagline": "string — one sentence",
  "axis": {
    "cu001": "pole_a | pole_b",
    "cu002": "pole_a | pole_b"
  },
  "predetermined_element_ids": ["f001", "f002"],
  "internal_consistency_score": 0.87,
  "consistency_notes": "string (optional)",
  "created_at": "ISO date string",
  "updated_at": "ISO date string"
}
```

### `scenarios/{id}/narrative.md`

Free-form Markdown. Minimum 100 words. Should read as a vivid story, not a bullet list.
The tool does not enforce style but warns if the file is below minimum length.

### `scenarios/{id}/signals.json`

```json
{
  "scenario_id": "sc001",
  "signals": [
    {
      "id": "sig001",
      "description": "string — an observable indicator this scenario is emerging",
      "observable_in": "string — where/how you'd see this signal"
    }
  ]
}
```

Minimum 3 signals per scenario. The tool warns if fewer exist at output generation.

---

### `strategic_options/{id}/meta.json`

```json
{
  "id": "op001",
  "name": "string",
  "description": "string",
  "hedging_value": true,
  "created_at": "ISO date string",
  "notes": "string (optional)"
}
```

### `strategic_options/{id}/performance.json`

```json
{
  "option_id": "op001",
  "evaluations": {
    "sc001": {
      "rating": "robust | acceptable | fragile",
      "rationale": "string"
    },
    "sc002": {
      "rating": "robust | acceptable | fragile",
      "rationale": "string"
    }
  },
  "robustness_score": 0.71,
  "evaluated_at": "ISO date string"
}
```

`robustness_score` is computed by the tool: robust=1.0, acceptable=0.5, fragile=0.0, averaged
across all evaluated scenarios.

---

## Command Reference

All commands support:
- `--project-dir PATH` — override default project directory
- `--json` — output machine-readable JSON instead of rich terminal output (for agent use)
- `--quiet` — suppress all output except errors

---

### `kahn init`

Initialize a new project.

```
kahn init [OPTIONS]
```

**Options:**
```
--question TEXT     The focal strategic question  [required]
--domain TEXT       Industry or organizational domain  [required]
--horizon TEXT      Planning horizon (e.g. "5 years")  [required]
--id TEXT           Project ID (auto-generated if omitted)
--notes TEXT        Optional context notes
--project-dir PATH  Where to create the project (default: ./kahn_project)
```

**Behavior:**
- Creates directory structure
- Writes `meta.json` with phase=`forces`
- Fails if directory already exists unless `--force` passed

**Output:**
```
✓ Project initialized: sp_2024_001
  Focal question: How should we structure our GTM over 5 years?
  Domain: B2B SaaS | Horizon: 5 years
  Next step: kahn force add
```

---

### `kahn status`

Show current project state.

```
kahn status
```

**Output:** A rich summary panel showing:
- Project ID, focal question, domain, horizon
- Current phase and phase locks
- Count of forces (trends / uncertainties)
- Count of critical uncertainties (and whether poles are set)
- Count of scenarios (and which have narratives / signals)
- Count of strategic options (and which have been evaluated)
- Next recommended action

---

### `kahn force`

Subcommand group for managing environmental forces.

#### `kahn force add`

```
kahn force add [OPTIONS]
```

**Options:**
```
--name TEXT              [required]
--domain [political|economic|social|technological|environmental|legal]  [required]
--type [trend|uncertainty]  [required]
--impact [low|medium|high]  [required]
--predictability [low|medium|high]  [required]
--direction TEXT         What this force is doing or could do  [required]
--notes TEXT
```

**Behavior:**
- Blocked if `forces` phase is locked
- Assigns next available ID (f001, f002, ...)
- Writes to `forces/trends/` or `forces/uncertainties/` based on `--type`

**Output:**
```
✓ Force added: f003
  AI commoditization of core features [technological | uncertainty]
  Impact: high | Predictability: low
```

#### `kahn force list`

```
kahn force list [--type trend|uncertainty] [--impact low|medium|high] [--domain TEXT]
```

Prints a rich table of all forces, filtered by any combination of options.

#### `kahn force show <id>`

```
kahn force show f003
```

Pretty-prints the full force record.

#### `kahn force edit <id>`

```
kahn force edit f003 [--name TEXT] [--impact low|medium|high] [--predictability low|medium|high]
                     [--direction TEXT] [--notes TEXT]
```

Updates any field. Blocked if `forces` phase is locked.

#### `kahn force delete <id>`

```
kahn force delete f003 [--confirm]
```

Deletes the force file. Warns if the force is referenced as a source by a critical uncertainty.
Blocked if `forces` phase is locked. Requires `--confirm` flag.

---

### `kahn uncertainty`

Subcommand group for critical uncertainties.

#### `kahn uncertainty select <force_id> <force_id>`

```
kahn uncertainty select f003 f007
```

**Behavior:**
- Both forces must exist and have `type=uncertainty` and `impact=high`
- Warns (but does not block) if predictability is not `low`
- Creates `critical_uncertainties/cu001.json` and `cu002.json` as stubs
- Sets `source_force_id` on each
- Blocked if `uncertainty_selection` phase is locked

**Output:**
```
✓ Critical uncertainties selected:
  cu001 ← f003 (AI commoditization of core features)
  cu002 ← f007 (Regulatory fragmentation)

  Next step: kahn uncertainty set-poles cu001 --pole-a "..." --pole-b "..."
```

#### `kahn uncertainty set-poles <id>`

```
kahn uncertainty set-poles cu001 \
  --pole-a "Features fully commoditized — competition shifts to distribution and brand" \
  --pole-b "AI creates new capability tiers — early movers establish durable technical leads"
```

Updates `pole_a` and `pole_b` on the critical uncertainty. Blocked if phase is locked.

#### `kahn uncertainty list`

Prints both critical uncertainties with their poles.

#### `kahn uncertainty show <id>`

Full record for one critical uncertainty.

#### `kahn uncertainty check-independence`

```
kahn uncertainty check-independence
```

**Behavior:**
- Reads both critical uncertainties
- Runs a logical check: "If cu001 resolves to pole_a, does that make pole_a or pole_b of cu002
  more likely?"
- Outputs a plain-language independence assessment and a warning if correlation is detected
- Does not block — this is an advisory check
- Designed to be called by an agent before proceeding to scenario construction

**Output:**
```
Independence Check
──────────────────
cu001 × cu002:
  Assessing: "AI commoditization" vs "Regulatory fragmentation"
  
  ⚠ Possible correlation detected:
    If AI commoditizes features (cu001 pole_a), regulatory pressure on AI may
    increase, making cu002 pole_a (fragmentation) more likely.
    Consider whether these are truly independent axes or whether a different
    second uncertainty would be more orthogonal.
```

---

### `kahn scenario`

Subcommand group for scenario management.

#### `kahn scenario build`

```
kahn scenario build
```

**Behavior:**
- Requires exactly 2 critical uncertainties with poles set
- Requires `uncertainty_selection` phase lock (enforces separation)
- Constructs 2×2 matrix: creates 4 scenario stub directories
- Assigns IDs sc001–sc004
- Names each quadrant by axis position (e.g. "cu001:pole_a × cu002:pole_b")
- Does NOT generate narratives — stubs only
- Sets predetermined_element_ids from all `type=trend` forces

**Output:**
```
✓ Scenario matrix built: 4 scenarios created

  sc001: [cu001: pole_a] × [cu002: pole_a]  → narrative pending
  sc002: [cu001: pole_a] × [cu002: pole_b]  → narrative pending
  sc003: [cu001: pole_b] × [cu002: pole_a]  → narrative pending
  sc004: [cu001: pole_b] × [cu002: pole_b]  → narrative pending

  Next step: kahn scenario name sc001 --name "..." --tagline "..."
```

#### `kahn scenario name <id>`

```
kahn scenario name sc001 --name "The Platform Wars" --tagline "Commoditized features, fragmented regulation"
```

Sets the evocative name and tagline on a scenario. Can be called by agent or human.

#### `kahn scenario narrative set <id>`

```
kahn scenario narrative set sc001 --file narrative.md
kahn scenario narrative set sc001 --text "In this world..."
```

Writes or replaces `scenarios/sc001/narrative.md`. Warns if under 100 words.

#### `kahn scenario narrative show <id>`

```
kahn scenario narrative show sc001
```

Renders `narrative.md` to terminal using rich Markdown rendering.

#### `kahn scenario signals set <id>`

```
kahn scenario signals set sc001 \
  --signal "Incumbent SaaS vendors begin dropping feature pricing tiers" \
    --observable-in "Pricing pages, earnings calls" \
  --signal "VC funding shifts from feature startups to distribution plays" \
    --observable-in "Crunchbase, pitch deck themes"
```

Replaces `signals.json` for the scenario. Multiple `--signal / --observable-in` pairs allowed.

#### `kahn scenario signals show <id>`

Prints signals table for a scenario.

#### `kahn scenario list`

Prints all scenarios: ID, name, tagline, axis positions, narrative status, signal count.

#### `kahn scenario show <id>`

Full record: meta + narrative + signals rendered to terminal.

#### `kahn scenario check-consistency`

```
kahn scenario check-consistency [--scenario <id>]
```

**Behavior:**
- Without `--scenario`: checks all scenarios
  - Internal consistency: does the narrative contradict the axis positions or predetermined elements?
  - Pairwise similarity: are any two scenarios too similar to be meaningfully distinct?
- With `--scenario`: checks only that scenario for internal consistency
- Writes `internal_consistency_score` to each scenario's meta.json
- Advisory only — does not block

**Output:**
```
Consistency Check
─────────────────
sc001 (The Platform Wars)       internal consistency: 0.91  ✓
sc002 (The Capability Race)     internal consistency: 0.84  ✓
sc003 (Regulated Moats)         internal consistency: 0.62  ⚠ review narrative
sc004 (Fragmented Innovation)   internal consistency: 0.88  ✓

Pairwise similarity:
  sc001 × sc002: low similarity   ✓
  sc001 × sc003: medium similarity ⚠ consider differentiating
  sc002 × sc004: low similarity   ✓
```

---

### `kahn phase`

Phase management commands.

#### `kahn phase status`

Shows current phase and what is locked.

#### `kahn phase lock <phase>`

```
kahn phase lock forces
kahn phase lock uncertainty_selection
kahn phase lock scenario_construction
```

**Behavior:**
- Locks the specified phase and all prior phases
- Runs a pre-lock validation check:
  - `forces`: at least 2 uncertainties and 1 trend exist
  - `uncertainty_selection`: both CUs have poles set; independence check has been run
  - `scenario_construction`: all scenarios have names, narratives, and signals
- Fails with explanation if validation fails
- Appends phase name to `meta.json phase_locks` array
- Irreversible (no unlock command) — use snapshots to recover

**Output:**
```
✓ Phase locked: scenario_construction
  Forces, uncertainty selection, and scenario construction are now immutable.
  
  Next step: kahn option add
```

#### `kahn phase advance`

```
kahn phase advance
```

Convenience command. Runs pre-lock validation for the current phase, locks it if valid,
and advances `meta.json phase` to the next phase. Recommended for agent use.

---

### `kahn option`

Subcommand group for strategic options.

#### `kahn option add`

```
kahn option add --name TEXT --description TEXT [--hedging] [--notes TEXT]
```

**Behavior:**
- Blocked until `scenario_construction` phase is locked (enforces separation)
- Assigns next available ID (op001, op002, ...)
- Writes `strategic_options/op001/meta.json`

#### `kahn option list`

Prints all options: ID, name, hedging flag, evaluation status.

#### `kahn option show <id>`

Full record including performance if evaluated.

#### `kahn option evaluate <id>`

```
kahn option evaluate op001 \
  --scenario sc001 --rating robust --rationale "Distribution advantages compound in commoditized markets" \
  --scenario sc002 --rating fragile --rationale "Collapses if technical differentiation matters" \
  --scenario sc003 --rating acceptable --rationale "Regulatory moats partially substitute for feature moats" \
  --scenario sc004 --rating robust --rationale "Brand still wins in fragmented markets"
```

Multiple `--scenario / --rating / --rationale` triplets in one call.
Computes and writes `robustness_score`. Blocked if `scenario_construction` is not locked.

#### `kahn option evaluate-all`

Prints a table of all options × all scenarios with current ratings. Shows gaps (unevaluated pairs).

#### `kahn option robustness-rank`

```
kahn option robustness-rank
```

**Output:**
```
Strategic Option Robustness Ranking
─────────────────────────────────────
Rank  ID     Name                              Score   Fragile?  Hedging?
 1    op003  Invest in distribution moats      0.88    no        no
 2    op001  Enterprise vertical integration   0.71    YES       no
 3    op002  Platform/API-first pivot          0.63    no        yes
 4    op004  Acqui-hire AI capability          0.38    YES       no

⚠ Fragile options: op001, op004 — each has at least one scenario where performance = fragile
✓ Hedging options: op002 — preserves flexibility regardless of scenario
```

---

### `kahn report`

Output generation commands.

#### `kahn report generate`

```
kahn report generate [--force]
```

**Behavior:**
- Requires `option_evaluation` phase to be current (all scenarios evaluated for all options)
- Generates all files in `output/`:
  - `summary.md` — narrative overview of the full plan
  - `strategy_matrix.json` — options × scenarios grid with ratings
  - `robust_recommendations.md` — prose recommendations based on robustness analysis
  - `signal_dashboard.json` — all signals from all scenarios in one structure
- Warns if any scenario has fewer than 3 signals
- `--force` regenerates even if output already exists

#### `kahn report show`

```
kahn report show [--section summary|strategy|recommendations|signals]
```

Renders the specified output section to terminal. Default: summary.

#### `kahn report export`

```
kahn report export [--format markdown|json] [--output FILE]
```

Writes the full report to stdout or a file. Default format: markdown. Useful for piping.

---

### `kahn validate`

```
kahn validate
```

Runs full referential integrity and schema validation across the project:
- All JSON files parse and validate against their Pydantic schemas
- All `source_force_id` references in critical uncertainties resolve to existing forces
- All `predetermined_element_ids` in scenarios resolve to existing forces
- All scenario IDs in `performance.json` resolve to existing scenarios
- All option IDs in performance files resolve to existing options

Prints a pass/fail report. Designed to be run by an agent before any major operation.

---

### `kahn snapshot`

#### `kahn snapshot save <label>`

```
kahn snapshot save "after_workshop"
```

Copies the full current project state to `snapshots/after_workshop/`. Label must be filesystem-safe.

#### `kahn snapshot list`

Lists all snapshots with labels and timestamps.

#### `kahn snapshot restore <label>`

```
kahn snapshot restore "after_workshop" [--confirm]
```

Replaces current project state with the snapshot. Destructive — requires `--confirm`.

---

## Error Handling

All errors follow a consistent format:

```
✗ Error: [error code] message
  Context: additional detail
  Hint: suggested remediation
```

**Error codes:**

| Code | Meaning |
|------|---------|
| `PHASE_LOCKED` | Command blocked because target phase is locked |
| `PHASE_REQUIRED` | Command requires a phase that hasn't been reached |
| `VALIDATION_FAILED` | JSON file failed schema validation |
| `ID_NOT_FOUND` | Referenced ID does not exist |
| `DEPENDENCY_MISSING` | Required predecessor step not complete |
| `INTEGRITY_ERROR` | Referential integrity violation |
| `ALREADY_EXISTS` | Attempted to create something that exists |

---

## Machine-Readable Output (`--json`)

Every command that produces output supports `--json`. The JSON envelope is:

```json
{
  "command": "force list",
  "status": "ok | error",
  "data": {},
  "warnings": [],
  "errors": [],
  "next_steps": []
}
```

`next_steps` is an array of suggested CLI commands for the agent to consider next.
This is the primary mechanism for agent guidance — the tool tells the agent what to do next
rather than requiring the agent to reason about state from scratch.

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `KAHN_PROJECT_DIR` | Default project directory | `./kahn_project` |
| `KAHN_JSON_OUTPUT` | Always use JSON output | `false` |
| `KAHN_NO_COLOR` | Disable rich terminal color | `false` |

---

## Project Layout: Python Package

```
kahn/
├── pyproject.toml
├── README.md
│
└── kahn/
    ├── __init__.py
    ├── cli.py               # typer app, command registration
    │
    ├── commands/
    │   ├── init.py
    │   ├── status.py
    │   ├── force.py
    │   ├── uncertainty.py
    │   ├── scenario.py
    │   ├── phase.py
    │   ├── option.py
    │   ├── report.py
    │   ├── validate.py
    │   └── snapshot.py
    │
    ├── models/              # Pydantic schemas
    │   ├── meta.py
    │   ├── force.py
    │   ├── uncertainty.py
    │   ├── scenario.py
    │   └── option.py
    │
    ├── store.py             # filesystem read/write, ID generation
    ├── validator.py         # referential integrity checks
    ├── scorer.py            # robustness_score, consistency_score computation
    └── renderer.py          # rich terminal output, report templates
```

---

## Design Invariants

1. **The tool never calls an LM.** It is pure structure. The LM (agent) calls the tool.
2. **Phase locks are irreversible.** Use snapshots before locking if you want an escape hatch.
3. **`--json` + `next_steps` is the agent interface.** Human-facing rich output is secondary.
4. **All IDs are stable.** Once assigned, an ID never changes even if the record is edited.
5. **Narratives are Markdown files, not JSON fields.** They are first-class artifacts, not data.
6. **`validate` is idempotent and safe.** It never modifies state. Always safe for an agent to run.