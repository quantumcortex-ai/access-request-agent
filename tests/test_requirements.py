"""Every label points at a requirement, and every requirement it points at exists."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = (ROOT / "docs" / "requirements.md").read_text()
TRACE = tomllib.loads((ROOT / "tasks" / "label-rules.toml").read_text())

BUSINESS = set(re.findall(r"^### (BR-\d\d):", REQUIREMENTS, flags=re.M))
TECHNICAL = set(re.findall(r"^\| (TR-\d\d) \|", REQUIREMENTS, flags=re.M))


def _rows(name: str) -> list[dict]:
    return [json.loads(line) for line in (ROOT / "tasks" / name).read_text().splitlines() if line.strip()]


def test_every_generated_category_and_dev_probe_is_traced():
    assert {t["category"] for t in _rows("tasks.jsonl")} == set(TRACE["generated"])
    assert {t["category"] for t in _rows("dev-probes.jsonl")} == set(TRACE["dev-probes"])


def test_every_test_request_is_traced():
    assert {t["id"] for t in _rows("test.jsonl")} == set(TRACE["test"])


def test_a_label_cites_only_business_requirements_that_exist():
    for section in TRACE.values():
        for key, cited in section.items():
            assert cited, key
            assert set(cited) <= BUSINESS, key


def test_every_business_requirement_is_behind_at_least_one_label():
    cited = {r for section in TRACE.values() for rules in section.values() for r in rules}
    assert cited == BUSINESS


def test_a_technical_requirement_serves_business_requirements_that_exist():
    assert TECHNICAL
    for line in REQUIREMENTS.splitlines():
        if re.match(r"^\| TR-\d\d \|", line):
            serves = line.split("|")[3]
            for low, high in re.findall(r"BR-(\d\d) to BR-(\d\d)", serves):
                assert {f"BR-{n:02d}" for n in range(int(low), int(high) + 1)} <= BUSINESS
            assert set(re.findall(r"BR-\d\d", serves)) <= BUSINESS
