# Results

One folder for each run. Each holds the run's report and its records. The run numbers are the ones the main
[README](../README.md) uses.

| Run | Folder | Code |
|---|---|---|
| 1 | `2026-11-15-haiku` | Commit not recorded. The first run, before `6a2999d` |
| 2 | `2026-11-15-haiku-rerun` | Commit not recorded. Ran with `6a2999d`, which adds models that refuse a forced tool call |
| 3 | `2026-11-15-sonnet` | Commit not recorded. The same code as run 2 |
| 4 | `2026-11-15-haiku-settle-rule-off` | Commit not recorded. Ran with `e2cb47e`, with the settle rule left out |
| 5 | `2026-11-15-haiku-settle-rule-on` | Commit not recorded. The same code as run 4, with the rule on |
| 6 | `2026-11-16-haiku` | Commit not recorded. Ran with `640a334`, which adds the one-grant rule |
| 7 | `2026-11-16-0b17231-haiku-validation` | `0b17231` |
| 8 | `2026-11-16-0b17231-sonnet-validation` | `0b17231` |
| 9 | `2026-11-16-b817e83-haiku-validation` | `b817e83` |
| 10 | `2026-11-16-b817e83-sonnet-validation` | `b817e83` |
| 11 | `2026-11-17-971486d-haiku-validation` | `971486d`. The first run whose records keep the rule that refused a call |
| 12 | `2026-11-17-971486d-sonnet-validation` | `971486d` |
| Validation at `971486d`, Haiku, settle rule and one-grant rule left out | `2026-11-17-971486d-haiku-validation-rules-out` | `971486d` |
| Test set at `0b17231`, Haiku | `2026-11-16-0b17231-haiku-test` | `0b17231` |
| Test set at `0b17231`, Sonnet | `2026-11-16-0b17231-sonnet-test` | `0b17231` |
| Test set at `b817e83`, Haiku | `2026-11-16-b817e83-haiku-test` | `b817e83` |
| Test set at `b817e83`, Sonnet | `2026-11-16-b817e83-sonnet-test` | `b817e83` |
| Test set at `971486d`, Haiku | `2026-11-17-971486d-haiku-test` | `971486d` |
| Test set at `971486d`, Haiku, settle rule and one-grant rule left out | `2026-11-17-971486d-haiku-test-rules-out` | `971486d` |
| Test set at `971486d`, Sonnet | `2026-11-17-971486d-sonnet-test` | `971486d` |
| Test set at `971486d`, Sonnet, settle rule and one-grant rule left out | `2026-11-17-971486d-sonnet-test-rules-out` | `971486d` |
| Finance reports request, before the hand-back fix | `2026-11-16-9dec77f-haiku-finance-reports-before` | `9dec77f` |
| Finance reports request, after it | `2026-11-16-0b17231-haiku-finance-reports-after` | `0b17231` |
| Development probes, before the one-grant rule | `2026-11-16-haiku-probes-before-one-grant-rule` | Commit not recorded. Development probes on 2026-11-16 |
| Development probes, after it | `2026-11-16-haiku-probes-after-one-grant-rule` | Commit not recorded. Development probes on 2026-11-16 |
| Development tasks at `b817e83` | `2026-11-16-b817e83-haiku-development` | `b817e83` |
| Development probes at `b817e83` | `2026-11-16-b817e83-haiku-probes` | `b817e83` |

For every other folder, the commit is in the folder's name, and from `971486d` on it is in the run's `meta.json`
too. Earlier records carry no commit and no date, so
for runs 1 to 6 the column gives the change each run was made to measure, from the dated notes in
`docs/eval-pass-criteria.md`.
