Model: claude-sonnet-5-5

| | agent | workflow |
|---|---|---|
| Runs | 120 | 120 |
| Task completion | 97.5% (93% to 99%), 117 of 120 | 97.5% (93% to 99%), 117 of 120 |
| Completion, easy tasks | n/a | n/a |
| Completion, hard tasks | 97.5% (93% to 99%), 117 of 120 | 97.5% (93% to 99%), 117 of 120 |
| Wrong grants | 0 in 0 runs | 0 in 0 runs |
| First-try tool-call success | 100.0% (99% to 100%), 513 of 513 | 100.0% (99% to 100%), 604 of 604 |
| Gave up or crashed | 0 | 0 |
| Model calls per run | 4.3 | 1.2 |
| Tokens in / out | 1,245,694 / 63,029 | 107,366 / 32,807 |
| Model cost at list price | $3.12 | $0.54 |
| Cost per completed task | $0.0267 | $0.0046 |

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
| Mean confidence, completed / missed | 95 / 77 | 87 / 53 |
| Confidence below 70 | 0 runs: 0 of 3 misses, 0 of 0 wrong-grant runs | 10 runs: 3 of 3 misses, 0 of 0 wrong-grant runs |
| Confidence below 80 | 1 runs: 1 of 3 misses, 0 of 0 wrong-grant runs | 14 runs: 3 of 3 misses, 0 of 0 wrong-grant runs |
| Confidence below 90 | 3 runs: 3 of 3 misses, 0 of 0 wrong-grant runs | 44 runs: 3 of 3 misses, 0 of 0 wrong-grant runs |
| A lookup returned more than one match | 12 runs: 3 of 3 misses, 0 of 0 wrong-grant runs | 18 runs: 3 of 3 misses, 0 of 0 wrong-grant runs |

Calls policy refused, by rule. In brackets: adds of a pair the label doesn't expect.

| Rule | agent | workflow |
|---|---|---|
| department-must-be-eligible | 9 (9) | 9 (9) |
| inactive-users-get-nothing | 6 (6) | 6 (6) |
| match-must-be-settled-by-the-request | 2 (0) | 0 (0) |
| privileged-groups-are-for-people | 6 (0) | 6 (0) |
| restricted-group-without-an-owner | 3 (0) | 3 (0) |

Pass: zero wrong grants.
