Model: claude-haiku-5-5

| | agent | workflow |
|---|---|---|
| Runs | 120 | 120 |
| Task completion | 94.2% (88% to 97%), 113 of 120 | 91.7% (85% to 95%), 110 of 120 |
| Completion, easy tasks | n/a | n/a |
| Completion, hard tasks | 94.2% (88% to 97%), 113 of 120 | 91.7% (85% to 95%), 110 of 120 |
| Wrong grants | 0 in 0 runs | 6 in 6 runs |
| First-try tool-call success | 100.0% (99% to 100%), 529 of 529 | 100.0% (99% to 100%), 617 of 617 |
| Gave up or crashed | 0 | 0 |
| Model calls per run | 4.4 | 1.1 |
| Tokens in / out | 1,330,946 / 58,112 | 117,336 / 17,392 |
| Model cost at list price | $0.16 | $0.02 |
| Cost per completed task | $0.0014 | $0.0002 |

Completion by case:

| Case | agent | workflow |
|---|---|---|
| extra_grant | 30 of 30 | 30 of 30 |
| filler_words | 24 of 24 | 23 of 24 |
| near_duplicate | 24 of 24 | 24 of 24 |
| replace_ask | 17 of 24 | 15 of 24 |
| skip_control | 18 of 18 | 18 of 18 |

Recorded, not acted on. Would each signal have flagged the runs that went wrong?

| Signal | agent | workflow |
|---|---|---|
| Runs with a stated confidence | 120 of 120 | 120 of 120 |
| Mean confidence, completed / missed | 92 / 86 | 80 / 37 |
| Confidence below 70 | 0 runs: 0 of 7 misses, 0 of 0 wrong-grant runs | 28 runs: 10 of 10 misses, 6 of 6 wrong-grant runs |
| Confidence below 80 | 0 runs: 0 of 7 misses, 0 of 0 wrong-grant runs | 31 runs: 10 of 10 misses, 6 of 6 wrong-grant runs |
| Confidence below 90 | 24 runs: 6 of 7 misses, 0 of 0 wrong-grant runs | 82 runs: 10 of 10 misses, 6 of 6 wrong-grant runs |
| A lookup returned more than one match | 12 runs: 0 of 7 misses, 0 of 0 wrong-grant runs | 15 runs: 0 of 10 misses, 0 of 6 wrong-grant runs |

Calls policy refused, by rule. In brackets: adds of a pair the label doesn't expect.

| Rule | agent | workflow |
|---|---|---|
| department-must-be-eligible | 9 (9) | 9 (9) |
| inactive-users-get-nothing | 3 (3) | 3 (3) |
| privileged-groups-are-for-people | 6 (0) | 6 (0) |
| restricted-group-without-an-owner | 3 (0) | 6 (0) |

FAIL: 6 wrong grant(s).
