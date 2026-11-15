"""The approval step: ask the group's owner, then record the answer.

`interrupt` stops the graph and hands the question to whoever runs it. Nothing
is running while the owner decides. When the answer comes back, LangGraph runs
the node again from its first line, so a node that calls `ask_owner` must do
nothing before it that shouldn't happen twice.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langgraph.types import Command, interrupt

from .directory import Directory

Approver = Callable[[dict[str, Any]], dict[str, Any]]


def ask_owner(directory: Directory, request: dict[str, Any]) -> dict[str, Any]:
    """Pause for a decision on one user and one group, and write it down.

    `request` is the data the gateway returned for `request_approval`, so the
    approver named in it is the group's owner as the directory has it. The
    answer says who actually decided. If that isn't the owner, the record says
    so, and the gateway won't accept it.
    """
    user = directory.get_user(request["user_id"])
    group = directory.get_group(request["group_id"])
    answer = interrupt(
        {
            "kind": "approval",
            "user_id": request["user_id"],
            "user_name": user.name if user else None,
            "group_id": request["group_id"],
            "group_name": group.name if group else None,
            "approver_id": request["approver_id"],
        }
    )
    if not isinstance(answer, dict) or "approved" not in answer or not answer.get("approver_id"):
        raise ValueError("An approval answer needs `approved` and `approver_id`.")
    approved = bool(answer["approved"])
    approver_id = str(answer["approver_id"])
    directory.record_approval(request["user_id"], request["group_id"], approver_id, approved)
    return {"approved": approved, "approver_id": approver_id}


def run(graph: Any, state: dict[str, Any], *, thread_id: str, approver: Approver) -> dict[str, Any]:
    """Run one request to its end, answering each approval question with `approver`."""
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(state, config)
    while result.get("__interrupt__"):
        question = result["__interrupt__"][0].value
        result = graph.invoke(Command(resume=approver(question)), config)
    return result


def owner_says(approved: bool) -> Approver:
    """A simulated owner who always gives the same answer."""

    def approver(question: dict[str, Any]) -> dict[str, Any]:
        return {"approved": approved, "approver_id": question["approver_id"]}

    return approver
