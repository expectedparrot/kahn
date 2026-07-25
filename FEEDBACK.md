# kahn CLI — Feedback from Agent Trial Run

Collected during a full end-to-end run: construction industry / AI / 5–10 year horizon.
Organized by priority.

---

## Bugs / Hard Failures

### 1. `kahn report show --section` gives no valid options on error
Running `--section scenarios` returned `VALIDATION_FAILED: Unknown report section` with no indication of what values ARE valid. The error message should enumerate accepted section names (e.g. `summary`, `recommendations`).

### 2. No HTML export format
`kahn report export --format` only supports `markdown` and `json`. HTML requires manual construction from the JSON output. Either add `--format html` or document that HTML is unsupported and must be built externally.

---

## Friction / Workflow Issues

### 3. ~~`codegen evaluate-options` requires manual copy-paste of generated commands~~ Resolved
The script prints `kahn option evaluate` commands but does not execute them. The agent must copy ~5 large multi-flag commands and re-run them manually. Add an `--auto-apply` flag or have the generated script call `kahn` directly at the end.

### 4. Two-step narrative loading is awkward
Kahn now builds portable, model-free Jobs packages. The `ep` client runs them and
`kahn ingest` validates and applies the Results explicitly.

### 5. `uncertainty check-independence` gives no remediation path
When a correlation is flagged, the output is a warning panel with no indication of whether it is blocking or advisory, and no suggested fix. Should say either "safe to proceed" or "consider replacing cu00X with an alternative force" with a pointer to `kahn force list`.

---

## Weak Feedback / Unhelpful Output

### 6. Consistency check notes are generic and non-actionable
All four scenarios received identical notes: *"Predetermined trends are not clearly reflected in the narrative."* This doesn't identify which specific forces are absent. The check should name the force IDs that are missing from each narrative.

### 7. No passing threshold defined for consistency scores
Scores of 0.70–0.80 were returned but the CLI never indicates what is acceptable. The phase advanced without complaint. Either document the threshold (e.g. ≥0.70 is sufficient) or surface it in the check output.

### 8. `--human` table truncates force names
In `kahn force list --human`, long names were cut off in the table. This matters during the uncertainty selection step when full names are needed to make a good choice. Consider wrapping text or increasing column width.

---

## Documentation Issues

### 9. `agent-start` operating rules say to always pass `--project-dir` but `agent-start` itself doesn't require it
Minor inconsistency. The rules state "Pass `--project-dir <path>` on every command" but `agent-start` runs fine without it, defaulting to `kahn_project`. Clarify in the rules whether `agent-start` is exempt, or make it consistent.

### 10. Getting-started guide uses hardcoded force IDs in `uncertainty select` example
The guide shows `kahn uncertainty select f003 f007` without explaining that force IDs are assigned sequentially and must be looked up via `kahn force list` first. A new user won't know their IDs. Add an explicit `kahn force list` step before the `uncertainty select` example.

---

## Priority Order for Fixes

1. **#3** resolved by the Jobs/Results execution boundary.
2. **#4** (two-step narrative loading) — unnecessary manual step every scenario
3. **#1** (unhelpful error message on report show) — confusing for agents and humans
4. **#2** (no HTML export) — forces manual workaround for a common output need
5. **#6** (generic consistency notes) — reduces analytical value of the check
6. **#5** (no remediation on independence warning) — leaves agent uncertain how to proceed
7. **#7, #8, #9, #10** — polish / docs
