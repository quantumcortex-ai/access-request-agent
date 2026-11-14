"""Run the eval set and report the numbers.

    python -m access_agent.eval --arm both --limit 20          # a quick look
    python -m access_agent.eval --arm both --repeats 3          # a full run
    python -m access_agent.eval --report runs/<run id>          # print the table again

Every task starts from a fresh copy of the company, so one task can't affect
another. Each result is written as it finishes, so a run that stops can be
started again with `--run-id` and picks up where it left off.

What each number means is fixed in docs/eval-pass-criteria.md.
"""

from __future__ import annotations

import argparse
import json
import math
import tomllib
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from . import agent, workflow
from .approval import Approver, run
from .directory import Directory
from .gateway import Gateway
from .llm import ClaudeModel, Model
from .seed import seed
from .tasks import TASKS_FILE, Task, load_tasks

RUNS_DIR = Path(__file__).resolve().parents[2] / "runs"
PRICES_FILE = Path(__file__).resolve().parents[2] / "tasks" / "prices.toml"
ARMS = {"workflow": (workflow.ACTOR, workflow.build_workflow), "agent": (agent.ACTOR, agent.build_agent)}
# A call the policy stopped was still a well-formed call, so it counts as a success.
GOOD_CALLS = {"ok", "policy_denied"}


def prepare(task: Task) -> Directory:
    directory = Directory()
    seed(directory)
    for user_id, group_id in task.setup_members:
        directory.add_member(user_id, group_id, added_by="setup")
    return directory


def approver_for(task: Task, directory: Directory) -> Approver:
    """How the approval question gets answered for this task, if it's asked."""

    def answer(question: dict[str, Any]) -> dict[str, Any]:
        owner = question["approver_id"]
        if task.approver == "other_yes":
            # A department head who isn't this group's owner says yes.
            row = directory.conn.execute(
                "SELECT id FROM users WHERE manager_id IS NULL AND id != ? ORDER BY id DESC LIMIT 1", (owner,)
            ).fetchone()
            return {"approved": True, "approver_id": row["id"]}
        return {"approved": task.approver == "owner_yes", "approver_id": owner}

    return answer


def new_grants(task: Task, directory: Directory) -> list[list[str]]:
    rows = directory.conn.execute("SELECT user_id, group_id FROM memberships ORDER BY user_id, group_id").fetchall()
    return [[r["user_id"], r["group_id"]] for r in rows if [r["user_id"], r["group_id"]] not in task.setup_members]


def run_one(arm: str, task: Task, repeat: int, model: Model, run_id: str) -> dict[str, Any]:
    actor, build = ARMS[arm]
    directory = prepare(task)
    gateway = Gateway(directory, actor=actor, run_id=run_id)
    graph = build(gateway, model, InMemorySaver())
    record: dict[str, Any] = {
        "arm": arm,
        "task_id": task.id,
        "repeat": repeat,
        "category": task.category,
        "hard": task.hard,
    }
    try:
        final = run(
            graph,
            {"task_id": task.id, "request": task.request},
            thread_id=f"{task.id}-{repeat}",
            approver=approver_for(task, directory),
        )
        record |= {
            "outcome": final.get("outcome"),
            "note": final.get("note", ""),
            "model_calls": final.get("model_calls", 0),
            "input_tokens": final.get("input_tokens", 0),
            "output_tokens": final.get("output_tokens", 0),
        }
    except Exception as exc:  # noqa: BLE001 - an arm that crashes fails the task; the run goes on
        record |= {"outcome": "error", "note": f"{type(exc).__name__}: {exc}"[:300]}
    grants = new_grants(task, directory)
    record["grants"] = grants
    record["wrong_grants"] = [g for g in grants if g not in task.expect_grants]
    record["completed"] = record["outcome"] in task.expect_outcomes and sorted(grants) == sorted(task.expect_grants)
    record["calls"] = [[row["tool"], row["outcome"]] for row in gateway.audit.rows()]
    return record


