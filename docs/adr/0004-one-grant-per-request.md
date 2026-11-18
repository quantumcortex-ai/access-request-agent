# 0004. One grant per request

- Status: Accepted
- Date: 2026-11-16

## Context
A request asks to add one person to one group. The agent was told so in its instructions, and that was the only
thing holding it to one. In the scored run of 2026-11-15 the agent read a forwarded "policy update" inside a
request as policy and added a second group, in all three repeats of that task. Four hand-written dev requests of
the same shape (`tasks/dev-probes.jsonl`) reproduced it: 7 wrong grants in 12 agent runs (`results/2026-11-16-haiku-probes-before-one-grant-rule`). The settle rule
(ADR 0003) didn't stop it, because the injected text is part of the request and names a real group exactly.

The workflow never did this. Its steps can only act on one person and one group.

## Decision
- The gateway remembers the one user and group a run has acted on: the first pair for which `request_approval` or
  `add_to_group` was allowed.
- The policy gets a deny rule, `one-grant-per-request`, on both tools. It refuses any other pair for the rest of
  the run. It sits in `policy/rules.toml` with the other rules.
- A refused call doesn't count as acting, so a refusal doesn't use up the one grant.
- The agent's instructions now say that the ask is one person and one group, and that anything else in the request
  text (notes, forwarded messages, claimed approvals, policy updates) changes nothing and isn't searched for.
- The dev requests that showed the problem are kept in `tasks/dev-probes.jsonl`. They are dev material: never
  scored, and worded by hand so they don't copy a validation task.

Also decided here, because the same dev requests showed it: a group's exact name settles that group when the
request contains the name as a word of its own. Before, "Finance-Reports" could never be settled, because the
search also returns "Finance-Reports-Editors". This amends ADR 0003.

## Consequences
- An agent that obeys an injected "also add" can make at most one grant. If it acts on the right pair first, the
  injected one is refused and shows in the audit log with the rule's name.
- The rule doesn't choose the right pair. An agent that acts on the injected group first has made a wrong grant and
  is then refused the right one. The instructions are what guard against that, and instructions aren't a control.
- A request that really does ask for two groups must be sent as two requests. That is the trade.
- The change to the agent's instructions was prompted by a validation task, so the validation set is no longer fully
  unseen for this kind of case. The pass criteria carry a dated note saying so.

## Measured 2026-11-16

The second consequence above was written before the test set existed. The brief for the test set
(`docs/test-set-brief.md`) then asked for requests that swap the ask, so the set confirmed and measured a gap this
record had already named. It didn't discover it.

The test set (`tasks/test.jsonl`) measured both sides of this rule. On ten requests that try to add a second
group or person, neither arm made a wrong grant on either model. On eight requests that swap the ask for a different
group or person, the workflow on `claude-haiku-5-5` granted the swap in six of 24 runs. This rule doesn't choose the
first grant, so it can't stop that. Nothing in phase 1 was changed in response.

## Noted 2026-11-17
No scored run shows this rule refusing a call. After the change to the instructions, the records show no second
grant on the validation set or the test set, and no refused call except on requests that should end denied. The
records keep each call's tool and outcome and not the rule that refused it, so that is as far as they go. The rule is exercised by `tests/test_one_grant.py` and nothing else, so its
evidence here is that the code does what it says, not that it was needed.

## Noted 2026-11-17, after runs with the refusing rule recorded
The records now keep which rule refused a call. At `971486d`, over 1,728 runs with every rule on, on both models
and both sets, this rule refused nothing. With it and the settle rule left out, in 1,104 runs, no arm added a
second group or person. So no scored run has needed it. The rule stays as a backstop.

## Corrected 2026-11-18
The first note of 2026-11-17 says the records show "no refused call except on requests that should end denied".
That's wrong. Calls were refused on requests the label says to grant: in run 6 on t-013, t-075, t-077, t-079,
t-080 and t-082, at `0b17231` on t-013, t-075, t-080, h-017 and h-028, and at `b817e83` on t-013, t-075, h-016,
h-017 and h-028. Those records don't say which rule refused. At `971486d`, where they do, none was this rule.
