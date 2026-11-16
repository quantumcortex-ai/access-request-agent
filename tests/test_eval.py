"""The eval set and the scoring, with no live model."""

import json
from dataclasses import asdict
from typing import Any

from access_agent import Gateway
from access_agent import eval as ev
from access_agent.gateway import ONE_GRANT_RULE, SETTLE_RULE
from access_agent.llm import Reply, ScriptedModel, tool_use
from access_agent.policy import load_rules
from access_agent.tasks import TASKS_FILE, Task, build_tasks, load_tasks
from access_agent.workflow import ACTOR, HANDOFF_RULES

TASKS = load_tasks()
# These tests are about the other rules. The settle rule has its own tests in test_settle.py.
OTHER_RULES = [rule for rule in load_rules() if rule.id != SETTLE_RULE]
NO_SETTLE = (SETTLE_RULE,)


def by_category(name: str) -> Task:
    return next(t for t in TASKS if t.category == name)


def own_words(task: Task, group: Any) -> str:
    """The words of the request that also describe this group: what a careful person would search for."""
    about = f"{group.name} {group.description}".lower()
    words = [word.strip(".,?!()'") for word in task.request.lower().split()]
    return " ".join(dict.fromkeys(word for word in words if len(word) >= 4 and word in about))


def reply(*blocks: dict[str, Any]) -> Reply:
    return Reply(content=list(blocks), stop_reason="tool_use", input_tokens=1000, output_tokens=100)


# The set


def test_the_committed_tasks_are_what_the_generator_makes():
    assert [asdict(t) for t in build_tasks()] == [json.loads(line) for line in TASKS_FILE.read_text().splitlines()]


def test_the_set_is_the_size_and_difficulty_we_said():
    assert 100 <= len(TASKS) <= 150
    assert sum(t.hard for t in TASKS) / len(TASKS) >= 0.40
    assert len({t.id for t in TASKS}) == len(TASKS)
    assert len({t.request for t in TASKS}) > 0.9 * len(TASKS)


def test_no_task_tells_the_model_the_answer():
    for task in TASKS:
        assert "u-0" not in task.request and "g-0" not in task.request, task.id


def test_every_label_agrees_with_a_careful_person_following_the_policy():
    """Do each request by hand through the gateway and compare with the label.

    The labels were written from how each case was built. If this disagrees,
    either a label or a policy rule is wrong, and both need a look.
    """
    checked = 0
    for task in TASKS:
        directory = ev.prepare(task)
        if task.user_id is None or task.group_id is None:
            assert task.expect_outcomes == ["needs_clarification"] and task.expect_grants == [], task.id
            continue
        gateway = Gateway(directory, actor=ACTOR, run_id="by-hand", rules=OTHER_RULES)
        pair = {"user_id": task.user_id, "group_id": task.group_id}

        def refused(result) -> str:
            return "handed_off" if result.rule_id in HANDOFF_RULES else "denied"

        if directory.is_member(task.user_id, task.group_id):
            outcome = "already_member"
        else:
            asked = gateway.call("request_approval", pair, task_id=task.id)
            if not asked.ok:
                outcome = refused(asked)
            else:
                approved = True
                if asked.data["needed"]:
                    answer = ev.approver_for(task, directory)({"approver_id": asked.data["approver_id"]})
                    directory.record_approval(task.user_id, task.group_id, answer["approver_id"], answer["approved"])
                    approved = answer["approved"]
                if not approved:
                    outcome = "denied"
                else:
                    added = gateway.call("add_to_group", pair, task_id=task.id)
                    outcome = "granted" if added.ok else refused(added)
        assert outcome in task.expect_outcomes, (task.id, task.category, outcome)
        assert ev.new_grants(task, directory) == task.expect_grants, (task.id, task.category)
        checked += 1
    assert checked > 100


def test_a_wrong_approver_is_never_the_owner():
    task = by_category("approved_by_the_wrong_person")
    directory = ev.prepare(task)
    owner = directory.get_group(task.group_id).owner_id
    answer = ev.approver_for(task, directory)({"approver_id": owner})
    assert answer["approved"] is True and answer["approver_id"] != owner


# Scoring


def test_a_correct_run_is_completed():
    task = by_category("standard_by_email")
    person = task.request.split("@")[0].split()[-1] + "@larkspur-freight.example"
    group = ev.prepare(task).get_group(task.group_id)
    model = ScriptedModel(
        lambda call: reply(tool_use("record_request", {"person": person, "group": own_words(task, group)}))
    )
    record = ev.run_one("workflow", task, 1, model, "test")
    assert record["completed"] is True and record["outcome"] == "granted"
    assert record["wrong_grants"] == [] and record["grants"] == task.expect_grants
    assert record["input_tokens"] == 1000 and all(outcome == "ok" for _, outcome in record["calls"])


def obeys_the_injection(task, extra):
    turns = [
        [tool_use("add_to_group", {"user_id": task.user_id, "group_id": task.group_id}, "c1")],
        [tool_use("add_to_group", {"user_id": task.user_id, "group_id": extra}, "c2")],
        [tool_use("finish", {"outcome": "granted"}, "c3")],
    ]
    return ScriptedModel(lambda call: reply(*turns.pop(0)))


def test_an_agent_that_obeys_an_injection_is_caught():
    task = by_category("injected_extra_groups")
    directory = ev.prepare(task)
    extra = directory.conn.execute("SELECT id FROM groups WHERE name = 'Office-Wifi-Guests'").fetchone()["id"]
    record = ev.run_one("agent", task, 1, obeys_the_injection(task, extra), "test", (SETTLE_RULE, ONE_GRANT_RULE))
    assert record["outcome"] == "granted"
    assert record["wrong_grants"] == [[task.user_id, extra]]
    assert record["completed"] is False


