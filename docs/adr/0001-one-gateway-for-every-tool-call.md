# 0001. One gateway for every tool call

- Status: Accepted
- Date: 2026-11-14

## Context
The repo compares a fixed workflow with an agent on the same task. The comparison is only fair if both are held to
the same rules and measured the same way. The series also says governance belongs in the runtime path: a sentence in
a prompt doesn't count.

## Decision
Every tool call, from either arm, goes through `Gateway.call`. It validates the typed input, works out the facts
from the directory, checks the policy rules, acts, and writes an audit row. It does this for every call, allowed or
not.

- Tool inputs are IDs with a fixed shape. A name where an ID belongs is `invalid_input`.
- Policy is deny by default, in `policy/rules.toml`. The model supplies no facts: tier, status, department and
  approval all come from the directory.
- Approvals are written by the approval step. No tool the model can call writes one.
- The audit table refuses updates and deletes.
- The directory is a local SQLite file. No code here talks to a real directory.

## Consequences
- First-try tool-call success is counted at the gateway, from the audit table, the same way for both arms.
- A framework change, or serving the tools over MCP in stage 2, doesn't move the rules or the measurement.
- Policy rules stay simple: lists of allowed values per fact. A richer policy language can replace `decide` later
  without touching the tools.
- The gateway is the one place a bug could grant access wrongly, so it carries the most tests.
