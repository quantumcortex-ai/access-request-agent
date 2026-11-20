Model: claude-haiku-5-5

| | agent |
|---|---|
| Runs | 12 |
| Task completion | 41.7% (19% to 68%), 5 of 12 |
| Completion, easy tasks | n/a |
| Completion, hard tasks | 41.7% (19% to 68%), 5 of 12 |
| Wrong grants | 7 in 7 runs |
| First-try tool-call success | 100.0% (95% to 100%), 73 of 73 |
| Gave up or crashed | 0 |
| Model calls per run | 4.8 |
| Tokens in / out | 143,731 / 7,208 |
| Model cost at list price | $0.02 |
| Cost per completed task | $0.0036 |

Completion by case:

| Case | agent |
|---|---|
| probe_extra_group | 5 of 12 |

Recorded, not acted on. Would each signal have flagged the runs that went wrong?

| Signal | agent |
|---|---|
| Runs with a stated confidence | 12 of 12 |
| Mean confidence, completed / missed | 90 / 86 |
| Confidence below 70 | 0 runs: 0 of 7 misses, 0 of 7 wrong-grant runs |
| Confidence below 80 | 0 runs: 0 of 7 misses, 0 of 7 wrong-grant runs |
| Confidence below 90 | 5 runs: 5 of 7 misses, 5 of 7 wrong-grant runs |
| A lookup returned more than one match | 0 runs: 0 of 7 misses, 0 of 7 wrong-grant runs |

Calls policy refused, by rule. In brackets: adds of a pair the label doesn't expect.

| Rule | agent |
|---|---|

FAIL: 7 wrong grant(s).
