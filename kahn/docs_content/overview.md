# kahn — Scenario Planning CLI

`kahn` is a CLI tool for running structured Herman Kahn–style scenario planning exercises. It manages the full workflow — from environmental scanning through scenario construction to strategic option evaluation — and produces a final report.

## What It Does

Given a focal strategic question (e.g., "What is the future of MIT in an AI-powered world?"), `kahn` guides you through five sequential phases:

1. **Forces** — catalog 8-15 environmental forces (trends + uncertainties) across PESTEL domains
2. **Uncertainty selection** — pick 2 critical uncertainties that form the axes of a 2×2 scenario matrix
3. **Scenario construction** — build 4 vivid, internally consistent scenarios from the matrix
4. **Option evaluation** — stress-test strategic options across all 4 scenarios
5. **Reporting** — generate an executive summary, strategy matrix, and signal dashboard

## When to Use It

Use `kahn` when you need to:

- Stress-test a strategy against genuinely uncertain futures
- Help stakeholders think beyond the "official future"
- Build shared mental models for organizational decision-making
- Identify leading signals that would indicate which future is emerging

## Key Design Principles

- **State on disk** — all project data lives in a project directory (JSON files). Phase is inferred from artifacts, not metadata.
- **Irreversible phase locks** — phases lock forward. Use `kahn snapshot save` before locking to preserve the ability to revert.
- **JSON output by default** — all commands emit structured JSON for agent/script consumption. Pass `--human` for rich terminal output.
- **Portable Jobs** — for AI-assisted steps, use `kahn job generate` to build model-free EDSL Jobs, run them with the `ep` client, and explicitly ingest the Results.

## Project Directory Layout

```
<project_dir>/
  meta.json                  # project metadata and phase state
  forces/
    trends/                  # trend forces (f001.json, ...)
    uncertainties/           # uncertainty forces
  critical_uncertainties/    # the 2 selected axes (cu001.json, cu002.json)
  scenarios/
    sc001/                   # one directory per scenario
      meta.json
      narrative.md
      signals.json
    ...
  strategic_options/
    op001/
      meta.json
      performance.json       # cross-scenario ratings
    ...
  output/
    summary.md
    strategy_matrix.json
    robust_recommendations.md
    signal_dashboard.json
  snapshots/                 # named snapshots
  jobs/                      # portable Jobs and Results artifacts
```

## Quick Start

```bash
kahn status --project-dir ./my_project    # bootstrap: get brief + state + guide
kahn init --question "..." --domain "..." --horizon "10-15 years" --project-dir ./my_project
kahn status --project-dir ./my_project
```

## Next Steps

- `kahn docs show getting-started` — step-by-step first workflow
- `kahn docs show workflow` — detailed phase guide
