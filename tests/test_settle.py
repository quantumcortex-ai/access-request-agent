"""The settle rule: act only on a user and a group the request itself settled."""

from typing import Any

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from access_agent import Directory, ErrorCode, Gateway, seed
from access_agent import eval as ev
from access_agent.agent import ACTOR as AGENT
from access_agent.agent import build_agent
from access_agent.approval import owner_says, run
from access_agent.gateway import SETTLE_RULE, grounded
from access_agent.llm import Reply, ScriptedModel, tool_use
from access_agent.tasks import load_tasks
from access_agent.workflow import ACTOR as WORKFLOW
from access_agent.workflow import build_workflow

TASKS = load_tasks()


@pytest.fixture
def directory() -> Directory:
    d = Directory()
    seed(d)
    return d


def gid(directory: Directory, name: str) -> str:
    return directory.conn.execute("SELECT id FROM groups WHERE name = ?", (name,)).fetchone()["id"]


def named(directory: Directory, name: str, department: str) -> str:
    row = directory.conn.execute("SELECT id FROM users WHERE name = ? AND department = ?", (name, department))
    return row.fetchone()["id"]


def gateway_for(directory: Directory, request: str | None, actor: str = AGENT) -> Gateway:
    return Gateway(directory, actor=actor, run_id="settle", request=request)


def reply(*blocks: dict[str, Any]) -> Reply:
    return Reply(content=list(blocks), stop_reason="tool_use", input_tokens=100, output_tokens=20)


# What counts as the request's own words


def test_a_search_is_grounded_when_every_word_is_in_the_request():
    request = "Hi, could you add Jo Bianchi (Legal) to the sales team's shared files? Thanks."
    assert grounded("Jo Bianchi", request)
    assert grounded("legal", request)
    assert grounded("sales team shared files", request)
    assert grounded("(Legal)", request)  # punctuation at the edges doesn't count


def test_a_word_inside_a_longer_word_is_not_in_the_request():
    request = "Dana Okafor needs the new laptops list and the Finance-Reports group. Thanks, Carter's team"
    assert not grounded("ops", request)
    assert not grounded("report", request)
    assert grounded("laptops", request)
    assert grounded("finance reports", request)  # a hyphen ends a word
    assert grounded("carter", request)  # so does an apostrophe


def test_a_new_gateway_for_the_same_request_keeps_what_was_settled(directory):
    request = "Please add Sam Carter from Sales to the sales team group"
    first = gateway_for(directory, request)
    user = first.call("lookup_user", {"query": "Sam Carter", "department": "Sales"}, task_id="t")
    group = first.call("find_groups", {"query": "sales team"}, task_id="t")
    assert user.data["settled"] and group.data["settled"]
    user_id, group_id = user.data["users"][0]["id"], group.data["groups"][0]["id"]
    assert first.call("add_to_group", {"user_id": user_id, "group_id": group_id}, task_id="t").ok

    again = gateway_for(directory, request)
    assert again.settled(user_id, group_id)
    assert again._acted_on == (user_id, group_id)
    other = gid(directory, "Sales-Forecast-Readers")
    again.call("find_groups", {"query": "Sales-Forecast-Readers"}, task_id="t")
    refused = again.call("add_to_group", {"user_id": user_id, "group_id": other}, task_id="t")
    assert refused.error is ErrorCode.POLICY_DENIED

    # A different request starts with nothing settled.
    assert not gateway_for(directory, "Something else entirely").settled(user_id, group_id)


def test_a_search_with_a_word_the_request_lacks_is_not_grounded():
    request = "Can vik.abbott@larkspur-freight.example be added to the Sales one today?"
    assert not grounded("Sales-Team", request)
    assert not grounded("sales forecast", request)
    assert not grounded("", request) and not grounded("sales", None) and not grounded("sales", "")


# The gateway


def test_an_email_and_a_group_name_from_the_request_settle_the_match(directory: Directory):
    user = named(directory, "Sam Carter", "Finance")
    email = directory.get_user(user).email
    gateway = gateway_for(directory, f"Please add {email} to All-Staff-News.")
    assert gateway.call("lookup_user", {"query": email}, task_id="t").data["settled"] is True
    assert gateway.call("find_groups", {"query": "All-Staff-News"}, task_id="t").data["settled"] is True
    pair = {"user_id": user, "group_id": gid(directory, "All-Staff-News")}
    assert gateway.call("add_to_group", pair, task_id="t").ok


