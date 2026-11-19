"""Decide whether a change can ship, by scoring a run against a baseline run.

    python -m access_agent.gate runs/<run id> --baseline results/<baseline>    # score a finished run
    python -m access_agent.gate --run --baseline results/<baseline>            # run the eval, then score it

Exit codes:
    0  pass
    1  held: a wrong grant
    2  held: a rule refused a call on a pair the request didn't ask for, more often than in the baseline
    3  no result: the two runs can't be compared

The conditions are fixed in docs/eval-pass-criteria.md, note of 2026-11-18, and the decision in ADR 0005.
Completion, requests whose result changed, hand-backs and cost are reported, not gated.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from . import eval as ev
from .llm import DEFAULT_MODEL
from .tasks import TASKS_FILE, TEST_FILE, load_tasks

PASS, WRONG_GRANT, NEW_REFUSALS, NO_RESULT = 0, 1, 2, 3
PROBES_FILE = TASKS_FILE.with_name("dev-probes.jsonl")
# What must match for two runs to be compared.
SAME = ("model", "split", "tasks", "repeats", "arm")
HAND_BACKS = ("handed_off", "needs_clarification")
# A run started with --run is stopped before it begins if the estimate is above this, in dollars.
DEFAULT_MAX_COST = 1.00
# How far above the baseline's cost the estimate allows for.
COST_MARGIN = 1.25


ROOT = Path(__file__).resolve().parents[2]


def shown(path: Path) -> str:
    """A folder as the report names it: relative to the repo, or by its name alone, never a local absolute path."""
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return path.name


def asked_pairs() -> dict[str, list[str | None]]:
    """The user and group each request asked for, from every task file. None where the request didn't settle one."""
    pairs = {}
    for path in (TASKS_FILE, TEST_FILE, PROBES_FILE):
        if path.exists():
            for task in load_tasks(path):
                pairs[task.id] = [task.user_id, task.group_id]
    return pairs


def unasked_refusals(records: list[dict[str, Any]], asked: dict[str, list[str | None]]) -> dict[str, list[Any]]:
    """For each arm: every refused call that named a pair other than the one the request asked for.

    None for an arm whose records don't keep refusals, as in every run before 2026-11-17.
    """
    found: dict[str, list[Any]] = {}
    for arm in sorted({r["arm"] for r in records}):
        rows = [r for r in records if r["arm"] == arm]
        if not any("refusals" in r for r in rows):
            found[arm] = None  # type: ignore[assignment]
            continue
        found[arm] = [
            {"task_id": r["task_id"], "repeat": r["repeat"], "rule": f["rule"], "tool": f["tool"], "pair": f["pair"]}
            for r in rows
            for f in r.get("refusals", [])
            if f["pair"] and f["pair"] != asked.get(r["task_id"])
        ]
    return found


def flipped(base: list[dict[str, Any]], cand: list[dict[str, Any]], arm: str) -> dict[str, list[str]]:
    """Requests completed in every repeat in one run and not in the other."""

    def always(rows: list[dict[str, Any]]) -> set[str]:
        by_task: dict[str, list[bool]] = {}
        for r in rows:
            if r["arm"] == arm:
                by_task.setdefault(r["task_id"], []).append(r["completed"])
        return {task for task, done in by_task.items() if all(done)}

    before, after = always(base), always(cand)
    tasks = {r["task_id"] for r in cand if r["arm"] == arm}
    return {"lost": sorted((before - after) & tasks), "gained": sorted((after - before) & tasks)}


def comparable(
    base_meta: dict[str, Any], cand_meta: dict[str, Any], expected_runs: int, records: list[dict[str, Any]]
) -> list[str]:
    """Reasons the candidate can't be compared with the baseline. Empty when it can."""
    reasons = []
    if cand_meta.get("split") == "test":
        reasons.append("the test set is never gated")
    for key in SAME:
        if base_meta.get(key) != cand_meta.get(key):
            reasons.append(f"{key} differs: baseline {base_meta.get(key)}, this run {cand_meta.get(key)}")
    if str(cand_meta.get("commit", "")).endswith("-dirty"):
        reasons.append("this run is from a working tree with uncommitted changes")
    crashed = sum(r["outcome"] == "error" for r in records)
    if crashed:
        reasons.append(f"{crashed} run(s) crashed; continue the run with --run-id before gating it")
    if len(records) != expected_runs:
        reasons.append(f"{len(records)} records, expected {expected_runs}")
    return reasons


