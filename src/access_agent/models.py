"""Typed records and tool inputs.

IDs are typed on purpose: a tool takes `u-00042`, never a name. A model that
passes prose where an ID belongs gets `invalid_input`, and that counts against
first-try tool-call success.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

UserId = Annotated[str, StringConstraints(pattern=r"^u-\d{5}$")]
GroupId = Annotated[str, StringConstraints(pattern=r"^g-\d{4}$")]
Query = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]


class Tier(StrEnum):
    """How much control a group needs before anyone is added to it."""

    STANDARD = "standard"  # the agent may add an active, eligible user
    RESTRICTED = "restricted"  # needs the group owner's approval first
    PRIVILEGED = "privileged"  # never added by the agent: a person does it


class Status(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class User(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UserId
    name: str
    email: str
    department: str
    status: Status
    manager_id: UserId | None = None


class Group(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: GroupId
    name: str
    description: str
    tier: Tier
    owner_id: UserId | None = None
    # Empty means any department may join.
    allowed_departments: tuple[str, ...] = ()


class _Input(BaseModel):
    # A tool call with an argument the tool doesn't define is a malformed call.
    model_config = ConfigDict(extra="forbid")


class LookupUserInput(_Input):
    query: Query = Field(description="A name or an email address.")


class FindGroupsInput(_Input):
    query: Query = Field(description="Words from the group's name or description.")


class CheckMembershipInput(_Input):
    user_id: UserId
    group_id: GroupId


class AddToGroupInput(_Input):
    user_id: UserId
    group_id: GroupId


class ErrorCode(StrEnum):
    INVALID_INPUT = "invalid_input"
    UNKNOWN_TOOL = "unknown_tool"
    NOT_FOUND = "not_found"
    POLICY_DENIED = "policy_denied"


class ToolResult(BaseModel):
    """What every tool call returns, allowed or not."""

    ok: bool
    tool: str
    data: dict[str, Any] | None = None
    error: ErrorCode | None = None
    reason: str | None = None
    rule_id: str | None = None
