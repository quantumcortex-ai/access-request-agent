"""The one path every tool call takes.

validate the input -> look up the facts -> check policy -> act -> write the audit row

The workflow and the agent both call tools through here, so both are held to
the same rules and measured from the same log.

The gateway also remembers two things about the run, as facts for the policy.
Both are worked out here and never taken from the model. Both are kept in the
directory's database, so a request that pauses for an approval can be picked
up by a new process:

- which users and groups the request itself settled: each was the only result
  of a search whose every word appears in the request as a word of its own, or
  the request contains the group's exact name;
- which user and group the run has already acted on, because a request adds
  one person to one group.
"""

from __future__ import annotations

import re
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
    RequestApprovalInput,
    Tier,
    ToolResult,
    User,
)
from .policy import Rule, decide, load_rules

SETTLE_RULE = "match-must-be-settled-by-the-request"
ONE_GRANT_RULE = "one-grant-per-request"
_EDGE_PUNCTUATION = ".,;:!?()[]{}'\"<>"


def _words(query: str) -> list[str]:
    words = [word.strip(_EDGE_PUNCTUATION) for word in query.lower().split()]
    return [word for word in words if word]


def in_request(word: str, request: str | None) -> bool:
    """Does the request contain this word as a word of its own?

    "ops" is not in a request that says "laptops". A letter or a digit on either
    side, in any alphabet, makes it part of a longer word. A hyphen, an underscore,
    a dot or an apostrophe doesn't, so "finance" is in "Finance-Reports" and
    "carter" is in "Carter's".
    """
    if not request or not word:
        return False
    return re.search(rf"(?<![^\W_]){re.escape(word.lower())}(?![^\W_])", request.lower()) is not None


def outside_request(query: str, request: str | None) -> list[str]:
    """The words of this search that the request doesn't contain."""
    return [word for word in _words(query) if not in_request(word, request)]


