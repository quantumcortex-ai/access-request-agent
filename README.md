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

1. **Local.** The workflow, the agent, the eval set and the results table. You need Python and a model API key.
2. **MCP.** The same tools, served as an MCP server.
3. **Azure.** A Terraform module that deploys it for a few dollars a month.

Level 1 is being built. Levels 2 and 3 aren't started.
