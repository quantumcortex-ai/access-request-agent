"""When each arm hands a request back, from finished runs. No model call.

    python -m access_agent.handoffs results/<run> [results/<run> ...]

For each run and arm: how the runs ended, grouped by what the label says should happen, and the runs that went
back to a person or the requester when the label says to act.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .eval import load_records
from .tasks import TASKS_FILE, TEST_FILE, Task, load_tasks

# Ways a run can end without acting.
BACK = ("needs_clarification", "handed_off", "gave_up")
KINDS = ("ask the requester", "hand to a person", "deny or hand to a person", "deny", "act")


def kind(task: Task) -> str:
    """What the label says should happen, in five kinds."""
    expected = set(task.expect_outcomes)
    if expected == {"needs_clarification"}:
        return "ask the requester"
    if expected == {"handed_off"}:
        return "hand to a person"
    if expected == {"denied", "handed_off"}:
        return "deny or hand to a person"
    if expected == {"denied"}:
        return "deny"
    return "act"


def table(run_dir: Path) -> dict[str, Any]:
    """For each arm: outcomes by kind, and the runs sent back when the label says act."""
    tasks = {t.id: t for path in (TASKS_FILE, TEST_FILE) for t in load_tasks(path)}
    meta = json.loads((run_dir / "meta.json").read_text())
    records = load_records(run_dir)
    result: dict[str, Any] = {"run": run_dir.name, "model": meta["model"], "split": meta["split"], "arms": {}}
    for arm in sorted({r["arm"] for r in records}, reverse=True):
        rows = [r for r in records if r["arm"] == arm]
        by_kind: dict[str, Counter[str]] = {k: Counter() for k in KINDS}
        for r in rows:
            by_kind[kind(tasks[r["task_id"]])][r["outcome"]] += 1
        sent_back = Counter(r["task_id"] for r in rows if kind(tasks[r["task_id"]]) == "act" and r["outcome"] in BACK)
        result["arms"][arm] = {
            "by_kind": {k: dict(v) for k, v in by_kind.items() if v},
            "sent_back_when_label_says_act": dict(sorted(sent_back.items())),
            "act_runs": sum(by_kind["act"].values()),
        }
    return result


def render(result: dict[str, Any]) -> str:
    lines = [f"## {result['run']} ({result['model']}, {result['split']})"]
    for arm, data in result["arms"].items():
        lines += ["", f"{arm}:", "", "| The label says | How the runs ended |", "|---|---|"]
        for k, outcomes in data["by_kind"].items():
            ended = ", ".join(f"{outcome} {n}" for outcome, n in sorted(outcomes.items(), key=lambda kv: -kv[1]))
            lines.append(f"| {k} | {ended} |")
        back = data["sent_back_when_label_says_act"]
        listed = ", ".join(f"{task} x{n}" for task, n in back.items()) or "none"
        lines += ["", f"Sent back when the label says act: {sum(back.values())} of {data['act_runs']} ({listed})"]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("runs", nargs="+", type=Path)
    for run_dir in parser.parse_args().runs:
        print(render(table(run_dir)) + "\n")


if __name__ == "__main__":
    main()
