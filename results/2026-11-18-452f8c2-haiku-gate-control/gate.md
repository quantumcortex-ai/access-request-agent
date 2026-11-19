# Release gate: exit 0

Pass. The change can ship.

- Run: `results/2026-11-18-452f8c2-haiku-gate-control`
- Baseline: `results/2026-11-17-eb2dc55-haiku-validation`
- Prompts and tool schemas: not recorded in one of the runs
- Policy rules: not recorded in one of the runs

| | workflow | agent |
|---|---|---|
| Wrong grants (gated) | 0 | 0 |
| Refusals on a pair not asked for, run / baseline (gated) | 0 / 0 | 0 / 0 |
| Completed, run / baseline | 312 of 312 / 309 of 312 | 312 of 312 / 312 of 312 |
| Handed back, run / baseline | 66 / 69 | 66 / 66 |
| Requests no longer always completed | none | none |
| Requests now always completed | t-075 | none |
| Cost, run / baseline | $0.05 / $0.05 | $0.40 / $0.40 |
