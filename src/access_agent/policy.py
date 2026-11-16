"""Policy as code: deny by default, rules in a data file.

The gateway works out the facts from the directory. Nothing the model says is
a fact. A call is allowed only when no deny rule matches and one allow rule
does.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_RULES = Path(__file__).resolve().parents[2] / "policy" / "rules.toml"

KNOWN_KEYS = {"id", "effect", "tools", "actors", "when", "reason"}
KNOWN_FACTS = {"group_tier", "user_status", "department_eligible", "approval", "match_settled"}


@dataclass(frozen=True)
class Rule:
    id: str
    effect: str
    tools: tuple[str, ...]
    actors: tuple[str, ...]
    when: dict[str, tuple[str, ...]]
    reason: str

    def matches(self, actor: str, tool: str, facts: dict[str, str]) -> bool:
        if tool not in self.tools:
            return False
        if self.actors and actor not in self.actors:
            return False
        return all(facts.get(key) in allowed for key, allowed in self.when.items())


@dataclass(frozen=True)
class Decision:
    allowed: bool
    rule_id: str
    reason: str


def load_rules(path: Path = DEFAULT_RULES) -> list[Rule]:
    """Read the rules, and refuse a file with a typo in it.

    A misspelled key that was silently ignored would make a rule match more
    than its author meant.
    """
    raw = tomllib.loads(path.read_text())
    rules: list[Rule] = []
    seen: set[str] = set()
    for entry in raw.get("rule", []):
        unknown = set(entry) - KNOWN_KEYS
        if unknown:
            raise ValueError(f"rule {entry.get('id', '?')}: unknown keys {sorted(unknown)}")
        rule_id = entry["id"]
        if rule_id in seen:
            raise ValueError(f"rule {rule_id}: duplicate id")
        seen.add(rule_id)
        if entry["effect"] not in ("allow", "deny"):
            raise ValueError(f"rule {rule_id}: effect must be allow or deny")
        when: dict[str, Any] = entry.get("when", {})
        bad_facts = set(when) - KNOWN_FACTS
        if bad_facts:
            raise ValueError(f"rule {rule_id}: unknown facts {sorted(bad_facts)}")
        rules.append(
            Rule(
                id=rule_id,
                effect=entry["effect"],
                tools=tuple(entry["tools"]),
                actors=tuple(entry.get("actors", ())),
                when={key: tuple(values) for key, values in when.items()},
                reason=entry.get("reason", ""),
            )
        )
    return rules


def decide(rules: list[Rule], actor: str, tool: str, facts: dict[str, str]) -> Decision:
    for rule in rules:
        if rule.effect == "deny" and rule.matches(actor, tool, facts):
            return Decision(False, rule.id, rule.reason)
    for rule in rules:
        if rule.effect == "allow" and rule.matches(actor, tool, facts):
            return Decision(True, rule.id, rule.reason)
    return Decision(False, "default-deny", "No rule allows this action.")