# What the gateway remembers about one request. It is keyed by the run and the request's
# text, so a new gateway for the same request finds what the first one worked out.
# The caller must give each ticket its own run id: two tickets with the same words under
# one run id share this state. A saved match isn't checked again if the directory changes.
STATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS request_state (
    run_id TEXT NOT NULL,
    request TEXT NOT NULL,
    kind TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (run_id, request, kind, value)
);
"""


def grounded(query: str, request: str | None) -> bool:
    """Does every word of this search appear in the request?

    A search that uses a word the request doesn't contain is the caller's guess,
    so its result can't settle who or what the request means.
    """
    if not request:
        return False
    return bool(_words(query)) and not outside_request(query, request)


def names_whole(name: str, request: str | None) -> bool:
    """Does the request contain this exact group name, as a word of its own?

    "Finance-Reports" is not named by a request for "Finance-Reports-Editors".
    """
    if not request:
        return False
    return re.search(rf"(?<![\w-]){re.escape(name.lower())}(?![\w-])", request.lower()) is not None


TOOL_INPUTS: dict[str, type[BaseModel]] = {
    "lookup_user": LookupUserInput,
    "find_groups": FindGroupsInput,
    "check_membership": CheckMembershipInput,
    "add_to_group": AddToGroupInput,
    "request_approval": RequestApprovalInput,
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
        request: str | None = None,
    ) -> None:
        self.directory = directory
        self.actor = actor
        self.run_id = run_id
        # The request this gateway is handling, given by the caller's code, not by the model.
        # With no request nothing counts as settled.
        self.request = request
        self._settled_users: set[str] = set()
        self._settled_groups: set[str] = set()
        # The one user and group this run has acted on, once it has.
        self._acted_on: tuple[str, str] | None = None
        directory.conn.executescript(STATE_SCHEMA)
        self._recall()
        self.rules = rules if rules is not None else load_rules()
        self.audit = AuditLog(directory.conn)
        self._handlers: dict[str, Callable[[Any], ToolResult]] = {
            "lookup_user": self._lookup_user,
            "find_groups": self._find_groups,
            "check_membership": self._check_membership,
            "add_to_group": self._add_to_group,
            "request_approval": self._request_approval,
        }

    def _recall(self) -> None:
        """Read back what an earlier gateway worked out for this run and request."""
        if self.request is None:
            return
        rows = self.directory.conn.execute(
            "SELECT kind, value FROM request_state WHERE run_id = ? AND request = ? ORDER BY rowid DESC",
            (self.run_id, self.request),
        ).fetchall()
        # Oldest last, so the first pair ever acted on is the one that stands.
        for row in rows:
            if row["kind"] == "user":
                self._settled_users.add(row["value"])
            elif row["kind"] == "group":
                self._settled_groups.add(row["value"])
            elif row["kind"] == "acted_on":
                user_id, group_id = row["value"].split(" ")
                self._acted_on = (user_id, group_id)

    def _remember(self, kind: str, value: str) -> None:
        if self.request is None:
            return
        self.directory.conn.execute(
            "INSERT OR IGNORE INTO request_state VALUES (?, ?, ?, ?)", (self.run_id, self.request, kind, value)
        )
        self.directory.conn.commit()

    def _act_on(self, user_id: str, group_id: str) -> None:
        # The rule has already refused any other pair, so this is the first pair or the same one.
        self._acted_on = (user_id, group_id)
        self._remember("acted_on", f"{user_id} {group_id}")

    def call(self, tool: str, args: dict[str, Any], *, task_id: str) -> ToolResult:
        """Run one tool call and record it, whatever happens."""
        result = self._run(tool, args)
        failure = result.error.value if result.error else "error"
        outcome = "ok" if result.ok else failure
        # How many records a lookup returned: more than one means the caller had to choose.
        found = (result.data or {}).get("users", (result.data or {}).get("groups"))
        self.audit.write(
            run_id=self.run_id,
            task_id=task_id,
            actor=self.actor,
            tool=tool,
            args=args if isinstance(args, dict) else {"_raw": repr(args)},
            outcome=outcome,
            rule_id=result.rule_id,
            reason=result.reason,
            matches=len(found) if isinstance(found, list) else None,
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
        users = self.directory.search_users(args.query, args.department)
        from_request = grounded(args.query, self.request) and (
            args.department is None or grounded(args.department, self.request)
        )
        settled = len(users) == 1 and from_request
        if settled:
            self._settled_users.add(users[0].id)
            self._remember("user", users[0].id)
        return ToolResult(
            ok=True,
            tool="lookup_user",
            rule_id="read-directory",
            data={"users": [_public_user(u) for u in users], "settled": settled},
        )

    def _find_groups(self, args: FindGroupsInput) -> ToolResult:
        denied = self._check("find_groups", {})
        if denied:
            return denied
        groups = self.directory.search_groups(args.query)
        # A group's exact name, when the request names it, means that group and no other,
        # even if the name is also the start of another group's name.
        exact = [g for g in groups if g.name.lower() == args.query.lower()]
        if len(groups) > 1 and exact and names_whole(exact[0].name, self.request):
            groups = exact
        settled = len(groups) == 1 and grounded(args.query, self.request)
        if settled:
            self._settled_groups.add(groups[0].id)
            self._remember("group", groups[0].id)
        data: dict[str, Any] = {"groups": [_public_group(g) for g in groups], "settled": settled}
        # Say why a search didn't settle, so the caller can drop the word that spoiled it
        # instead of giving up. This changes nothing about what counts as settled.
        outside = outside_request(args.query, self.request) if self.request else []
        if outside:
            data["words_not_in_request"] = outside
        if not groups:
            data["words_in_no_group"] = [w for w in _words(args.query) if not self.directory.search_groups(w)]
        return ToolResult(ok=True, tool="find_groups", rule_id="read-directory", data=data)

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
        self._act_on(user.id, group.id)
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

    def _request_approval(self, args: RequestApprovalInput) -> ToolResult:
        """Say whether an approval is needed and who must give it.

        This writes no approval. The approval step asks the owner and records the
        answer. The approver is always the group's owner, read from the directory:
        the caller can't name someone else.
        """
        missing = self._missing(args.user_id, args.group_id, "request_approval")
        if missing:
            return missing
        user = self.directory.get_user(args.user_id)
        group = self.directory.get_group(args.group_id)
        assert user is not None and group is not None  # _missing checked both
        decision = decide(self.rules, self.actor, "request_approval", self._facts(user, group))
        if not decision.allowed:
            return self._denied("request_approval", decision.rule_id, decision.reason)
        self._act_on(user.id, group.id)
        needed = group.tier is Tier.RESTRICTED
        return ToolResult(
            ok=True,
            tool="request_approval",
            rule_id=decision.rule_id,
            data={
                "user_id": user.id,
                "group_id": group.id,
                "needed": needed,
                "approver_id": group.owner_id if needed else None,
            },
        )

    def _missing(self, user_id: str, group_id: str, tool: str) -> ToolResult | None:
        if self.directory.get_user(user_id) is None:
            return ToolResult(ok=False, tool=tool, error=ErrorCode.NOT_FOUND, reason=f"No user {user_id}.")
        if self.directory.get_group(group_id) is None:
            return ToolResult(ok=False, tool=tool, error=ErrorCode.NOT_FOUND, reason=f"No group {group_id}.")
        return None

    def _facts(self, user: User, group: Group) -> dict[str, str]:
        # Read the saved state again: another gateway for this request may have acted since this one started.
        self._recall()
        eligible = not group.allowed_departments or user.department in group.allowed_departments
        return {
            "group_tier": group.tier.value,
            "user_status": user.status.value,
            "department_eligible": "yes" if eligible else "no",
            "approval": self._approval(user, group),
            "match_settled": "yes" if self.settled(user.id, group.id) else "no",
            "second_pair": "yes" if self._acted_on not in (None, (user.id, group.id)) else "no",
        }

    def settled(self, user_id: str, group_id: str) -> bool:
        """Did the request itself settle both this user and this group?"""
        return user_id in self._settled_users and group_id in self._settled_groups

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