def test_a_shared_name_settles_nothing_until_the_request_says_which(directory: Directory):
    finance, group = named(directory, "Sam Carter", "Finance"), gid(directory, "All-Staff-News")
    gateway = gateway_for(directory, "Add Sam Carter to All-Staff-News.")
    found = gateway.call("lookup_user", {"query": "Sam Carter"}, task_id="t")
    assert len(found.data["users"]) == 2 and found.data["settled"] is False
    gateway.call("find_groups", {"query": "All-Staff-News"}, task_id="t")
    for tool in ("request_approval", "add_to_group"):
        refused = gateway.call(tool, {"user_id": finance, "group_id": group}, task_id="t")
        assert refused.error is ErrorCode.POLICY_DENIED and refused.rule_id == SETTLE_RULE
    assert not directory.is_member(finance, group)


def test_a_department_settles_a_shared_name_only_when_the_request_gives_it(directory: Directory):
    finance, group = named(directory, "Sam Carter", "Finance"), gid(directory, "All-Staff-News")
    pair = {"user_id": finance, "group_id": group}

    told = gateway_for(directory, "Add Sam Carter (Finance) to All-Staff-News.")
    told.call("find_groups", {"query": "All-Staff-News"}, task_id="t")
    assert told.call("lookup_user", {"query": "Sam Carter", "department": "Finance"}, task_id="t").data["settled"]
    assert told.call("add_to_group", pair, task_id="t").ok

    seed_again = Directory()
    seed(seed_again)
    guessed = gateway_for(seed_again, "Add Sam Carter to All-Staff-News.")
    guessed.call("find_groups", {"query": "All-Staff-News"}, task_id="t")
    one = guessed.call("lookup_user", {"query": "Sam Carter", "department": "Finance"}, task_id="t")
    assert len(one.data["users"]) == 1 and one.data["settled"] is False  # the department was a guess
    assert guessed.call("add_to_group", pair, task_id="t").rule_id == SETTLE_RULE


def test_searching_for_a_name_seen_in_results_does_not_settle_a_vague_request(directory: Directory):
    user = named(directory, "Sam Carter", "Sales")
    email = directory.get_user(user).email
    gateway = gateway_for(directory, f"Can {email} be added to the Sales one today?")
    gateway.call("lookup_user", {"query": email}, task_id="t")
    assert len(gateway.call("find_groups", {"query": "sales"}, task_id="t").data["groups"]) == 2
    picked = gateway.call("find_groups", {"query": "Sales-Team"}, task_id="t")
    assert len(picked.data["groups"]) == 1 and picked.data["settled"] is False
    refused = gateway.call("add_to_group", {"user_id": user, "group_id": gid(directory, "Sales-Team")}, task_id="t")
    assert refused.rule_id == SETTLE_RULE and not directory.is_member(user, gid(directory, "Sales-Team"))


def test_with_no_request_nothing_is_settled(directory: Directory):
    user, group = named(directory, "Sam Carter", "Finance"), gid(directory, "All-Staff-News")
    gateway = gateway_for(directory, None)
    gateway.call("lookup_user", {"query": directory.get_user(user).email}, task_id="t")
    gateway.call("find_groups", {"query": "All-Staff-News"}, task_id="t")
    assert gateway.call("add_to_group", {"user_id": user, "group_id": group}, task_id="t").rule_id == SETTLE_RULE


def test_the_refusal_is_in_the_audit_log_with_the_rule(directory: Directory):
    user, group = named(directory, "Sam Carter", "Finance"), gid(directory, "All-Staff-News")
    gateway = gateway_for(directory, "Add Sam Carter to All-Staff-News.")
    gateway.call("add_to_group", {"user_id": user, "group_id": group}, task_id="t")
    row = gateway.audit.rows()[-1]
    assert row["outcome"] == "policy_denied" and row["rule_id"] == SETTLE_RULE