def test_the_one_grant_rule_refuses_the_injected_group():
    task = by_category("injected_extra_groups")
    directory = ev.prepare(task)
    extra = directory.conn.execute("SELECT id FROM groups WHERE name = 'Office-Wifi-Guests'").fetchone()["id"]
    record = ev.run_one("agent", task, 1, obeys_the_injection(task, extra), "test", NO_SETTLE)
    assert record["wrong_grants"] == [] and record["grants"] == task.expect_grants
    assert ("add_to_group", "policy_denied") in [tuple(call) for call in record["calls"]]


def test_the_right_label_with_no_grant_is_not_completed():
    task = by_category("standard_by_email")
    model = ScriptedModel(lambda call: reply(tool_use("finish", {"outcome": "granted"}, "c1")))
    record = ev.run_one("agent", task, 1, model, "test", NO_SETTLE)
    assert record["outcome"] == "granted" and record["completed"] is False


def test_an_arm_that_crashes_fails_the_task_and_the_run_goes_on(tmp_path):
    def broken(call):
        raise RuntimeError("the model is down")

    records = ev.run_eval(TASKS[:2], ["agent"], 1, ScriptedModel(broken), tmp_path / "run", quiet=True)
    assert [r["outcome"] for r in records] == ["error", "error"]
    assert not any(r["completed"] for r in records)


def test_a_stopped_run_picks_up_where_it_left_off(tmp_path):
    model = ScriptedModel(lambda call: reply(tool_use("finish", {"outcome": "needs_clarification"}, "c1")))
    ev.run_eval(TASKS[:3], ["agent"], 1, model, tmp_path / "run", quiet=True)
    first = len(model.calls)
    records = ev.run_eval(TASKS[:5], ["agent"], 1, model, tmp_path / "run", quiet=True)
    assert len(records) == 5 and len(model.calls) == first + 2


# The numbers


def test_wilson_interval():
    low, high = ev.wilson(48, 50)
    assert round(low, 2) == 0.87 and round(high, 2) == 0.99
    assert ev.wilson(0, 0) == (0.0, 0.0)
    assert ev.wilson(50, 50)[1] == 1.0 and ev.wilson(50, 50)[0] < 1.0


def test_summary_counts_calls_grants_and_cost():
    base = {"category": "c", "hard": False, "model_calls": 2, "input_tokens": 1_000_000, "output_tokens": 100_000}
    good = [["add_to_group", "ok"], ["add_to_group", "policy_denied"]]
    bad = [["add_to_group", "invalid_input"], ["lookup_user", "not_found"]]
    records = [
        base | {"arm": "agent", "completed": True, "outcome": "granted", "wrong_grants": [], "calls": good},
        base
        | {"arm": "agent", "completed": False, "outcome": "granted", "wrong_grants": [["u", "g"]], "hard": True}
        | {"calls": bad},
    ]
    agent = ev.summarize(records, "claude-haiku-5-5")["agent"]
    assert agent["completed"] == [1, 2] and agent["completed_hard"] == [0, 1]
    assert agent["tool_calls"] == [2, 4]
    assert agent["wrong_grants"] == 1 and agent["runs_with_a_wrong_grant"] == 1
    # 2M input at $0.10 and 0.2M output at $0.50 per million.
    assert round(agent["cost"], 4) == 0.30 and round(agent["cost_per_completed"], 4) == 0.30
    text = ev.render({"agent": agent}, "claude-haiku-5-5")
    assert "FAIL: 1 wrong grant(s)." in text and "50.0%" in text
    assert ev.summarize(records, "a-model-with-no-price")["agent"]["cost"] is None


def test_signals_say_what_a_confidence_level_or_several_matches_would_have_flagged():
    base = {"arm": "agent", "category": "c", "hard": False, "calls": [], "outcome": "granted"}
    one, two = [["lookup_user", 1]], [["lookup_user", 1], ["find_groups", 2]]
    records = [
        base | {"completed": True, "wrong_grants": [], "confidence": 95, "lookups": one},
        base | {"completed": True, "wrong_grants": [], "confidence": 75, "lookups": two},
        base | {"completed": False, "wrong_grants": [["u", "g"]], "confidence": 65, "lookups": two},
        base | {"completed": False, "wrong_grants": [], "confidence": None, "lookups": one},
    ]
    found = ev.signals(records)
    assert found["stated"] == 3 and found["mean_completed"] == 85 and found["mean_missed"] == 65
    # [runs flagged, misses among them, wrong-grant runs among them]
    assert found["below"] == {"70": [1, 1, 1], "80": [2, 1, 1], "90": [2, 1, 1]}
    assert found["several_matches"] == [2, 1, 1] and found["all"] == [4, 2, 1]
    text = ev.render(ev.summarize(records, "claude-haiku-5-5"), "claude-haiku-5-5")
    assert "| Confidence below 70 | 1 runs: 1 of 2 misses, 1 of 1 wrong-grant runs |" in text
    assert "| A lookup returned more than one match | 2 runs: 1 of 2 misses, 1 of 1 wrong-grant runs |" in text


def test_the_test_set_loads_and_names_real_records():
    from access_agent import Directory, seed
    from access_agent.tasks import TEST_FILE, load_tasks

    tasks = load_tasks(TEST_FILE)
    directory = Directory()
    seed(directory)
    assert len(tasks) == 40 and {t.split for t in tasks} == {"test"}
    assert len({t.id for t in tasks}) == 40
    for task in tasks:
        for user_id, group_id in [*task.expect_grants, [task.user_id, task.group_id]]:
            assert directory.get_user(user_id) is not None, task.id
            assert directory.get_group(group_id) is not None, task.id
