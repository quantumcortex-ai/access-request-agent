# 0002. Two arms in one framework, and the SDK for the model

- Status: Accepted
- Date: 2026-11-14

## Context
The repo compares a fixed workflow with an agent. If each were built in a different framework, a difference in
results could come from the framework. The model also has to be reachable two ways: with a reader's API key, and with
keyless sign-in to Claude on Microsoft Foundry.

## Decision
- Both arms are LangGraph graphs written by hand as `StateGraph`s. No prebuilt agent.
- The model is called through the Anthropic SDK inside the nodes, behind a small `Model` protocol. `ANTHROPIC_API_KEY`
  picks the Anthropic API. `FOUNDRY_RESOURCE` picks Foundry with an Entra ID token.
- The approval is a LangGraph `interrupt` in a node of its own. LangGraph runs a node again from its first line when
  the answer arrives, so that node does nothing before the interrupt.
- The agent is forced to call a tool on every turn and ends by calling `finish`. It gets 12 steps.
- Tests use a scripted stand-in for the model.

## Consequences
- The comparison is about the pattern. Both arms share the tools, the gateway, the policy and the approval step.
- Token counts come straight from the SDK, so cost per task is exact.
- A reader needs no tracing account. Tracing can be added later without changing how the numbers are counted.
- We carry our own tool loop, about 100 lines, in place of a framework's. It's the part readers most need to see.
- LangChain's model wrappers and callbacks aren't in play, so tools that hook into them need an adapter.

## Amended 2026-11-17
Two lines above say more than is true.

- "The agent is forced to call a tool on every turn" holds for `claude-haiku-5-5`. `claude-sonnet-5-5` and the
  larger models refuse a forced tool call, so for them the arm asks for one in the system prompt (`llm.py`). A
  comparison between models carries that difference.
- "The comparison is about the pattern" leaves out that the two arms have different prompts. The README's runs 4
  and 5 show a change to the agent's prompt causing wrong grants, so the prompts are part of what is compared.
