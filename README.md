# access-request-agent

By QuantumCortex.AI.

A worked example for our agentic engineering series: one IT access request, built as a fixed workflow and as an
agent, and measured on the same eval set.

Status: private and in progress. Nothing here is measured yet.

## What's simulated

The company, its people and its groups are generated. The directory is a local SQLite file, and the approver is
simulated. Nothing here talks to a real directory.

## Levels

Pick how deep you want to go. Each level builds on the one before.

1. Local: the workflow, the agent, the eval set and the results table. You need Python and a model API key.
2. MCP: the same tools, served as an MCP server.
3. Azure: a Terraform module that deploys it for a few dollars a month.

Level 1 is being built. Levels 2 and 3 aren't started.

## What's here so far

The part with no model in it:

- A generated company, Larkspur Freight, with the awkward cases built in: people who share a name, groups whose names
  differ by a word, a restricted group with no owner, and inactive accounts.
- Four tools with typed inputs: `lookup_user`, `find_groups`, `check_membership` and `add_to_group`.
- One gateway that every tool call goes through. It checks the input, checks the policy and writes an audit row.
- Policy rules in `policy/rules.toml`, deny by default.
- An audit log that can't be changed or deleted.

Still to come in level 1: the workflow, the agent, the approval step, the eval set and the results table.

## Run the tests

```bash
pip install -e ".[dev]"
pytest -q
```

## How we'll measure

`docs/eval-pass-criteria.md` says what counts as a pass. It's written before the first run.
