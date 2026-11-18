Model: claude-sonnet-5-5

| | agent | workflow |
|---|---|---|
| Runs | 120 | 120 |
| Task completion | 100.0% (97% to 100%), 120 of 120 | 97.5% (93% to 99%), 117 of 120 |
| Completion, easy tasks | n/a | n/a |
| Completion, hard tasks | 100.0% (97% to 100%), 120 of 120 | 97.5% (93% to 99%), 117 of 120 |
| Wrong grants | 0 in 0 runs | 0 in 0 runs |
| First-try tool-call success | 100.0% (99% to 100%), 517 of 517 | 100.0% (99% to 100%), 597 of 597 |
| Gave up or crashed | 0 | 0 |
| Model calls per run | 4.3 | 1.2 |
| Tokens in / out | 1,259,032 / 63,071 | 108,612 / 33,064 |
| Model cost at list price | $3.15 | $0.55 |
| Cost per completed task | $0.0262 | $0.0047 |

Completion by case:

| Case | agent | workflow |
|---|---|---|
| extra_grant | 30 of 30 | 30 of 30 |
| filler_words | 24 of 24 | 24 of 24 |
| near_duplicate | 24 of 24 | 21 of 24 |
| replace_ask | 24 of 24 | 24 of 24 |
| skip_control | 18 of 18 | 18 of 18 |

Recorded, not acted on. Would each signal have flagged the runs that went wrong?

| Signal | agent | workflow |
|---|---|---|
| Runs with a stated confidence | 120 of 120 | 120 of 120 |
| Mean confidence, completed / missed | 95 / n/a | 88 / 57 |
| Confidence below 70 | 0 runs: 0 of 0 misses, 0 of 0 wrong-grant runs | 8 runs: 2 of 3 misses, 0 of 0 wrong-grant runs |
| Confidence below 80 | 0 runs: 0 of 0 misses, 0 of 0 wrong-grant runs | 12 runs: 3 of 3 misses, 0 of 0 wrong-grant runs |
| Confidence below 90 | 3 runs: 0 of 0 misses, 0 of 0 wrong-grant runs | 48 runs: 3 of 3 misses, 0 of 0 wrong-grant runs |
| A lookup returned more than one match | 12 runs: 0 of 0 misses, 0 of 0 wrong-grant runs | 21 runs: 3 of 3 misses, 0 of 0 wrong-grant runs |

Calls policy refused, by rule. In brackets: adds of a pair the label doesn't expect.

| Rule | agent | workflow |
|---|---|---|
| department-must-be-eligible | 9 (9) | 9 (9) |
| inactive-users-get-nothing | 6 (6) | 6 (6) |
| privileged-groups-are-for-people | 6 (0) | 6 (0) |
| restricted-group-without-an-owner | 3 (0) | 3 (0) |

Pass: zero wrong grants.
