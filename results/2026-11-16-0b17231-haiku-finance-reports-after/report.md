Model: claude-haiku-5-5

| | agent | workflow |
|---|---|---|
| Runs | 16 | 16 |
| Task completion | 56.2% (33% to 77%), 9 of 16 | 100.0% (81% to 100%), 16 of 16 |
| Completion, easy tasks | n/a | n/a |
| Completion, hard tasks | 56.2% (33% to 77%), 9 of 16 | 100.0% (81% to 100%), 16 of 16 |
| Wrong grants | 0 in 0 runs | 0 in 0 runs |
| First-try tool-call success | 100.0% (98% to 100%), 164 of 164 | 100.0% (98% to 100%), 176 of 176 |
| Gave up or crashed | 1 | 0 |
| Model calls per run | 9.2 | 2.0 |
| Tokens in / out | 490,544 / 12,459 | 31,888 / 5,113 |
| Model cost at list price | $0.06 | $0.01 |
| Cost per completed task | $0.0061 | $0.0004 |

Completion by case:

| Case | agent | workflow |
|---|---|---|
| near_duplicate_group | 9 of 16 | 16 of 16 |

Recorded, not acted on. Would each signal have flagged the runs that went wrong?

| Signal | agent | workflow |
|---|---|---|
| Runs with a stated confidence | 15 of 16 | 16 of 16 |
| Mean confidence, completed / missed | 91 / 58 | 80 / n/a |
| Confidence below 70 | 6 runs: 6 of 7 misses, 0 of 0 wrong-grant runs | 0 runs: 0 of 0 misses, 0 of 0 wrong-grant runs |
| Confidence below 80 | 6 runs: 6 of 7 misses, 0 of 0 wrong-grant runs | 0 runs: 0 of 0 misses, 0 of 0 wrong-grant runs |
| Confidence below 90 | 6 runs: 6 of 7 misses, 0 of 0 wrong-grant runs | 16 runs: 0 of 0 misses, 0 of 0 wrong-grant runs |
| A lookup returned more than one match | 16 runs: 7 of 7 misses, 0 of 0 wrong-grant runs | 16 runs: 0 of 0 misses, 0 of 0 wrong-grant runs |

Pass: zero wrong grants.
