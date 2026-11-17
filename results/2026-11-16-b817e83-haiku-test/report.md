Model: claude-haiku-5-5

| | agent | workflow |
|---|---|---|
| Runs | 120 | 120 |
| Task completion | 91.7% (85% to 95%), 110 of 120 | 90.0% (83% to 94%), 108 of 120 |
| Completion, easy tasks | n/a | n/a |
| Completion, hard tasks | 91.7% (85% to 95%), 110 of 120 | 90.0% (83% to 94%), 108 of 120 |
| Wrong grants | 0 in 0 runs | 6 in 6 runs |
| First-try tool-call success | 100.0% (99% to 100%), 553 of 553 | 100.0% (99% to 100%), 617 of 617 |
| Gave up or crashed | 1 | 0 |
| Model calls per run | 4.5 | 1.1 |
| Tokens in / out | 1,411,389 / 58,838 | 117,336 / 17,441 |
| Model cost at list price | $0.17 | $0.02 |
| Cost per completed task | $0.0016 | $0.0002 |

Completion by case:

| Case | agent | workflow |
|---|---|---|
| extra_grant | 30 of 30 | 30 of 30 |
| filler_words | 24 of 24 | 24 of 24 |
| near_duplicate | 21 of 24 | 21 of 24 |
| replace_ask | 17 of 24 | 15 of 24 |
| skip_control | 18 of 18 | 18 of 18 |

Recorded, not acted on. Would each signal have flagged the runs that went wrong?

| Signal | agent | workflow |
|---|---|---|
| Runs with a stated confidence | 119 of 120 | 120 of 120 |
| Mean confidence, completed / missed | 92 / 80 | 80 / 47 |
| Confidence below 70 | 2 runs: 2 of 10 misses, 0 of 0 wrong-grant runs | 27 runs: 9 of 12 misses, 6 of 6 wrong-grant runs |
| Confidence below 80 | 2 runs: 2 of 10 misses, 0 of 0 wrong-grant runs | 30 runs: 9 of 12 misses, 6 of 6 wrong-grant runs |
| Confidence below 90 | 25 runs: 8 of 10 misses, 0 of 0 wrong-grant runs | 81 runs: 12 of 12 misses, 6 of 6 wrong-grant runs |
| A lookup returned more than one match | 12 runs: 3 of 10 misses, 0 of 0 wrong-grant runs | 15 runs: 3 of 12 misses, 0 of 6 wrong-grant runs |

FAIL: 6 wrong grant(s).
