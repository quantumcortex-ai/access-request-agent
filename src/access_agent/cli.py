"""Try one request from the command line.

    python -m access_agent.cli --arm agent "Please add Sam Carter in Sales to the sales team group"

The company is generated fresh in memory each time, so nothing is kept.
"""

from __future__ import annotations

import argparse
import uuid
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from . import agent, workflow
from .approval import owner_says, run
from .directory import Directory
from .gateway import Gateway
from .llm import ClaudeModel
from .seed import seed


def ask_on_terminal(question: dict[str, Any]) -> dict[str, Any]:
    prompt = f"Approve adding {question['user_name']} to {question['group_name']}? [y/N] "
    try:
        answer = input(prompt)
    except EOFError:
        # Nobody is at the terminal (piped or closed input). No answer is a no.
        print("no answer, so not approved")
        answer = ""
    return {"approved": answer.strip().lower() == "y", "approver_id": question["approver_id"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("request", help="The access request, in plain words.")
    parser.add_argument("--arm", choices=["workflow", "agent"], default="workflow")
    parser.add_argument("--approve", choices=["ask", "yes", "no"], default="ask", help="How the group's owner answers.")
    args = parser.parse_args()

    directory = Directory()
    seed(directory)
    arm = agent if args.arm == "agent" else workflow
    gateway = Gateway(directory, actor=arm.ACTOR, run_id=uuid.uuid4().hex[:8])
    try:
        model = ClaudeModel()
    except RuntimeError as exc:
        # No key and no Foundry resource: say what to set, without a traceback.
        raise SystemExit(str(exc)) from None
    build = agent.build_agent if args.arm == "agent" else workflow.build_workflow
    graph = build(gateway, model, InMemorySaver())
    approver = ask_on_terminal if args.approve == "ask" else owner_says(args.approve == "yes")

    final = run(graph, {"task_id": "cli", "request": args.request}, thread_id="cli", approver=approver)

    print(f"\n{args.arm} on {model.name}")
    for row in gateway.audit.rows():
        rule = f"  [{row['rule_id']}]" if row["rule_id"] else ""
        print(f"  {row['tool']:<17} {row['outcome']:<14} {row['args']}{rule}")
    print(f"outcome: {final.get('outcome')}  {final.get('note') or ''}".rstrip())
    calls, tokens_in, tokens_out = (final.get(k, 0) for k in ("model_calls", "input_tokens", "output_tokens"))
    print(f"model calls: {calls}, tokens in/out: {tokens_in}/{tokens_out}")


if __name__ == "__main__":
    main()
