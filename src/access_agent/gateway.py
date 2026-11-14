"""The one path every tool call takes.

validate the input -> look up the facts -> check policy -> act -> write the audit row

The workflow and the agent both call tools through here, so both are held to
the same rules and measured from the same log.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ValidationError

from .audit import AuditLog
from .directory import Directory
from .models import (
    AddToGroupInput,
    CheckMembershipInput,
    ErrorCode,
    FindGroupsInput,
    Group,
    LookupUserInput,
    Tier,
    ToolResult,
    User,
)
from .policy import Rule, decide, load_rules

TOOL_INPUTS: dict[str, type[BaseModel]] = {
    "lookup_user": LookupUserInput,
    "find_groups": FindGroupsInput,
    "check_membership": CheckMembershipInput,
    "add_to_group": AddToGroupInput,
}


def _public_user(user: User) -> dict[str, Any]:
    return user.model_dump(mode="json")


def _public_group(group: Group) -> dict[str, Any]:
    data = group.model_dump(mode="json")
    data["allowed_departments"] = list(group.allowed_departments)
    return data


class Gateway:
    def __init__(
        self,
        directory: Directory,
        *,
        actor: str,
        run_id: str,
        rules: list[Rule] | None = None,
    ) -> None:
        self.directory = directory
        self.actor = actor
        self.run_id = run_id
        self.rules = rules if rules is not None else load_rules()
        self.audit = AuditLog(directory.conn)
        self._handlers: dict[str, Callable[[Any], ToolResult]] = {
            "lookup_user": self._lookup_user,
            "find_groups": self._find_groups,
            "check_membership": self._check_membership,
            "add_to_group": self._add_to_group,
        }

    def call(self, tool: str, args: dict[str, Any], *, task_id: str) -> ToolResult:
        """Run one tool call and record it, whatever happens."""
        result = self._run(tool, args)
        failure = result.error.value if result.error else "error"
        outcome = "ok" if result.ok else failure
        self.audit.write(
            run_id=self.run_id,
            task_id=task_id,
            actor=self.actor,
            tool=tool,
            args=args if isinstance(args, dict) else {"_raw": repr(args)},
            outcome=outcome,
            rule_id=result.rule_id,
            reason=result.reason,
        )
        return result

    def _run(self, tool: str, args: dict[str, Any]) -> ToolResult:
        model = TOOL_INPUTS.get(tool)
        if model is None:
            return ToolResult(ok=False, tool=tool, error=ErrorCode.UNKNOWN_TOOL, reason=f"No tool named {tool}.")
        try:
            parsed = model.model_validate(args)
        except ValidationError as exc:
            problems = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors())
            return ToolResult(ok=False, tool=tool, error=ErrorCode.INVALID_INPUT, reason=problems)
        return self._handlers[tool](parsed)

    def _denied(self, tool: str, rule_id: str, reason: str) -> ToolResult:
        return ToolResult(ok=False, tool=tool, error=ErrorCode.POLICY_DENIED, rule_id=rule_id, reason=reason)

    def _check(self, tool: str, facts: dict[str, str]) -> ToolResult | None:
        decision = decide(self.rules, self.actor, tool, facts)
        if decision.allowed:
            return None
        return self._denied(tool, decision.rule_id, decision.reason)

    def _lookup_user(self, args: LookupUserInput) -> ToolResult:
        denied = self._check("lookup_user", {})
        if denied:
            return denied
        users = self.directory.search_users(args.query)
        return ToolResult(
            ok=True, tool="lookup_user", rule_id="read-directory", data={"users": [_public_user(u) for u in users]}
        )

    def _find_groups(self, args: FindGroupsInput) -> ToolResult:
        denied = self._check("find_groups", {})
        if denied:
            return denied
        groups = self.directory.search_groups(args.query)
        return ToolResult(
            ok=True, tool="find_groups", rule_id="read-directory", data={"groups": [_public_group(g) for g in groups]}
        )

    def _check_membership(self, args: CheckMembershipInput) -> ToolResult:
        denied = self._check("check_membership", {})
        if denied:
            return denied
        missing = self._missing(args.user_id, args.group_id, "check_membership")
        if missing:
            return missing
        member = self.directory.is_member(args.user_id, args.group_id)
        return ToolResult(ok=True, tool="check_membership", rule_id="read-directory", data={"is_member": member})

    def _add_to_group(self, args: AddToGroupInput) -> ToolResult:
        missing = self._missing(args.user_id, args.group_id, "add_to_group")
        if missing:
            return missing
        user = self.directory.get_user(args.user_id)
        group = self.directory.get_group(args.group_id)
        assert user is not None and group is not None  # _missing checked both
        facts = self._facts(user, group)
        decision = decide(self.rules, self.actor, "add_to_group", facts)
        if not decision.allowed:
            return self._denied("add_to_group", decision.rule_id, decision.reason)
        already = self.directory.is_member(user.id, group.id)
        if not already:
            self.directory.add_member(user.id, group.id, added_by=self.actor)
        return ToolResult(
            ok=True,
            tool="add_to_group",
            rule_id=decision.rule_id,
            reason=decision.reason,
            data={"user_id": user.id, "group_id": group.id, "added": not already, "already_member": already},
        )

    def _missing(self, user_id: str, group_id: str, tool: str) -> ToolResult | None:
        if self.directory.get_user(user_id) is None:
            return ToolResult(ok=False, tool=tool, error=ErrorCode.NOT_FOUND, reason=f"No user {user_id}.")
        if self.directory.get_group(group_id) is None:
            return ToolResult(ok=False, tool=tool, error=ErrorCode.NOT_FOUND, reason=f"No group {group_id}.")
        return None

    def _facts(self, user: User, group: Group) -> dict[str, str]:
        eligible = not group.allowed_departments or user.department in group.allowed_departments
        return {
            "group_tier": group.tier.value,
            "user_status": user.status.value,
            "department_eligible": "yes" if eligible else "no",
            "approval": self._approval(user, group),
        }

    def _approval(self, user: User, group: Group) -> str:
        """Who approved this exact user and group, read from the approvals table."""
        if group.tier is Tier.RESTRICTED and group.owner_id is None:
            return "no_owner"
        row = self.directory.latest_approval(user.id, group.id)
        if row is None:
            return "none"
        if not row["approved"]:
            return "rejected"
        return "owner" if row["approver_id"] == group.owner_id else "other"
