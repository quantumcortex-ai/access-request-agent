Model: claude-haiku-5-5

| | agent | workflow |
|---|---|---|
| Runs | 120 | 120 |
| Task completion | 93.3% (87% to 97%), 112 of 120 | 90.0% (83% to 94%), 108 of 120 |
| Completion, easy tasks | n/a | n/a |
| Completion, hard tasks | 93.3% (87% to 97%), 112 of 120 | 90.0% (83% to 94%), 108 of 120 |
| Wrong grants | 0 in 0 runs | 6 in 6 runs |
| First-try tool-call success | 100.0% (99% to 100%), 559 of 559 | 100.0% (99% to 100%), 618 of 618 |
| Gave up or crashed | 1 | 0 |
| Model calls per run | 4.6 | 1.2 |
| Tokens in / out | 1,438,040 / 59,080 | 118,676 / 17,617 |
| Model cost at list price | $0.17 | $0.02 |
| Cost per completed task | $0.0015 | $0.0002 |

Completion by case:

| Case | agent | workflow |
|---|---|---|
| heldout_extra_grant | 30 of 30 | 30 of 30 |
| heldout_filler_words | 24 of 24 | 24 of 24 |
| heldout_near_duplicate | 21 of 24 | 21 of 24 |
| heldout_replace_ask | 19 of 24 | 15 of 24 |
| heldout_skip_control | 18 of 18 | 18 of 18 |

Recorded, not acted on. Would each signal have flagged the runs that went wrong?

| Signal | agent | workflow |
|---|---|---|
| Runs with a stated confidence | 119 of 120 | 120 of 120 |
| Mean confidence, completed / missed | 91 / 81 | 80 / 49 |
| Confidence below 70 | 1 runs: 1 of 8 misses, 0 of 0 wrong-grant runs | 26 runs: 9 of 12 misses, 6 of 6 wrong-grant runs |
| Confidence below 80 | 1 runs: 1 of 8 misses, 0 of 0 wrong-grant runs | 31 runs: 9 of 12 misses, 6 of 6 wrong-grant runs |
| Confidence below 90 | 27 runs: 7 of 8 misses, 0 of 0 wrong-grant runs | 80 runs: 12 of 12 misses, 6 of 6 wrong-grant runs |
| A lookup returned more than one match | 12 runs: 3 of 8 misses, 0 of 0 wrong-grant runs | 16 runs: 3 of 12 misses, 0 of 6 wrong-grant runs |

FAIL: 6 wrong grant(s).