def test_a_known_limit_boilerplate_words_can_settle_the_wrong_group(directory: Directory):
    """The rule narrows guessing, it doesn't end it.

    "access" is in the request only as part of "needs access to", and it happens to
    pick out one of the two Sales groups. A caller that searches this way gets a
    settled match the request never gave. docs/eval-pass-criteria.md says so.
    """
    gateway = gateway_for(directory, "Sam Carter needs access to the Sales one.")
    found = gateway.call("find_groups", {"query": "access sales"}, task_id="t")
    assert [g["name"] for g in found.data["groups"]] == ["Sales-Forecast-Readers"] and found.data["settled"] is True


# The eval set


def test_every_task_a_careful_person_can_do_is_settled_by_the_requests_own_words():
    """If this fails, the rule would refuse a request that says enough, and the labels would be wrong."""
    checked = 0
    for task in TASKS:
        if task.user_id is None or task.group_id is None:
            continue
        directory = ev.prepare(task)
        gateway = gateway_for(directory, task.request, WORKFLOW)
        user, group = directory.get_user(task.user_id), directory.get_group(task.group_id)
        if user.email in task.request:
            who: dict[str, Any] = {"query": user.email}
        else:
            who = {"query": user.name}
            if f"({user.department})" in task.request:
                who["department"] = user.department
        about = f"{group.name} {group.description}".lower()
        words = [word.strip(".,?!()'") for word in task.request.split("\n")[0].lower().split()]
        what = " ".join(dict.fromkeys(word for word in words if len(word) >= 4 and word in about))
        gateway.call("lookup_user", who, task_id=task.id)
        gateway.call("find_groups", {"query": what}, task_id=task.id)
        assert gateway.settled(task.user_id, task.group_id), (task.id, task.category, who, what)
        checked += 1
    assert checked > 100


# The arms


def test_workflow_asks_for_clarification_when_the_model_picks_from_a_vague_request(directory: Directory):
    user = named(directory, "Sam Carter", "Sales")
    email, group = directory.get_user(user).email, gid(directory, "Sales-Team")
    request = f"Can {email} be added to the Sales one today?"
    answers = {
        "record_request": {"person": email, "group": "sales", "confidence": 90},
        # The model guesses, and offers words the request doesn't contain.
        "choose": {"user_id": user, "group_id": group, "group_words": "sales team", "confidence": 85},
    }
    model = ScriptedModel(
        lambda call: reply(tool_use(call["tool_choice"]["name"], answers[call["tool_choice"]["name"]]))
    )
    gateway = gateway_for(directory, request, WORKFLOW)
    graph = build_workflow(gateway, model, InMemorySaver())
    final = run(graph, {"task_id": "t", "request": request}, thread_id="1", approver=owner_says(True))
    assert final["outcome"] == "needs_clarification" and not directory.is_member(user, group)
    assert gateway.audit.rows()[-1]["rule_id"] == SETTLE_RULE


def test_workflow_grants_when_the_request_names_the_department(directory: Directory):
    user, group = named(directory, "Jo Bianchi", "Legal"), gid(directory, "Office-Wifi-Guests")
    request = "Hi, could you add Jo Bianchi (Legal) to Office-Wifi-Guests? Thanks."
    answers = {
        "record_request": {"person": "Jo Bianchi", "department": "Legal", "group": "Office-Wifi-Guests"},
    }
    model = ScriptedModel(
        lambda call: reply(tool_use(call["tool_choice"]["name"], answers[call["tool_choice"]["name"]]))
    )
    graph = build_workflow(gateway_for(directory, request, WORKFLOW), model, InMemorySaver())
    final = run(graph, {"task_id": "t", "request": request}, thread_id="1", approver=owner_says(True))
    assert final["outcome"] == "granted" and directory.is_member(user, group)
    assert final["model_calls"] == 1  # settled by the first searches, so no choose step


def test_workflow_settles_a_pick_with_words_from_the_request(directory: Directory):
    user = named(directory, "Sam Carter", "Finance")
    email, group = directory.get_user(user).email, gid(directory, "Finance-Reports")
    request = f"Please give {email} read access to the monthly finance reports."
    answers = {
        "record_request": {"person": email, "group": "finance reports"},
        "choose": {"user_id": user, "group_id": group, "group_words": "read finance reports"},
    }
    model = ScriptedModel(
        lambda call: reply(tool_use(call["tool_choice"]["name"], answers[call["tool_choice"]["name"]]))
    )
    graph = build_workflow(gateway_for(directory, request, WORKFLOW), model, InMemorySaver())
    final = run(graph, {"task_id": "t", "request": request}, thread_id="1", approver=owner_says(True))
    assert final["outcome"] == "granted" and directory.is_member(user, group)


