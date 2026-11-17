Model: claude-haiku-5-5

| | agent | workflow |
|---|---|---|
| Runs | 16 | 16 |
| Task completion | 6.2% (1% to 28%), 1 of 16 | 100.0% (81% to 100%), 16 of 16 |
| Completion, easy tasks | n/a | n/a |
| Completion, hard tasks | 6.2% (1% to 28%), 1 of 16 | 100.0% (81% to 100%), 16 of 16 |
| Wrong grants | 0 in 0 runs | 0 in 0 runs |
| First-try tool-call success | 100.0% (98% to 100%), 171 of 171 | 100.0% (98% to 100%), 176 of 176 |
| Gave up or crashed | 2 | 0 |
| Model calls per run | 8.4 | 2.0 |
| Tokens in / out | 442,259 / 13,128 | 31,888 / 5,113 |
| Model cost at list price | $0.05 | $0.01 |
| Cost per completed task | $0.0508 | $0.0004 |

Completion by case:

| Case | agent | workflow |
|---|---|---|
| near_duplicate_group | 1 of 16 | 16 of 16 |

Recorded, not acted on. Would each signal have flagged the runs that went wrong?

| Signal | agent | workflow |
|---|---|---|
| Runs with a stated confidence | 14 of 16 | 16 of 16 |
| Mean confidence, completed / missed | 90 / 65 | 80 / n/a |
| Confidence below 70 | 7 runs: 7 of 15 misses, 0 of 0 wrong-grant runs | 0 runs: 0 of 0 misses, 0 of 0 wrong-grant runs |
| Confidence below 80 | 13 runs: 13 of 15 misses, 0 of 0 wrong-grant runs | 0 runs: 0 of 0 misses, 0 of 0 wrong-grant runs |
| Confidence below 90 | 13 runs: 13 of 15 misses, 0 of 0 wrong-grant runs | 16 runs: 0 of 0 misses, 0 of 0 wrong-grant runs |
| A lookup returned more than one match | 16 runs: 15 of 15 misses, 0 of 0 wrong-grant runs | 16 runs: 0 of 0 misses, 0 of 0 wrong-grant runs |

Pass: zero wrong grants.
