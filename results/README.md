# Results

One folder for each run. Each holds the run's report and its records. The run numbers are the ones the main
[README](../README.md) uses.

| Run | Folder | Code |
|---|---|---|
| 1 | `2026-11-15-haiku` | Commit not recorded. The first run, before `c1d31d5` |
| 2 | `2026-11-15-haiku-rerun` | Commit not recorded. Ran with `c1d31d5`, which adds models that refuse a forced tool call |
| 3 | `2026-11-15-sonnet` | Commit not recorded. The same code as run 2 |
| 4 | `2026-11-15-haiku-settle-rule-off` | Commit not recorded. Ran with `4e6aa51`, with the settle rule left out |
| 5 | `2026-11-15-haiku-settle-rule-on` | Commit not recorded. The same code as run 4, with the rule on |
| 6 | `2026-11-16-haiku` | Commit not recorded. Ran with `81d7af8`, which adds the one-grant rule |
| 7 | `2026-11-16-2f16bae-haiku-validation` | `2f16bae` |
| 8 | `2026-11-16-2f16bae-sonnet-validation` | `2f16bae` |
| 9 | `2026-11-16-1905b46-haiku-validation` | `1905b46` |
| 10 | `2026-11-16-1905b46-sonnet-validation` | `1905b46` |
| 11 | `2026-11-17-f7a8fa2-haiku-validation` | `f7a8fa2`. The first run whose records keep the rule that refused a call |
| 12 | `2026-11-17-f7a8fa2-sonnet-validation` | `f7a8fa2` |
| Validation at `f7a8fa2`, Haiku, settle rule and one-grant rule left out | `2026-11-17-f7a8fa2-haiku-validation-rules-out` | `f7a8fa2` |
| Test set at `2f16bae`, Haiku | `2026-11-16-2f16bae-haiku-test` | `2f16bae` |
| Test set at `2f16bae`, Sonnet | `2026-11-16-2f16bae-sonnet-test` | `2f16bae` |
| Test set at `1905b46`, Haiku | `2026-11-16-1905b46-haiku-test` | `1905b46` |
| Test set at `1905b46`, Sonnet | `2026-11-16-1905b46-sonnet-test` | `1905b46` |
| Test set at `f7a8fa2`, Haiku | `2026-11-17-f7a8fa2-haiku-test` | `f7a8fa2` |
| Test set at `f7a8fa2`, Haiku, settle rule and one-grant rule left out | `2026-11-17-f7a8fa2-haiku-test-rules-out` | `f7a8fa2` |
| Test set at `f7a8fa2`, Sonnet | `2026-11-17-f7a8fa2-sonnet-test` | `f7a8fa2` |
| Test set at `f7a8fa2`, Sonnet, settle rule and one-grant rule left out | `2026-11-17-f7a8fa2-sonnet-test-rules-out` | `f7a8fa2` |
| Finance reports request, before the hand-back fix | `2026-11-16-4f7d468-haiku-finance-reports-before` | `4f7d468` |
| Finance reports request, after it | `2026-11-16-2f16bae-haiku-finance-reports-after` | `2f16bae` |
| Development probes, before the one-grant rule | `2026-11-16-haiku-probes-before-one-grant-rule` | Commit not recorded. Development probes on 2026-11-16 |
| Development probes, after it | `2026-11-16-haiku-probes-after-one-grant-rule` | Commit not recorded. Development probes on 2026-11-16 |
| Development tasks at `1905b46` | `2026-11-16-1905b46-haiku-development` | `1905b46` |
| Development probes at `1905b46` | `2026-11-16-1905b46-haiku-probes` | `1905b46` |
| Release gate: control, validation | `2026-11-18-a8f284d-haiku-gate-control` | `a8f284d`. Gate exit 0 |
| Release gate drill: pilot on the development probes, one-grant rule out | `2026-11-18-6ba2030-haiku-drill-probes-pilot` | `6ba2030`, tag `drill-2026-11-18`: `a8f284d` with the agent's instructions from `4e6aa51` |
| Release gate drill: validation, every rule on | `2026-11-18-6ba2030-haiku-drill-rules-on` | `6ba2030`. Gate exit 2 |
| Release gate drill: validation, settle and one-grant rules out | `2026-11-18-6ba2030-haiku-drill-two-rules-out` | `6ba2030`. Gate exit 1 |

Where a folder's name has a commit, that's the commit the run scored, and from `f7a8fa2` on the run's `meta.json`
names it too. Earlier records carry no commit and no date, so for runs 1 to 6 and the two probe runs the last
column gives the change each run was made to measure, from the dated notes in
[`docs/eval-pass-criteria.md`](../docs/eval-pass-criteria.md).

From 2026-11-18, `meta.json` also records a hash of the prompts and tool schemas, a hash of the rules, the provider
and the model ids the API returned. A gated run's folder holds the gate's `gate.md` and `gate.json`, scored against
run 11. Each drill folder holds `change.patch`, the whole difference between the drill commit and `a8f284d`. The
drill commit was never merged. The tag keeps it.
