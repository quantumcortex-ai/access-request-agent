# Results

One folder for each run. Each holds the run's report and its records. The run numbers are the ones the main
[README](../README.md) uses.

| Run | Folder | Code |
|---|---|---|
| 1 | `2026-11-15-haiku` | Commit not recorded. The first run, before `4cb22bc` |
| 2 | `2026-11-15-haiku-rerun` | Commit not recorded. Ran with `4cb22bc`, which adds models that refuse a forced tool call |
| 3 | `2026-11-15-sonnet` | Commit not recorded. The same code as run 2 |
| 4 | `2026-11-15-haiku-settle-rule-off` | Commit not recorded. Ran with `490d0f9`, with the settle rule left out |
| 5 | `2026-11-15-haiku-settle-rule-on` | Commit not recorded. The same code as run 4, with the rule on |
| 6 | `2026-11-16-haiku` | Commit not recorded. Ran with `eebfa4b`, which adds the one-grant rule |
| 7 | `2026-11-16-48e5a16-haiku-validation` | `48e5a16` |
| 8 | `2026-11-16-48e5a16-sonnet-validation` | `48e5a16` |
| 9 | `2026-11-16-3a1c2f1-haiku-validation` | `3a1c2f1` |
| 10 | `2026-11-16-3a1c2f1-sonnet-validation` | `3a1c2f1` |
| 11 | `2026-11-17-eb2dc55-haiku-validation` | `eb2dc55`. The first run whose records keep the rule that refused a call |
| 12 | `2026-11-17-eb2dc55-sonnet-validation` | `eb2dc55` |
| Validation at `eb2dc55`, Haiku, settle rule and one-grant rule left out | `2026-11-17-eb2dc55-haiku-validation-rules-out` | `eb2dc55` |
| Test set at `48e5a16`, Haiku | `2026-11-16-48e5a16-haiku-test` | `48e5a16` |
| Test set at `48e5a16`, Sonnet | `2026-11-16-48e5a16-sonnet-test` | `48e5a16` |
| Test set at `3a1c2f1`, Haiku | `2026-11-16-3a1c2f1-haiku-test` | `3a1c2f1` |
| Test set at `3a1c2f1`, Sonnet | `2026-11-16-3a1c2f1-sonnet-test` | `3a1c2f1` |
| Test set at `eb2dc55`, Haiku | `2026-11-17-eb2dc55-haiku-test` | `eb2dc55` |
| Test set at `eb2dc55`, Haiku, settle rule and one-grant rule left out | `2026-11-17-eb2dc55-haiku-test-rules-out` | `eb2dc55` |
| Test set at `eb2dc55`, Sonnet | `2026-11-17-eb2dc55-sonnet-test` | `eb2dc55` |
| Test set at `eb2dc55`, Sonnet, settle rule and one-grant rule left out | `2026-11-17-eb2dc55-sonnet-test-rules-out` | `eb2dc55` |
| Finance reports request, before the hand-back fix | `2026-11-16-bf87eac-haiku-finance-reports-before` | `bf87eac` |
| Finance reports request, after it | `2026-11-16-48e5a16-haiku-finance-reports-after` | `48e5a16` |
| Development probes, before the one-grant rule | `2026-11-16-haiku-probes-before-one-grant-rule` | Commit not recorded. Development probes on 2026-11-16 |
| Development probes, after it | `2026-11-16-haiku-probes-after-one-grant-rule` | Commit not recorded. Development probes on 2026-11-16 |
| Development tasks at `3a1c2f1` | `2026-11-16-3a1c2f1-haiku-development` | `3a1c2f1` |
| Development probes at `3a1c2f1` | `2026-11-16-3a1c2f1-haiku-probes` | `3a1c2f1` |
| Release gate: control, validation | `2026-11-18-452f8c2-haiku-gate-control` | `452f8c2`. Gate exit 0 |
| Release gate drill: pilot on the development probes, one-grant rule out | `2026-11-18-f065586-haiku-drill-probes-pilot` | `f065586`, tag `drill-2026-11-18`: `452f8c2` with the agent's instructions from `490d0f9` |
| Release gate drill: validation, every rule on | `2026-11-18-f065586-haiku-drill-rules-on` | `f065586`. Gate exit 2 |
| Release gate drill: validation, settle and one-grant rules out | `2026-11-18-f065586-haiku-drill-two-rules-out` | `f065586`. Gate exit 1 |

Where a folder's name has a commit, that's the commit the run scored, and from `eb2dc55` on the run's `meta.json`
names it too. Earlier records carry no commit and no date, so for runs 1 to 6 and the two probe runs the last
column gives the change each run was made to measure, from the dated notes in
[`docs/eval-pass-criteria.md`](../docs/eval-pass-criteria.md).

From 2026-11-18, `meta.json` also records a hash of the prompts and tool schemas, a hash of the rules, the provider
and the model ids the API returned. A gated run's folder holds the gate's `gate.md` and `gate.json`, scored against
run 11. Each drill folder holds `change.patch`, the whole difference between the drill commit and `452f8c2`. The
drill commit was never merged. The tag keeps it.
