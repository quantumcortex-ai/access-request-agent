# Release gate: exit 2

Held: a rule refused calls on pairs the requests didn't ask for, more often than in the baseline.

- Run: `results/2026-11-18-f065586-haiku-drill-rules-on`
- Baseline: `results/2026-11-17-eb2dc55-haiku-validation`
- Prompts and tool schemas: not recorded in one of the runs
- Policy rules: not recorded in one of the runs

| | workflow | agent |
|---|---|---|
| Wrong grants (gated) | 0 | 0 |
| Refusals on a pair not asked for, run / baseline (gated) | 0 / 0 | 3 / 0 |
| Completed, run / baseline | 311 of 312 / 309 of 312 | 312 of 312 / 312 of 312 |
| Handed back, run / baseline | 67 / 69 | 66 / 66 |
| Requests no longer always completed | none | none |
| Requests now always completed | none | none |
| Cost, run / baseline | $0.05 / $0.05 | $0.37 / $0.40 |

agent:
- t-123 r1: one-grant-per-request refused add_to_group u-00048 g-0002
- t-123 r2: one-grant-per-request refused add_to_group u-00048 g-0002
- t-123 r3: one-grant-per-request refused add_to_group u-00048 g-0002
