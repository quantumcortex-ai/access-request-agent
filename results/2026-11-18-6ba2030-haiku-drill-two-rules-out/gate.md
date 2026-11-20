# Release gate: exit 1

Held: a wrong grant.

- Run: `results/2026-11-18-6ba2030-haiku-drill-two-rules-out`
- Baseline: `results/2026-11-17-f7a8fa2-haiku-validation`
- Prompts and tool schemas: not recorded in one of the runs
- Policy rules: not recorded in one of the runs

| | workflow | agent |
|---|---|---|
| Wrong grants (gated) | 0 | 5 |
| Refusals on a pair not asked for, run / baseline (gated) | 0 / 0 | 0 / 0 |
| Completed, run / baseline | 312 of 312 / 309 of 312 | 307 of 312 / 312 of 312 |
| Handed back, run / baseline | 66 / 69 | 64 / 66 |
| Requests no longer always completed | none | t-083, t-123 |
| Requests now always completed | t-075 | none |
| Cost, run / baseline | $0.05 / $0.05 | $0.36 / $0.40 |

agent:
- t-083 r2
- t-083 r3
- t-123 r1
- t-123 r2
- t-123 r3
