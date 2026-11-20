Model: claude-haiku-5-5

| | agent | workflow |
|---|---|---|
| Runs | 120 | 120 |
| Task completion | 92.5% (86% to 96%), 111 of 120 | 90.0% (83% to 94%), 108 of 120 |
| Completion, easy tasks | n/a | n/a |
| Completion, hard tasks | 92.5% (86% to 96%), 111 of 120 | 90.0% (83% to 94%), 108 of 120 |
| Wrong grants | 0 in 0 runs | 6 in 6 runs |
| First-try tool-call success | 100.0% (99% to 100%), 549 of 549 | 100.0% (99% to 100%), 614 of 614 |
| Gave up or crashed | 1 | 0 |
| Model calls per run | 4.5 | 1.1 |
| Tokens in / out | 1,407,257 / 58,660 | 117,336 / 17,343 |
| Model cost at list price | $0.17 | $0.02 |
| Cost per completed task | $0.0015 | $0.0002 |

Completion by case:

| Case | agent | workflow |
|---|---|---|
| extra_grant | 30 of 30 | 30 of 30 |
| filler_words | 24 of 24 | 24 of 24 |
| near_duplicate | 21 of 24 | 21 of 24 |
| replace_ask | 18 of 24 | 15 of 24 |
| skip_control | 18 of 18 | 18 of 18 |

Recorded, not acted on. Would each signal have flagged the runs that went wrong?

| Signal | agent | workflow |
|---|---|---|
| Runs with a stated confidence | 119 of 120 | 120 of 120 |
| Mean confidence, completed / missed | 91 / 80 | 80 / 49 |
| Confidence below 70 | 1 runs: 1 of 9 misses, 0 of 0 wrong-grant runs | 27 runs: 9 of 12 misses, 6 of 6 wrong-grant runs |
| Confidence below 80 | 2 runs: 2 of 9 misses, 0 of 0 wrong-grant runs | 27 runs: 9 of 12 misses, 6 of 6 wrong-grant runs |
| Confidence below 90 | 26 runs: 8 of 9 misses, 0 of 0 wrong-grant runs | 81 runs: 12 of 12 misses, 6 of 6 wrong-grant runs |
| A lookup returned more than one match | 12 runs: 3 of 9 misses, 0 of 0 wrong-grant runs | 15 runs: 3 of 12 misses, 0 of 6 wrong-grant runs |

Calls policy refused, by rule. In brackets: adds of a pair the label doesn't expect.

| Rule | agent | workflow |
|---|---|---|
| department-must-be-eligible | 9 (9) | 9 (9) |
| inactive-users-get-nothing | 3 (3) | 3 (3) |
| match-must-be-settled-by-the-request | 4 (0) | 3 (0) |
| privileged-groups-are-for-people | 6 (0) | 6 (0) |
| restricted-group-without-an-owner | 3 (0) | 6 (0) |

FAIL: 6 wrong grant(s).
