Model: claude-sonnet-5-5

| | agent | workflow |
|---|---|---|
| Runs | 120 | 120 |
| Task completion | 97.5% (93% to 99%), 117 of 120 | 97.5% (93% to 99%), 117 of 120 |
| Completion, easy tasks | n/a | n/a |
| Completion, hard tasks | 97.5% (93% to 99%), 117 of 120 | 97.5% (93% to 99%), 117 of 120 |
| Wrong grants | 0 in 0 runs | 0 in 0 runs |
| First-try tool-call success | 100.0% (99% to 100%), 513 of 513 | 100.0% (99% to 100%), 614 of 614 |
| Gave up or crashed | 0 | 0 |
| Model calls per run | 4.3 | 1.2 |
| Tokens in / out | 1,247,125 / 64,012 | 108,862 / 32,345 |
| Model cost at list price | $3.13 | $0.54 |
| Cost per completed task | $0.0268 | $0.0046 |

Completion by case:

| Case | agent | workflow |
|---|---|---|
| extra_grant | 30 of 30 | 30 of 30 |
| filler_words | 24 of 24 | 24 of 24 |
| near_duplicate | 21 of 24 | 21 of 24 |
| replace_ask | 24 of 24 | 24 of 24 |
| skip_control | 18 of 18 | 18 of 18 |

Recorded, not acted on. Would each signal have flagged the runs that went wrong?

| Signal | agent | workflow |
|---|---|---|
| Runs with a stated confidence | 120 of 120 | 120 of 120 |
| Mean confidence, completed / missed | 95 / 80 | 88 / 67 |
| Confidence below 70 | 0 runs: 0 of 3 misses, 0 of 0 wrong-grant runs | 6 runs: 2 of 3 misses, 0 of 0 wrong-grant runs |
| Confidence below 80 | 0 runs: 0 of 3 misses, 0 of 0 wrong-grant runs | 14 runs: 2 of 3 misses, 0 of 0 wrong-grant runs |
| Confidence below 90 | 3 runs: 3 of 3 misses, 0 of 0 wrong-grant runs | 41 runs: 3 of 3 misses, 0 of 0 wrong-grant runs |
| A lookup returned more than one match | 12 runs: 3 of 3 misses, 0 of 0 wrong-grant runs | 21 runs: 3 of 3 misses, 0 of 0 wrong-grant runs |

Pass: zero wrong grants.
