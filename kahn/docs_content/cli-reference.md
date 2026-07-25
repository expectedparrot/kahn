# kahn CLI Quick Reference

All commands accept `--project-dir PATH` and `--human` flags. Output is JSON by default; pass `--human` for rich terminal output.

## Phase Flow

```
forces → uncertainty_selection → scenario_construction → option_evaluation → complete
```

Phase locks are irreversible. Use `kahn snapshot save` before locking.

## Commands by Phase

### Initialization
```bash
kahn init --question "..." --domain "..." --horizon "..." [--id ID] [--notes TEXT]
kahn status
```

### Phase 1: Forces
```bash
kahn force add --name "..." --domain <pestel> --type <trend|uncertainty> --impact <low|med|high> --predictability <low|med|high> --direction "..."
kahn force list [--type trend|uncertainty] [--impact low|medium|high]
kahn force show <id>
kahn force edit <id> [--name] [--impact] [--predictability] [--direction] [--notes]
kahn force delete <id> --confirm
```

### Phase 2: Uncertainty Selection
```bash
kahn uncertainty select <force_id> <force_id>
kahn uncertainty set-poles <cu_id> --pole-a "..." --pole-b "..."
kahn uncertainty list
kahn uncertainty check-independence
```

### Phase 3: Scenario Construction
```bash
kahn scenario build
kahn scenario name <id> --name "..." --tagline "..."
kahn scenario narrative set <id> --text "..." | --file PATH
kahn scenario narrative show <id>
kahn scenario signals set <id> --signal "..." --observable-in "..." [repeated]
kahn scenario signals show <id>
kahn scenario list
kahn scenario show <id>
kahn scenario check-consistency [--scenario <id>]
```

### Phase 4: Option Evaluation
```bash
kahn option add --name "..." --description "..." [--hedging] [--notes TEXT]
kahn option list
kahn option show <id>
kahn option evaluate <id> --scenario <sc_id> --rating <robust|acceptable|fragile> --rationale "..." [repeated]
kahn option evaluate-all
kahn option robustness-rank
```

### Phase Management
```bash
kahn phase status
kahn phase lock <phase_name>
kahn phase advance          # validates, locks current, advances to next
```

### Reports
```bash
kahn report generate [--force]
kahn report show [--section summary|strategy|recommendations|signals]
kahn report export [--format markdown|json] [--output FILE]
```

### Utilities
```bash
kahn validate               # full referential integrity check
kahn snapshot save <label>
kahn snapshot list
kahn snapshot restore <label> --confirm
```

### EDSL Jobs and Results
```bash
kahn job generate research-forces [--output jobs/research-forces.jobs.ep]
kahn job generate write-narrative <scenario_id> [--output jobs/narrative.jobs.ep]
kahn job generate evaluate-options [--output jobs/evaluate-options.jobs.ep]

ep inspect <file.jobs.ep>
ep jobs cost <file.jobs.ep>
ep run <file.jobs.ep> --model <model-name> --output <results.ep>

kahn ingest forces --from <results.ep>
kahn ingest narrative <scenario_id> --from <results.ep>
kahn ingest option-evaluations --from <results.ep>
```

## ID Formats

| Entity | Format | Example |
|--------|--------|---------|
| Force | f### | f001, f012 |
| Critical uncertainty | cu### | cu001, cu002 |
| Scenario | sc### | sc001-sc004 |
| Strategic option | op### | op001, op005 |

## PESTEL Domains

`political` | `economic` | `social` | `technological` | `environmental` | `legal`

## Error Codes

`PHASE_LOCKED` | `PHASE_REQUIRED` | `VALIDATION_FAILED` | `ID_NOT_FOUND` | `DEPENDENCY_MISSING` | `INTEGRITY_ERROR` | `ALREADY_EXISTS`