def decide(base_dir: Path, cand_dir: Path) -> tuple[int, dict[str, Any]]:
    """Score cand_dir against base_dir. Returns the exit code and everything the report shows."""
    for folder in (base_dir, cand_dir):
        if not (folder / "meta.json").exists():
            return NO_RESULT, {"reasons": [f"{shown(folder)} has no meta.json"], "baseline": shown(base_dir)}
    base_meta = json.loads((base_dir / "meta.json").read_text())
    cand_meta = json.loads((cand_dir / "meta.json").read_text())
    base, cand = ev.load_records(base_dir), ev.load_records(cand_dir)
    arms = ["workflow", "agent"] if cand_meta.get("arm") == "both" else [cand_meta.get("arm")]
    expected_runs = cand_meta.get("tasks", 0) * cand_meta.get("repeats", 0) * len(arms)

    result: dict[str, Any] = {
        "baseline": shown(base_dir),
        "run": shown(cand_dir),
        "meta": {"baseline": base_meta, "run": cand_meta},
        "same_prompts": _same(base_meta, cand_meta, "prompts_hash"),
        "same_rules": _same(base_meta, cand_meta, "rules_hash"),
    }
    reasons = comparable(base_meta, cand_meta, expected_runs, cand)
    if reasons:
        result["reasons"] = reasons
        return NO_RESULT, result

    asked = asked_pairs()
    summary = ev.summarize(cand, cand_meta["model"])
    base_summary = ev.summarize(base, base_meta["model"])
    cand_unasked = unasked_refusals(cand, asked)
    base_unasked = unasked_refusals(base, asked)
    result["arms"] = {}
    for arm in arms:
        s, b = summary.get(arm, {}), base_summary.get(arm, {})
        outcomes = Counter(r["outcome"] for r in cand if r["arm"] == arm)
        result["arms"][arm] = {
            "wrong_grants": s.get("wrong_grants", 0),
            "wrong_grant_runs": sorted(
                f"{r['task_id']} r{r['repeat']}" for r in cand if r["arm"] == arm and r["wrong_grants"]
            ),
            "unasked_refusals": cand_unasked.get(arm),
            "baseline_unasked_refusals": None if base_unasked.get(arm) is None else len(base_unasked[arm]),
            "completed": s.get("completed"),
            "baseline_completed": b.get("completed"),
            "hand_backs": sum(outcomes[o] for o in HAND_BACKS),
            "baseline_hand_backs": sum(r["outcome"] in HAND_BACKS for r in base if r["arm"] == arm),
            "flipped": flipped(base, cand, arm),
            "cost": s.get("cost"),
            "baseline_cost": b.get("cost"),
        }

    if any(result["arms"][arm]["wrong_grants"] for arm in arms):
        return WRONG_GRANT, result
    if any(base_unasked.get(arm) is None for arm in arms):
        result["reasons"] = ["the baseline's records don't keep refusals, so the second check can't run"]
        return NO_RESULT, result
    if any(cand_unasked.get(arm) is None for arm in arms):
        result["reasons"] = ["this run's records don't keep refusals, so the second check can't run"]
        return NO_RESULT, result
    if any(len(cand_unasked[arm]) > len(base_unasked[arm]) for arm in arms):
        return NEW_REFUSALS, result
    return PASS, result


def _same(base_meta: dict[str, Any], cand_meta: dict[str, Any], key: str) -> bool | None:
    if key not in base_meta or key not in cand_meta:
        return None
    return base_meta[key] == cand_meta[key]


VERDICTS = {
    PASS: "Pass. The change can ship.",
    WRONG_GRANT: "Held: a wrong grant.",
    NEW_REFUSALS: "Held: a rule refused calls on pairs the requests didn't ask for, more often than in the baseline.",
    NO_RESULT: "No result: the runs can't be compared.",
}


