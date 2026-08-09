# Agent Instructions

Use Kahn's bundled workflow guide and state-derived next action as the source of truth:

```bash
kahn guide
kahn next --project-dir PATH
```

Run `kahn next` after every material workflow change and follow its `next_steps` until the project is complete or user input, approval, or external model execution is required. Keep JSON output enabled for parsing; use `--human` only for people. Preserve project provenance and snapshots, run `kahn validate` before reporting, and follow the remote-execution approval rules in `kahn guide`.
