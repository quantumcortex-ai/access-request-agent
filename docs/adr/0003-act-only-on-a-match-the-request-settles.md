# 0003. Act only on a match the request settles

- Status: Accepted
- Date: 2026-11-15

## Context
In the first scored run every miss, in both arms, came from a request where a search returned more than one record:
two people with one name, or "the Sales one" when there are two Sales groups. The prompt told the model not to
guess. It guessed anyway, rarely, and one guess became a wrong grant. A stronger model may guess less often, but
"less often" isn't a control. The model's stated confidence wasn't a dependable flag either: the workflow's was
below 80 on all four of its misses and on 59 runs it completed, and the agent's was below 80 on none of its four.

## Decision
- Whether a match is settled is a fact the gateway works out. It is never taken from the model.
- A user or a group is settled when it was the only result of a search and every word of that search appears in the
  request. A search that uses a word the request doesn't contain is the caller's guess and settles nothing.
- `lookup_user` takes an optional department, so "Jo Bianchi (Legal)" can be settled by the request's own words.
- The policy gets one deny rule, `match-must-be-settled-by-the-request`, on `request_approval` and `add_to_group`.
  It sits in `policy/rules.toml` with the other rules.
- The gateway is given the request by the code that starts a run. With no request, nothing is settled.
- Both arms end a request the rule refuses with `needs_clarification`.
- The eval can leave a named rule out (`--without-rule`), so a rule's effect is measured on the same commit.

## Consequences
- A guess can no longer reach the directory by way of a pick alone. It shows in the audit log as a refused call
  with the rule's name.
- More requests go back to the requester. That is the trade: fewer wrong grants for more hand-backs, and the
  results table reports both.
- The rule is a narrowing, not a proof. A request's filler words can happen to pick out one group: "needs access
  to the Sales one" contains "access", which matches only one of the two Sales groups. A caller that searches
  "access sales" gets a settled match the request didn't give. `tests/test_settle.py` keeps that case visible.
- The rule depends on how search works here: every word must match a group's name or description. A directory with
  fuzzier search would need a different test of "settled".
- Both arms changed to work with it: the workflow records a department and searches again after a pick, and the
  agent's instructions say how a match is settled. Those changes were made on the development tasks only.

## Amended 2026-11-16
A group's exact name settles that group when the request contains the name as a word of its own, even if the name
is also the start of another group's name (ADR 0004).

## Amended 2026-11-16, second time
Two fixes from a review of the code, scored as runs 9 and 10.

- A search word counts as in the request only as a word of its own. Before, the check looked for the letters
  anywhere, so "ops" counted as present in a request that said "laptops". A hyphen, a dot or an apostrophe ends a
  word, so "finance" is in "Finance-Reports".
- What the request settled, and the pair the run acted on (ADR 0004), are kept in the directory's database, keyed
  by the run and the request's text. A request that pauses for an approval can be finished by a new process.