def wilson(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """A 95% interval for a share. It behaves near 0% and 100%, where the simple one doesn't."""
    if total == 0:
        return (0.0, 0.0)
    share = successes / total
    centre = (share + z * z / (2 * total)) / (1 + z * z / total)
    half = z * math.sqrt(share * (1 - share) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return (max(0.0, centre - half), min(1.0, centre + half))


def _share(successes: int, total: int) -> str:
    if total == 0:
        return "n/a"
    low, high = wilson(successes, total)
    return f"{successes / total:.1%} ({low:.0%} to {high:.0%}), {successes} of {total}"


def summarize(records: list[dict[str, Any]], model_name: str) -> dict[str, Any]:
    prices = tomllib.loads(PRICES_FILE.read_text()).get(model_name) if PRICES_FILE.exists() else None
    summary: dict[str, Any] = {}
    for arm in sorted({r["arm"] for r in records}):
        rows = [r for r in records if r["arm"] == arm]
        done = [r for r in rows if r["completed"]]
        calls = [c for r in rows for c in r["calls"]]
        good = [c for c in calls if c[1] in GOOD_CALLS]
        tokens_in = sum(r.get("input_tokens", 0) for r in rows)
        tokens_out = sum(r.get("output_tokens", 0) for r in rows)
        cost = (tokens_in * prices["input"] + tokens_out * prices["output"]) / 1_000_000 if prices else None
        by_category: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for r in rows:
            by_category[r["category"]][0] += r["completed"]
            by_category[r["category"]][1] += 1
        hard, easy = [r for r in rows if r["hard"]], [r for r in rows if not r["hard"]]
        summary[arm] = {
            "runs": len(rows),
            "completed": [len(done), len(rows)],
            "completed_hard": [sum(r["completed"] for r in hard), len(hard)],
            "completed_easy": [sum(r["completed"] for r in easy), len(easy)],
            "wrong_grants": sum(len(r["wrong_grants"]) for r in rows),
            "runs_with_a_wrong_grant": sum(bool(r["wrong_grants"]) for r in rows),
            "errors": sum(r["outcome"] == "error" for r in rows),
            "gave_up": sum(r["outcome"] == "gave_up" for r in rows),
            "tool_calls": [len(good), len(calls)],
            "model_calls_per_run": sum(r.get("model_calls", 0) for r in rows) / len(rows),
            "input_tokens": tokens_in,
            "output_tokens": tokens_out,
            "cost": cost,
            "cost_per_completed": (cost / len(done)) if cost is not None and done else None,
            "by_category": {k: v for k, v in sorted(by_category.items())},
        }
    return summary


def render(summary: dict[str, Any], model_name: str) -> str:
    arms = list(summary)
    lines = [f"Model: {model_name}", "", "| | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]

    def row(label: str, cell: Any) -> None:
        lines.append(f"| {label} | " + " | ".join(cell(summary[a]) for a in arms) + " |")

    def money(value: float | None, digits: int) -> str:
        return "no price set" if value is None else f"${value:.{digits}f}"

    row("Runs", lambda s: str(s["runs"]))
    row("Task completion", lambda s: _share(*s["completed"]))
    row("Completion, easy tasks", lambda s: _share(*s["completed_easy"]))
    row("Completion, hard tasks", lambda s: _share(*s["completed_hard"]))
    row("Wrong grants", lambda s: f"{s['wrong_grants']} in {s['runs_with_a_wrong_grant']} runs")
    row("First-try tool-call success", lambda s: _share(*s["tool_calls"]))
    row("Gave up or crashed", lambda s: str(s["gave_up"] + s["errors"]))
    row("Model calls per run", lambda s: f"{s['model_calls_per_run']:.1f}")
    row("Tokens in / out", lambda s: f"{s['input_tokens']:,} / {s['output_tokens']:,}")
    row("Model cost at list price", lambda s: money(s["cost"], 2))
    row("Cost per completed task", lambda s: money(s["cost_per_completed"], 4))

    lines += ["", "Completion by case:", "", "| Case | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
    for category in sorted({c for a in arms for c in summary[a]["by_category"]}):
        cells = []
        for a in arms:
            done, total = summary[a]["by_category"].get(category, [0, 0])
            cells.append(f"{done} of {total}")
        lines.append(f"| {category} | " + " | ".join(cells) + " |")
    wrong = sum(summary[a]["wrong_grants"] for a in arms)
    lines += ["", "Pass: zero wrong grants." if wrong == 0 else f"FAIL: {wrong} wrong grant(s)."]
    return "\n".join(lines)


def load_records(run_dir: Path) -> list[dict[str, Any]]:
    """Read a run's records. If a task ran more than once, the last attempt counts."""
    path = run_dir / "records.jsonl"
    if not path.exists():
        return []
    latest: dict[tuple[str, str, int], dict[str, Any]] = {}
    for line in path.read_text().splitlines():
        if line.strip():
            record = json.loads(line)
            latest[(record["arm"], record["task_id"], record["repeat"])] = record
    return list(latest.values())


def run_eval(
    tasks: list[Task], arms: list[str], repeats: int, model: Model, run_dir: Path, *, quiet: bool = False
) -> list[dict[str, Any]]:
    run_dir.mkdir(parents=True, exist_ok=True)
    # A crash is about the run, not the task, so crashed tasks run again when a run is continued.
    records = [r for r in load_records(run_dir) if r["outcome"] != "error"]
    seen = {(r["arm"], r["task_id"], r["repeat"]) for r in records}
    with (run_dir / "records.jsonl").open("a") as out:
        for repeat in range(1, repeats + 1):
            for task in tasks:
                for arm in arms:
                    if (arm, task.id, repeat) in seen:
                        continue
                    record = run_one(arm, task, repeat, model, run_dir.name)
                    out.write(json.dumps(record) + "\n")
                    out.flush()
                    records.append(record)
                    if not quiet:
                        mark = "ok  " if record["completed"] else "MISS"
                        wrong = "  WRONG GRANT" if record["wrong_grants"] else ""
                        print(f"{mark} {arm:<8} {task.id} r{repeat} {task.category:<28} {record['outcome']}{wrong}")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--arm", choices=["workflow", "agent", "both"], default="both")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--limit", type=int, help="Run a spread of this many tasks, for a quick look.")
    parser.add_argument("--split", choices=["test", "dev", "all"], default="test", help="dev is for debugging.")
    parser.add_argument("--tasks", type=Path, default=TASKS_FILE)
    parser.add_argument("--run-id", help="Continue an earlier run.")
    parser.add_argument("--report", type=Path, help="Print the table for a finished run and stop.")
    args = parser.parse_args()

    if args.report:
        meta = json.loads((args.report / "meta.json").read_text())
        print(render(summarize(load_records(args.report), meta["model"]), meta["model"]))
        return

    tasks = [t for t in load_tasks(args.tasks) if args.split in ("all", t.split)]
    if args.limit:
        # Every nth task, so a short run still covers each kind of case.
        step = max(1, len(tasks) // args.limit)
        tasks = tasks[::step][: args.limit]
    model = ClaudeModel()
    run_dir = RUNS_DIR / (args.run_id or uuid.uuid4().hex[:8])
    run_dir.mkdir(parents=True, exist_ok=True)
    meta = {"model": model.name, "tasks": len(tasks), "repeats": args.repeats, "arm": args.arm, "split": args.split}
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=1))
    arms = ["workflow", "agent"] if args.arm == "both" else [args.arm]

    records = run_eval(tasks, arms, args.repeats, model, run_dir)
    report = render(summarize(records, model.name), model.name)
    (run_dir / "report.md").write_text(report + "\n")
    print(f"\n{report}\n\nSaved to {run_dir}")


if __name__ == "__main__":
    main()
