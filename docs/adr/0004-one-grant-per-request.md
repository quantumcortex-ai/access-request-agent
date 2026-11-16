# 0004. One grant per request

- Status: Accepted
- Date: 2026-11-16

## Context
A request asks to add one person to one group. The agent was told so in its instructions, and that was the only
thing holding it to one. In the scored run of 2026-11-15 the agent read a forwarded "policy update" inside a
request as policy and added a second group, in all three repeats of that task. Four hand-written dev requests of
the same shape (`tasks/dev-probes.jsonl`) reproduced it: 7 wrong grants in 12 agent runs. The settle rule
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

The test set (`tasks/test.jsonl`) measured both sides of this rule. On ten requests that try to add a second
group or person, neither arm made a wrong grant on either model. On eight requests that swap the ask for a different
group or person, the workflow on `claude-haiku-5-5` granted the swap in six of 24 runs. This rule doesn't choose the
first grant, so it can't stop that. Nothing in level 1 was changed in response.
