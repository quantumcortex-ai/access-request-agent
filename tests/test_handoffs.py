"""The hand-off figures the README quotes, recomputed from the committed records."""

from pathlib import Path

from access_agent import handoffs

RESULTS = Path(__file__).resolve().parents[1] / "results"
RUNS = [
    RESULTS / f"2026-11-17-f7a8fa2-{name}"
    for name in ("haiku-validation", "sonnet-validation", "haiku-test", "sonnet-test")
]


def test_every_request_that_should_go_back_did():
    for run in RUNS:
        for arm, data in handoffs.table(run)["arms"].items():
            by_kind = data["by_kind"]
            assert set(by_kind["ask the requester"]) == {"needs_clarification"}, (run.name, arm)
            assert set(by_kind["hand to a person"]) == {"handed_off"}, (run.name, arm)


def test_runs_sent_back_when_the_label_says_act():
    sent_back, act_runs, by_task = 0, 0, {}
    for run in RUNS:
        for data in handoffs.table(run)["arms"].values():
            act_runs += data["act_runs"]
            for task, n in data["sent_back_when_label_says_act"].items():
                sent_back += n
                by_task[task] = by_task.get(task, 0) + n
    assert (sent_back, act_runs) == (21, 1080)
    assert by_task == {"t-075": 3, "h-028": 12, "h-011": 3, "h-017": 3}