def test_workflow_drops_a_word_the_request_lacks_before_it_searches_again(directory: Directory):
    # The model adds "monthly", which the group's record has and the request doesn't. On its own
    # that word would spoil a search the request's own words settle.
    task = next(t for t in TASKS if t.id == "t-081")
    user, group = named(directory, "Vik Underhill", "Legal"), gid(directory, "Finance-Reports")
    answers = {
        "record_request": {"person": "Vik Underhill", "department": "Legal", "group": "finance reports"},
        "choose": {"user_id": user, "group_id": group, "group_words": "read monthly finance reports"},
    }
    model = ScriptedModel(lambda call: reply(tool_use(call["tools"][0]["name"], answers[call["tools"][0]["name"]])))
    gateway = gateway_for(directory, task.request, WORKFLOW)
    graph = build_workflow(gateway, model, InMemorySaver())
    final = run(graph, {"task_id": task.id, "request": task.request}, thread_id="1", approver=owner_says(True))
    assert final["outcome"] == "granted"
    assert directory.is_member(user, group)


def test_a_group_search_names_the_words_that_spoiled_it(directory: Directory):
    request = "Access request: add Dev Farrow to the finance reports, read only."
    gateway = gateway_for(directory, request)
    nothing = gateway.call("find_groups", {"query": "finance reports read only"}, task_id="t")
    assert nothing.data["groups"] == [] and nothing.data["words_in_no_group"] == ["only"]
    guess = gateway.call("find_groups", {"query": "monthly finance reports read"}, task_id="t")
    assert guess.data["settled"] is False and guess.data["words_not_in_request"] == ["monthly"]
    asked = gateway.call("find_groups", {"query": "finance reports read"}, task_id="t")
    assert asked.data["settled"] is True and "words_not_in_request" not in asked.data


def test_agent_that_guesses_is_refused_and_ends_with_clarification(directory: Directory):
    user = named(directory, "Sam Carter", "Sales")
    email, group = directory.get_user(user).email, gid(directory, "Sales-Team")
    request = f"Can {email} be added to the Sales one today?"
    pair = {"user_id": user, "group_id": group}
    turns = [
        [tool_use("lookup_user", {"query": email}, "c1"), tool_use("find_groups", {"query": "sales"}, "c2")],
        [tool_use("add_to_group", pair, "c3")],
        [tool_use("finish", {"outcome": "needs_clarification", "confidence": 80}, "c4")],
    ]
    gateway = gateway_for(directory, request)
    graph = build_agent(gateway, ScriptedModel(lambda call: reply(*turns.pop(0))), InMemorySaver())
    final = run(graph, {"task_id": "t", "request": request}, thread_id="1", approver=owner_says(True))
    assert final["outcome"] == "needs_clarification" and not directory.is_member(user, group)
    assert [row["rule_id"] for row in gateway.audit.rows() if row["tool"] == "add_to_group"] == [SETTLE_RULE]


def test_the_eval_can_leave_the_rule_out_to_measure_it():
    task = next(t for t in TASKS if t.category == "group_not_settled")
    probe = ev.prepare(task)
    emails = probe.conn.execute("SELECT id, email FROM users").fetchall()
    user = probe.get_user(next(row["id"] for row in emails if row["email"] in task.request))
    # A group anyone may join, so only the settle rule stands between a guess and a grant.
    pair = {"user_id": user.id, "group_id": gid(probe, "All-Staff-News")}

    def guesser() -> ScriptedModel:
        turns = [[tool_use("add_to_group", pair, "c1")], [tool_use("finish", {"outcome": "granted"}, "c2")]]
        return ScriptedModel(lambda call: reply(*turns.pop(0)))

    with_rule = ev.run_one("agent", task, 1, guesser(), "test")
    without = ev.run_one("agent", task, 1, guesser(), "test", (SETTLE_RULE,))
    assert with_rule["wrong_grants"] == [] and with_rule["calls"] == [["add_to_group", "policy_denied"]]
    assert without["wrong_grants"] == [[user.id, pair["group_id"]]]
