# CLAUDE.md

One IT access request, built as a fixed workflow and as an agent, measured on one eval set. Companion to the
QuantumCortex.AI agentic engineering series.

## Rules
- Generated data only. The company is fictional. Never add names, policies or designs from a real organization.
- No code that talks to a real directory or identity system. The directory is the local SQLite file.
- Never read or copy from `agent-stack-lab` or any other earlier repo. This one is written fresh.
- No person is named in the README or docs. The byline is QuantumCortex.AI.
- Never state a result that wasn't measured. The README has no results table until a run produces one.
- `docs/eval-pass-criteria.md` is fixed before the first run. Changes after that get a dated note.
- Private until the maintainer says otherwise.

## Working here
- Python 3.12, virtualenv `access-request-agent-env`. `pip install -e ".[dev]"`.
- Before a commit: `ruff check . && ruff format --check . && pytest -q`.
- Never commit to main. Branch, PR, and the maintainer merges.
- Decisions are in `docs/adr/`.

## Layout
- `src/access_agent/gateway.py`: the one path every tool call takes (ADR 0001). It also works out whether the
  request settled the user and the group (ADR 0003). That fact never comes from the model.
- `src/access_agent/policy.py` and `policy/rules.toml`: deny-by-default rules.
- `src/access_agent/directory.py` and `seed.py`: the generated company.
- `src/access_agent/audit.py`: the append-only log the eval reads.
- `src/access_agent/workflow.py` and `agent.py`: the two arms (ADR 0002). `approval.py`: the pause for the owner.
- `src/access_agent/tasks.py` builds `tasks/tasks.jsonl`. Labels come from how each case is built, never from running
  the gateway. After a change, run `python -m access_agent.tasks` and commit the file.
- `src/access_agent/eval.py`: runs the set and reports. Dev tasks are for debugging. Never adjust an arm against a
  test task.
- `src/access_agent/llm.py`: the model client. Tests use `ScriptedModel`, never a live model.
