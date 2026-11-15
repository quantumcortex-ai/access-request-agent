# access-request-agent

By QuantumCortex.AI.

A worked example for our agentic engineering series: one IT access request, built as a fixed workflow and as an
agent, and measured on the same eval set.

Status: private and in progress. Nothing here is measured yet.

## How it works

A request goes to one of two arms. Both use the same tools, and every tool call passes through one gateway, which
checks it against the policy and writes an audit row whether the call is allowed or refused.

```mermaid
flowchart TB
    R([Access request]) --> W
    R --> A

    subgraph arms [Two arms]
        W[Workflow<br/>fixed steps, model called at two set points]
        A[Agent<br/>model picks each next step]
    end

    W -- tool call --> V
    A -- tool call --> V

    subgraph gateway [The gateway]
        V[Check the input] --> F[Read the facts]
        F --> P{Does a rule<br/>allow it?}
        P -- yes --> X[Act]
        P -- no --> D[Refuse and name the rule]
        X --> L[Write the audit row]
        D --> L
    end

    RULES[/policy/rules.toml<br/>deny by default/] -.-> P
    F -.-> DIR[(Directory<br/>users, groups, members, approvals)]
    X -. adds the member .-> DIR
    L --> AUD[(Audit log<br/>append-only)]

    W -. restricted group .-> AP[Approval step<br/>pauses until the group's owner answers]
    A -. restricted group .-> AP
    AP -. records the answer .-> DIR

    AUD --> EV[Eval script<br/>every number comes from here]
```

- Neither arm can reach the directory except through the gateway.
- Policy facts are read from the directory. Nothing the model says counts as one.
- An approval is recorded by the approval step, never by a tool the model can call.

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

- The eval set (`tasks/tasks.jsonl`): 130 requests with the end state a careful person would reach. More than half
  are hard cases.
- The eval script (`eval.py`): runs both arms on the set and prints the numbers.

Still to come in level 1: the first scored run and its results table.

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

## Run the eval

```bash
python -m access_agent.eval --arm both --split dev          # the 26 dev tasks, for a quick look
python -m access_agent.eval --arm both --repeats 3          # the 104 test tasks, three times each
python -m access_agent.eval --report runs/<run id>          # print a finished run's table again
```

Each run is saved under `runs/`. A run that stops can be continued with `--run-id`. Cost per completed task uses the
list prices in `tasks/prices.toml`, so change those to what you pay.

A full run on a rate-limited account takes a while: the script waits out each limit and carries on.

## Run the tests

The tests use a scripted stand-in for the model, so they need no API key.

```bash
pytest -q
```

## How we'll measure

`docs/eval-pass-criteria.md` says what counts as a pass. It's written before the first run.
