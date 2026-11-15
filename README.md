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

- A generated company, Larkspur Freight, with the awkward cases built in: people who share a name, groups whose names
  differ by a word, a restricted group with no owner, and inactive accounts.
- Five tools with typed inputs: `lookup_user`, `find_groups`, `check_membership`, `request_approval` and
  `add_to_group`.
- One gateway that every tool call goes through. It checks the input, checks the policy and writes an audit row.
- Policy rules in `policy/rules.toml`, deny by default.
- An audit log that can't be changed or deleted.
- The workflow (`workflow.py`): the same steps every time, with the model called at two set points.
- The agent (`agent.py`): the model picks its own next step, with the same tools.
- An approval step that pauses the request until the group's owner answers, and survives a restart.

Still to come in level 1: the eval set and the results table.

## Try one request

```bash
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=...        # or see "Claude on Foundry" below
python -m access_agent.cli --arm workflow "Please add Sam Carter from Sales to the sales team group"
python -m access_agent.cli --arm agent "Add Sam Carter (Finance) to payroll please"
```

It prints each tool call, the rule that allowed or refused it, how the request ended and the tokens used. When a
group needs its owner's approval, it asks you. The company is generated in memory each time, so nothing is kept.

The model defaults to `claude-haiku-5-5`. Set `ACCESS_AGENT_MODEL` to change it.

### Claude on Foundry

To sign in to Claude on Microsoft Foundry with no API key:

```bash
pip install -e ".[dev,foundry]"
az login
export FOUNDRY_RESOURCE=<your Foundry resource name>
```

## Run the tests

The tests use a scripted stand-in for the model, so they need no API key.

```bash
pytest -q
```

## How we'll measure

`docs/eval-pass-criteria.md` says what counts as a pass. It's written before the first run.
