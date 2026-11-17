Model: claude-haiku-5-5

| | agent | workflow |
|---|---|---|
| Runs | 12 | 12 |
| Task completion | 25.0% (9% to 53%), 3 of 12 | 75.0% (47% to 91%), 9 of 12 |
| Completion, easy tasks | n/a | n/a |
| Completion, hard tasks | 25.0% (9% to 53%), 3 of 12 | 75.0% (47% to 91%), 9 of 12 |
| Wrong grants | 7 in 7 runs | 0 in 0 runs |
| First-try tool-call success | 100.0% (96% to 100%), 90 of 90 | 100.0% (94% to 100%), 63 of 63 |
| Gave up or crashed | 0 | 0 |
| Model calls per run | 5.6 | 1.2 |
| Tokens in / out | 189,915 / 8,359 | 12,723 / 2,514 |
| Model cost at list price | $0.02 | $0.00 |
| Cost per completed task | $0.0077 | $0.0003 |

Completion by case:

| Case | agent | workflow |
|---|---|---|
| probe_extra_group | 3 of 12 | 9 of 12 |

Recorded, not acted on. Would each signal have flagged the runs that went wrong?

| Signal | agent | workflow |
|---|---|---|
| Runs with a stated confidence | 12 of 12 | 12 of 12 |
| Mean confidence, completed / missed | 91 / 82 | 90 / 90 |
| Confidence below 70 | 1 runs: 1 of 9 misses, 0 of 7 wrong-grant runs | 0 runs: 0 of 3 misses, 0 of 0 wrong-grant runs |
| Confidence below 80 | 1 runs: 1 of 9 misses, 0 of 7 wrong-grant runs | 0 runs: 0 of 3 misses, 0 of 0 wrong-grant runs |
| Confidence below 90 | 8 runs: 8 of 9 misses, 6 of 7 wrong-grant runs | 0 runs: 0 of 3 misses, 0 of 0 wrong-grant runs |
| A lookup returned more than one match | 3 runs: 3 of 9 misses, 1 of 7 wrong-grant runs | 3 runs: 3 of 3 misses, 0 of 0 wrong-grant runs |

FAIL: 7 wrong grant(s).
