"""One grant per request, and a group's exact name settling it."""

import pytest

from access_agent import Directory, ErrorCode, Gateway, seed
from access_agent.agent import ACTOR as AGENT
from access_agent.gateway import ONE_GRANT_RULE, SETTLE_RULE, names_whole
from access_agent.policy import load_rules

NO_SETTLE = [rule for rule in load_rules() if rule.id != SETTLE_RULE]


@pytest.fixture
def directory() -> Directory:
    d = Directory()
    seed(d)
    return d


def gid(directory: Directory, name: str) -> str:
    return directory.conn.execute("SELECT id FROM groups WHERE name = ?", (name,)).fetchone()["id"]


def uid(directory: Directory, department: str) -> str:
    row = directory.conn.execute(
        "SELECT id FROM users WHERE department = ? AND status = 'active' AND manager_id IS NOT NULL ORDER BY id",
        (department,),
    )
    return row.fetchone()["id"]


def gateway_for(directory: Directory, request: str | None = None, rules=NO_SETTLE) -> Gateway:
    return Gateway(directory, actor=AGENT, run_id="one-grant", rules=rules, request=request)


# One grant per request


def test_a_second_group_is_refused_after_the_first_grant(directory: Directory):
    gateway = gateway_for(directory)
    user = uid(directory, "Engineering")
    oncall, wifi = gid(directory, "Engineering-Oncall"), gid(directory, "Office-Wifi-Guests")
    assert gateway.call("add_to_group", {"user_id": user, "group_id": oncall}, task_id="t").ok
    refused = gateway.call("add_to_group", {"user_id": user, "group_id": wifi}, task_id="t")
    assert refused.error is ErrorCode.POLICY_DENIED and refused.rule_id == ONE_GRANT_RULE
    assert not directory.is_member(user, wifi)
    assert gateway.audit.rows()[-1]["rule_id"] == ONE_GRANT_RULE


def test_a_second_person_is_refused_too(directory: Directory):
    gateway = gateway_for(directory)
    first, wifi = uid(directory, "Engineering"), gid(directory, "Office-Wifi-Guests")
    second = uid(directory, "Finance")
    assert gateway.call("add_to_group", {"user_id": first, "group_id": wifi}, task_id="t").ok
    assert gateway.call("add_to_group", {"user_id": second, "group_id": wifi}, task_id="t").rule_id == ONE_GRANT_RULE


def test_asking_for_approval_counts_as_acting(directory: Directory):
    gateway = gateway_for(directory)
    user = uid(directory, "Finance")
    payroll, wifi = gid(directory, "Finance-Payroll"), gid(directory, "Office-Wifi-Guests")
    assert gateway.call("request_approval", {"user_id": user, "group_id": payroll}, task_id="t").ok
    assert gateway.call("add_to_group", {"user_id": user, "group_id": wifi}, task_id="t").rule_id == ONE_GRANT_RULE
    assert gateway.call("request_approval", {"user_id": user, "group_id": wifi}, task_id="t").rule_id == ONE_GRANT_RULE


def test_the_same_pair_can_be_acted_on_again(directory: Directory):
    gateway = gateway_for(directory)
    user, payroll = uid(directory, "Finance"), gid(directory, "Finance-Payroll")
    assert gateway.call("request_approval", {"user_id": user, "group_id": payroll}, task_id="t").ok
    directory.record_approval(user, payroll, directory.get_group(payroll).owner_id, True)
    assert gateway.call("add_to_group", {"user_id": user, "group_id": payroll}, task_id="t").ok


def test_a_refused_call_does_not_use_up_the_one_grant(directory: Directory):
    gateway = gateway_for(directory)
    user = uid(directory, "Engineering")
    admins, oncall = gid(directory, "Directory-Admins"), gid(directory, "Engineering-Oncall")
    assert not gateway.call("add_to_group", {"user_id": user, "group_id": admins}, task_id="t").ok
    assert gateway.call("add_to_group", {"user_id": user, "group_id": oncall}, task_id="t").ok


def test_each_run_gets_its_own_one_grant(directory: Directory):
    user = uid(directory, "Engineering")
    oncall, wifi = gid(directory, "Engineering-Oncall"), gid(directory, "Office-Wifi-Guests")
    assert gateway_for(directory).call("add_to_group", {"user_id": user, "group_id": oncall}, task_id="t").ok
    assert gateway_for(directory).call("add_to_group", {"user_id": user, "group_id": wifi}, task_id="t").ok


# A group's exact name


def test_a_name_is_whole_only_as_a_word_of_its_own():
    assert names_whole("Finance-Reports", "Please add nico to Finance-Reports.")
    assert names_whole("Finance-Reports", "add nico to finance-reports, thanks")
    assert not names_whole("Finance-Reports", "Please add nico to Finance-Reports-Editors.")
    assert not names_whole("Finance-Reports", None)


def test_an_exact_name_the_request_gives_settles_the_group(directory: Directory):
    gateway = gateway_for(directory, "Please add nico to Finance-Reports.", rules=load_rules())
    found = gateway.call("find_groups", {"query": "Finance-Reports"}, task_id="t").data
    assert [g["name"] for g in found["groups"]] == ["Finance-Reports"] and found["settled"] is True


def test_a_name_that_starts_a_longer_name_in_the_request_settles_nothing(directory: Directory):
    gateway = gateway_for(directory, "Please add nico to Finance-Reports-Editors.", rules=load_rules())
    found = gateway.call("find_groups", {"query": "Finance-Reports"}, task_id="t").data
    assert len(found["groups"]) == 2 and found["settled"] is False
