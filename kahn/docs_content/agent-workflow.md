# Agent workflow

This guide and the output of `kahn next` are the authoritative operating contract for an agent completing a Kahn scenario-planning project.

## Control loop

1. Run `kahn next --project-dir PATH` before acting.
2. Complete the returned `next_steps` command, eliciting substantive strategic judgments from the user where required.
3. Run `kahn next` again after every material change.
4. Continue until it reports `stage: complete`, or stop when user input, approval, or external model execution is required.

`data.action` is the executable contract. It contains absolute `argv`, `cwd`, `project_dir`, required and enumerated inputs, mutation and spending flags, expected state transition, prerequisites, and alternatives. Populate inputs using their declared flag or positional metadata; do not reconstruct command names from prose.

JSON is the default output. Agents must not pass `--human` when parsing commands. Every successful or failed command returns one envelope with `schema_version`, `command`, `status`, `argv`, `data`, `warnings`, `errors`, and `next_steps`.

## Safety and quality gates

- Treat CLI-managed project records as the source of truth; do not hand-edit them.
- Save a snapshot before changing selected axes or revising a reviewed milestone.
- Use `scenario signals add` for normal incremental work. `scenario signals set` is atomic replacement and requires `--replace` once signals exist. Every scenario requires at least three signals.
- Keep trends separate from genuinely uncertain external drivers.
- Ask the user to confirm the focal decision, horizon, selected axes, scenario narratives, and strategic options.
- Do not claim that scenarios are forecasts or attach probabilities without a separate defensible method.
- Kahn generates model-free EDSL Jobs. Before remote execution, show the user the job, model choice, estimated cost, and likely time risk, and obtain approval.
- Preserve both `*.jobs.ep` and Results artifacts. Never display, copy, or commit credentials.
- Run `kahn validate` before generating or delivering a report.

## Canonical sequence

`init` → forces → critical uncertainties and poles → four scenarios → narratives and signals → strategic options and evaluations → validation → report → snapshot/export.

Use `kahn docs show workflow` for facilitation detail and `kahn docs show cli-reference` for command syntax.