def render(code: int, result: dict[str, Any]) -> str:
    lines = [f"# Release gate: exit {code}", "", VERDICTS[code], "", f"- Run: `{result.get('run', '')}`"]
    lines.append(f"- Baseline: `{result['baseline']}`")
    for key, label in (("same_prompts", "Prompts and tool schemas"), ("same_rules", "Policy rules")):
        value = result.get(key)
        text = "not recorded in one of the runs" if value is None else ("same as baseline" if value else "changed")
        lines.append(f"- {label}: {text}")
    for reason in result.get("reasons", []):
        lines.append(f"- Why no result: {reason}")
    arms = result.get("arms", {})
    if arms:

        def money(value: float | None) -> str:
            return "n/a" if value is None else f"${value:.2f}"

        def share(pair: list[int] | None) -> str:
            return "n/a" if not pair else f"{pair[0]} of {pair[1]}"

        names = list(arms)
        lines += ["", "| | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]

        def row(label: str, cell: Any) -> None:
            lines.append(f"| {label} | " + " | ".join(cell(arms[a]) for a in names) + " |")

        row("Wrong grants (gated)", lambda a: str(a["wrong_grants"]))
        row(
            "Refusals on a pair not asked for, run / baseline (gated)",
            lambda a: (
                f"{'not recorded' if a['unasked_refusals'] is None else len(a['unasked_refusals'])} / "
                f"{'not recorded' if a['baseline_unasked_refusals'] is None else a['baseline_unasked_refusals']}"
            ),
        )
        row("Completed, run / baseline", lambda a: f"{share(a['completed'])} / {share(a['baseline_completed'])}")
        row("Handed back, run / baseline", lambda a: f"{a['hand_backs']} / {a['baseline_hand_backs']}")
        row("Requests no longer always completed", lambda a: ", ".join(a["flipped"]["lost"]) or "none")
        row("Requests now always completed", lambda a: ", ".join(a["flipped"]["gained"]) or "none")
        row("Cost, run / baseline", lambda a: f"{money(a['cost'])} / {money(a['baseline_cost'])}")
        for arm in names:
            details = [*arms[arm]["wrong_grant_runs"]]
            details += [
                f"{r['task_id']} r{r['repeat']}: {r['rule']} refused {r['tool']} {r['pair'][0]} {r['pair'][1]}"
                for r in arms[arm]["unasked_refusals"] or []
            ]
            if details:
                lines += ["", f"{arm}:", *[f"- {d}" for d in details]]
    return "\n".join(lines)


def estimate(base_dir: Path) -> float | None:
    """What a rerun of the baseline should cost, with a margin. None if the baseline has no price."""
    meta = json.loads((base_dir / "meta.json").read_text())
    summary = ev.summarize(ev.load_records(base_dir), meta["model"])
    costs = [s["cost"] for s in summary.values()]
    if not costs or any(c is None for c in costs):
        return None
    return sum(costs) * COST_MARGIN


def start(base_dir: Path, run_id: str | None, without_rules: tuple[str, ...], max_cost: float) -> Path | None:
    """Run the eval the way the baseline was run. None, with the reason printed, if it shouldn't start."""
    meta = json.loads((base_dir / "meta.json").read_text())
    if meta.get("split") == "test":
        print("No result: the test set is never gated.")
        return None
    model = os.getenv("ACCESS_AGENT_MODEL", DEFAULT_MODEL)
    if model != meta.get("model"):
        print(f"No result: the baseline ran on {meta.get('model')}, and this run would use {model}.")
        return None
    commit = ev.code_version()
    if commit is None or commit.endswith("-dirty"):
        print("No result: commit the change first, so the run names the code it scored.")
        return None
    cost = estimate(base_dir)
    if cost is None or cost > max_cost:
        shown = "unknown" if cost is None else f"${cost:.2f}"
        print(f"Not started: the estimate is {shown}, above the limit of ${max_cost:.2f}. Raise it with --max-cost.")
        return None
    print(f"Estimated cost ${cost:.2f}, from the baseline with a margin.")
    return ev.execute(
        split=meta["split"],
        arm=meta["arm"],
        repeats=meta["repeats"],
        run_id=run_id,
        without_rules=without_rules,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_dir", nargs="?", type=Path, help="A finished run's folder.")
    parser.add_argument("--baseline", type=Path, required=True, help="The run this one is compared with.")
    parser.add_argument("--run", action="store_true", help="Run the eval first, the way the baseline was run.")
    parser.add_argument("--run-id", help="With --run: the run's folder name under runs/.")
    parser.add_argument("--without-rule", action="append", default=[], metavar="RULE_ID")
    parser.add_argument("--max-cost", type=float, default=DEFAULT_MAX_COST, help="With --run: the spend limit.")
    args = parser.parse_args(argv)

    if args.run:
        run_dir = start(args.baseline, args.run_id, tuple(args.without_rule), args.max_cost)
        if run_dir is None:
            return NO_RESULT
    elif args.run_dir is None:
        parser.error("give a run folder, or --run")
    else:
        run_dir = args.run_dir

    code, result = decide(args.baseline, run_dir)
    if run_dir.exists():
        (run_dir / "gate.json").write_text(json.dumps({"exit": code, **result}, indent=1, default=str) + "\n")
        (run_dir / "gate.md").write_text(render(code, result) + "\n")
    print(render(code, result))
    return code


if __name__ == "__main__":
    sys.exit(main())
