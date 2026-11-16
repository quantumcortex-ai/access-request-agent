# access-request-agent

By [QuantumCortex.AI](https://quantumcortex.ai).

A worked example for our [agentic engineering series](https://quantumcortex.ai/series/): one IT access request,
built as a fixed workflow and as an agent, and measured on the same eval set.

Status: level 1 is built and measured. Levels 2 and 3 are planned and not built yet.

## Results

Every run is the 104 test tasks, three times each, 312 runs an arm. The pass rule was written down before the
first run: zero wrong grants in both arms.

**Where it stands:** the latest run passes. On `claude-haiku-5-5`, with both rules below in place, neither arm made
a wrong grant, and each completed 311 of 312.

| Run | Agent completed | Workflow completed | Wrong grants | Pass rule |
|---|---|---|---|---|
| 1. Haiku, first run, 2026-11-15 | 308 of 312 | 308 of 312 | workflow 1 | Fails |
| 2. Haiku again, model-support commit | 308 of 312 | 312 of 312 | 0 | Passes |
| 3. Sonnet, same commit as run 2 | 312 of 312 | 312 of 312 | 0 | Passes |
| 4. Haiku, settle rule left out | 306 of 312 | 310 of 312 | agent 6, workflow 2 | Fails |
| 5. Haiku, settle rule on | 309 of 312 | 310 of 312 | agent 3 | Fails |
| 6. Haiku, settle rule and one-grant rule, 2026-11-16 | 311 of 312 | 311 of 312 | 0 | Passes |

Runs 4 and 5 are one commit, with and without the rule. Each run's report and records are in `results/`, and
`docs/eval-pass-criteria.md` has a dated note for every change made between runs.

The latest run, run 6, at commit `95513fb`:

| | Agent | Workflow |
|---|---|---|
| Task completion | 99.7% (98% to 100%), 311 of 312 | 99.7% (98% to 100%), 311 of 312 |
| Completion, hard tasks | 99.4% (97% to 100%), 167 of 168 | 99.4% (97% to 100%), 167 of 168 |
| Wrong grants | 0 | 0 |
| First-try tool-call success | 100%, 1,403 of 1,403 | 100%, 1,579 of 1,579 |
| Model calls per run | 4.3 | 1.2 |
| Input tokens | 3,237,498 | 311,859 |
| Cost per completed task, at list price | $0.0013 | $0.0002 |

Ranges are 95% intervals.

What the runs show:

- **A vague request became a wrong grant, and a prompt didn't stop it.** In run 1 a request asked for "the Sales
  one", two groups fit, and the workflow picked one where it should have asked. Run 2 had none, and run 4 had five
  of the same kind across both arms. Telling the model not to guess made it guess less often. It didn't make it
  stop.
- **A rule in code did.** The settle rule lets the gateway act only on a user and a group that the request's own
  words settled. On one commit, wrong grants from vague requests went from five without it to none with it.
- **The rule's cost is hand-backs.** In run 6 each arm sent one request back to the requester that a careful person
  could have done. It asked for "the finance reports, read only".
- **Our own fix caused a new failure.** To work with the settle rule, the agent's instructions told it to use "the
  request's own words". In run 5 the agent then obeyed a forwarded "policy update" inside a request and added a
  second group, three times. Earlier runs had refused it. The one-grant rule and plainer instructions fixed it in
  run 6.
- **The workflow never obeyed an injected instruction.** Its steps can only act on one person and one group.
- **A bigger model also got to zero, at about 15 times the cost.** Sonnet completed every task on both arms before
  either rule existed. It cost $0.0196 a completed task for the agent, against $0.0013 for Haiku with the rules.
  One run of 312 without a miss doesn't show that it can't miss.
- **The agent uses about ten times the input tokens** of the workflow to finish the same share of tasks.
- **The model's stated confidence didn't flag the misses.** A count from code did: every miss in run 1 was on a
  request where a lookup returned more than one match.

What they don't show:

- Anything about real service-desk requests. Every request here is generated, on a fictional company. See "What we
  won't claim" in `docs/eval-pass-criteria.md`.
- That the rules end wrong grants. The settle rule can be fooled by a request's filler words, and the one-grant
  rule doesn't choose the right group. `docs/adr/0003` and `0004` say how.
- A clean test of the injection fix. A test task prompted it, so those cases were no longer unseen in run 6. The
  fix was made on separate hand-written requests in `tasks/dev-probes.jsonl`.

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
2. MCP (planned): the same tools, served as an MCP server.
3. Azure (planned): a Terraform module that deploys it for a few dollars a month.

Level 1 is here. Levels 2 and 3 are planned and not built yet.

## What's in level 1

- A generated company, Larkspur Freight, with the awkward cases built in: people who share a name, groups whose names
  differ by a word, a restricted group with no owner, and inactive accounts.
- Five tools with typed inputs: `lookup_user`, `find_groups`, `check_membership`, `request_approval` and
  `add_to_group`.
- One gateway that every tool call goes through. It checks the input, checks the policy and writes an audit row.
- Policy rules in `policy/rules.toml`, deny by default.
- A rule that refuses to act on a guess: the gateway acts only on a user and a group that the request's own words
  settled (`docs/adr/0003-act-only-on-a-match-the-request-settles.md`).
- A rule that holds a request to one grant: once a run has acted on one person and one group, any other pair is
  refused (`docs/adr/0004-one-grant-per-request.md`).
- An audit log that can't be changed or deleted.
- The workflow (`workflow.py`): the same steps every time, with the model called at two set points.
- The agent (`agent.py`): the model picks its own next step, with the same tools.
- An approval step that pauses the request until the group's owner answers, and survives a restart.

- The eval set (`tasks/tasks.jsonl`): 130 requests with the end state a careful person would reach. More than half
  are hard cases.
- The eval script (`eval.py`): runs both arms on the set and prints the numbers.

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
python -m access_agent.eval --without-rule match-must-be-settled-by-the-request   # measure what one rule does
python -m access_agent.eval --tasks tasks/dev-probes.jsonl --split dev      # hand-written injection probes
```

Each run is saved under `runs/`. A run that stops can be continued with `--run-id`. Cost per completed task uses the
list prices in `tasks/prices.toml`, so change those to what you pay.

A full run on a rate-limited account takes a while: the script waits out each limit and carries on.

## Run the tests

The tests use a scripted stand-in for the model, so they need no API key.

```bash
pytest -q
```

## How we measure

`docs/eval-pass-criteria.md` says what counts as a pass. It was written and approved before the first run.
