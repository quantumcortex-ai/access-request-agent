import sqlite3
from pathlib import Path

import pytest

from access_agent import Directory, ErrorCode, Gateway, seed
from access_agent.gateway import SETTLE_RULE
from access_agent.models import Status, Tier
from access_agent.policy import decide, load_rules

AGENT = "agent:access-request"
# These tests are about the other rules. The settle rule has its own tests in test_settle.py.
OTHER_RULES = [rule for rule in load_rules() if rule.id != SETTLE_RULE]


@pytest.fixture
def directory() -> Directory:
    d = Directory()
    seed(d)
    return d


@pytest.fixture
def gateway(directory: Directory) -> Gateway:
    return Gateway(directory, actor=AGENT, run_id="test-run", rules=OTHER_RULES)


def group_id(directory: Directory, name: str) -> str:
    row = directory.conn.execute("SELECT id FROM groups WHERE name = ?", (name,)).fetchone()
    return row["id"]


def a_user(directory: Directory, department: str, status: Status = Status.ACTIVE, skip_head: bool = True) -> str:
    rows = directory.conn.execute(
        "SELECT id, manager_id FROM users WHERE department = ? AND status = ? ORDER BY id",
        (department, status.value),
    ).fetchall()
    for row in rows:
        if not skip_head or row["manager_id"] is not None:
            return row["id"]
    raise AssertionError(f"no {status.value} user in {department}")


def owner_of(directory: Directory, gid: str) -> str:
    group = directory.get_group(gid)
    assert group is not None and group.owner_id is not None
    return group.owner_id


# The generated company


def test_seed_is_the_same_every_time():
    first, second = Directory(), Directory()
    seed(first)
    seed(second)
    dump = "SELECT * FROM users ORDER BY id"
    assert [tuple(r) for r in first.conn.execute(dump)] == [tuple(r) for r in second.conn.execute(dump)]


def test_seed_has_the_awkward_cases(directory: Directory):
    conn = directory.conn
    shared = conn.execute("SELECT name FROM users GROUP BY name HAVING count(*) > 1").fetchall()
    assert {"Sam Carter", "Jo Bianchi"} <= {r["name"] for r in shared}
    assert conn.execute("SELECT count(*) FROM users WHERE status = 'inactive'").fetchone()[0] > 0
    ownerless = conn.execute("SELECT name FROM groups WHERE owner_id IS NULL AND tier = 'restricted'").fetchall()
    assert [r["name"] for r in ownerless] == ["Customer-Data-Export"]
    assert len(directory.search_groups("finance reports")) == 2
    assert {t.value for t in Tier} == {r["tier"] for r in conn.execute("SELECT DISTINCT tier FROM groups")}


def test_emails_are_unique_and_never_real(directory: Directory):
    emails = [r["email"] for r in directory.conn.execute("SELECT email FROM users")]
    assert len(emails) == len(set(emails))
    assert all(e.endswith(".example") for e in emails)


# Typed inputs


@pytest.mark.parametrize(
    "args",
    [
        {"user_id": "Sam Carter", "group_id": "g-0001"},
        {"user_id": "u-00001", "group_id": "Finance-Reports"},
        {"user_id": "u-1", "group_id": "g-0001"},
        {"user_id": "u-00001"},
        {"user_id": "u-00001", "group_id": "g-0001", "reason": "they asked nicely"},
    ],
)
def test_add_to_group_takes_ids_and_nothing_else(gateway: Gateway, args: dict):
    result = gateway.call("add_to_group", args, task_id="t")
    assert not result.ok
    assert result.error is ErrorCode.INVALID_INPUT


def test_unknown_tool_is_refused_and_recorded(gateway: Gateway):
    result = gateway.call("delete_group", {"group_id": "g-0001"}, task_id="t")
    assert result.error is ErrorCode.UNKNOWN_TOOL
    assert gateway.audit.rows()[-1]["outcome"] == "unknown_tool"


def test_ids_that_do_not_exist_are_not_found(gateway: Gateway):
    result = gateway.call("add_to_group", {"user_id": "u-99999", "group_id": "g-0001"}, task_id="t")
    assert result.error is ErrorCode.NOT_FOUND


# Reads


def test_a_shared_name_returns_both_people(gateway: Gateway):
    result = gateway.call("lookup_user", {"query": "Sam Carter"}, task_id="t")
    assert result.ok
    departments = {u["department"] for u in result.data["users"]}
    assert departments == {"Finance", "Sales"}


def test_find_groups_matches_every_word(gateway: Gateway):
    result = gateway.call("find_groups", {"query": "finance reports editors"}, task_id="t")
    assert [g["name"] for g in result.data["groups"]] == ["Finance-Reports-Editors"]


# Policy


def test_standard_group_is_added(gateway: Gateway, directory: Directory):
    user, group = a_user(directory, "Sales"), group_id(directory, "Sales-Team")
    result = gateway.call("add_to_group", {"user_id": user, "group_id": group}, task_id="t")
    assert result.ok and result.data["added"] is True
    assert result.rule_id == "standard-groups"
    assert directory.is_member(user, group)


def test_adding_twice_changes_nothing(gateway: Gateway, directory: Directory):
    args = {"user_id": a_user(directory, "Sales"), "group_id": group_id(directory, "Sales-Team")}
    gateway.call("add_to_group", args, task_id="t")
    again = gateway.call("add_to_group", args, task_id="t")
    assert again.ok and again.data == {**args, "added": False, "already_member": True}
    assert directory.conn.execute("SELECT count(*) FROM memberships").fetchone()[0] == 1


