# Market-entry scenario project

This example follows the full Kahn control loop for a market-entry decision shaped by regulation and adoption.

```bash
export KAHN_EXAMPLE_DIR="$(mktemp -d)/market-entry"
kahn next --project-dir "$KAHN_EXAMPLE_DIR"
kahn init --question "How should we enter the market?" --domain energy --horizon 2030 --project-dir "$KAHN_EXAMPLE_DIR"
kahn next --project-dir "$KAHN_EXAMPLE_DIR"
```

Continue with the returned `next_steps`. Add at least one trend and two high-impact, low-predictability uncertainties, select and define the two axes, and rerun `kahn next` after every stage. The end-to-end test suite executes this same lifecycle through report generation without remote model calls.