def test_wrong_department_is_denied(gateway: Gateway, directory: Directory):
    args = {"user_id": a_user(directory, "Engineering"), "group_id": group_id(directory, "Sales-Team")}
    result = gateway.call("add_to_group", args, task_id="t")
    assert result.error is ErrorCode.POLICY_DENIED
    assert result.rule_id == "department-must-be-eligible"


def test_inactive_user_is_denied(gateway: Gateway, directory: Directory):
    user = directory.conn.execute("SELECT id FROM users WHERE status = 'inactive' ORDER BY id").fetchone()["id"]
    result = gateway.call(
        "add_to_group", {"user_id": user, "group_id": group_id(directory, "All-Staff-News")}, task_id="t"
    )
    assert result.rule_id == "inactive-users-get-nothing"
    assert not directory.is_member(user, group_id(directory, "All-Staff-News"))


def test_privileged_group_is_never_added_even_with_approval(gateway: Gateway, directory: Directory):
    user, group = a_user(directory, "Engineering"), group_id(directory, "Directory-Admins")
    directory.record_approval(user, group, owner_of(directory, group), approved=True)
    result = gateway.call("add_to_group", {"user_id": user, "group_id": group}, task_id="t")
    assert result.rule_id == "privileged-groups-are-for-people"
    assert not directory.is_member(user, group)


def test_restricted_group_needs_its_owners_approval(gateway: Gateway, directory: Directory):
    user, group = a_user(directory, "Finance"), group_id(directory, "Finance-Reports")
    args = {"user_id": user, "group_id": group}

    assert gateway.call("add_to_group", args, task_id="t").rule_id == "default-deny"

    someone_else = a_user(directory, "Legal")
    directory.record_approval(user, group, someone_else, approved=True)
    assert gateway.call("add_to_group", args, task_id="t").rule_id == "default-deny"

    directory.record_approval(user, group, owner_of(directory, group), approved=False)
    assert gateway.call("add_to_group", args, task_id="t").rule_id == "default-deny"
    assert not directory.is_member(user, group)

    directory.record_approval(user, group, owner_of(directory, group), approved=True)
    result = gateway.call("add_to_group", args, task_id="t")
    assert result.ok and result.rule_id == "restricted-groups-with-owner-approval"
    assert directory.is_member(user, group)


def test_an_approval_covers_one_user_and_one_group(gateway: Gateway, directory: Directory):
    user, group = a_user(directory, "Finance"), group_id(directory, "Finance-Reports")
    directory.record_approval(user, group, owner_of(directory, group), approved=True)
    other_group = group_id(directory, "Finance-Reports-Editors")
    result = gateway.call("add_to_group", {"user_id": user, "group_id": other_group}, task_id="t")
    assert result.error is ErrorCode.POLICY_DENIED


def test_restricted_group_with_no_owner_is_handed_off(gateway: Gateway, directory: Directory):
    args = {"user_id": a_user(directory, "Support"), "group_id": group_id(directory, "Customer-Data-Export")}
    result = gateway.call("add_to_group", args, task_id="t")
    assert result.rule_id == "restricted-group-without-an-owner"
    assert "identity team" in result.reason


def test_an_actor_no_rule_names_can_do_nothing(directory: Directory):
    stranger = Gateway(directory, actor="agent:something-else", run_id="test-run", rules=OTHER_RULES)
    assert stranger.call("lookup_user", {"query": "Sam"}, task_id="t").rule_id == "default-deny"
    args = {"user_id": a_user(directory, "Sales"), "group_id": group_id(directory, "Sales-Team")}
    assert stranger.call("add_to_group", args, task_id="t").rule_id == "default-deny"


def test_no_rules_means_everything_is_denied():
    assert decide([], AGENT, "lookup_user", {}).allowed is False


def test_a_rules_file_with_a_typo_is_refused(tmp_path: Path):
    bad = tmp_path / "rules.toml"
    bad.write_text(
        '[[rule]]\nid = "x"\neffect = "allow"\ntools = ["add_to_group"]\nwhne = { group_tier = ["standard"] }\n'
    )
    with pytest.raises(ValueError, match="unknown keys"):
        load_rules(bad)
    bad.write_text('[[rule]]\nid = "x"\neffect = "allow"\ntools = ["add_to_group"]\nwhen = { tier = ["standard"] }\n')
    with pytest.raises(ValueError, match="unknown facts"):
        load_rules(bad)


# Audit


def test_every_call_is_recorded_with_who_and_why(gateway: Gateway, directory: Directory):
    gateway.call("lookup_user", {"query": "Sam Carter"}, task_id="task-7")
    gateway.call("add_to_group", {"user_id": "Sam Carter", "group_id": "g-0001"}, task_id="task-7")
    args = {"user_id": a_user(directory, "Engineering"), "group_id": group_id(directory, "Directory-Admins")}
    gateway.call("add_to_group", args, task_id="task-7")

    rows = gateway.audit.rows("test-run")
    assert [r["outcome"] for r in rows] == ["ok", "invalid_input", "policy_denied"]
    assert {r["actor"] for r in rows} == {AGENT}
    assert {r["task_id"] for r in rows} == {"task-7"}
    assert rows[2]["rule_id"] == "privileged-groups-are-for-people"


def test_audit_rows_cannot_be_changed_or_deleted(gateway: Gateway, directory: Directory):
    gateway.call("lookup_user", {"query": "Sam Carter"}, task_id="t")
    with pytest.raises(sqlite3.IntegrityError, match="cannot be changed"):
        directory.conn.execute("UPDATE audit SET outcome = 'ok'")
    with pytest.raises(sqlite3.IntegrityError, match="cannot be deleted"):
        directory.conn.execute("DELETE FROM audit")
    assert len(gateway.audit.rows()) == 1
