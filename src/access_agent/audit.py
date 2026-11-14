"""An append-only audit log.

Every tool call leaves a row, allowed or not. The database refuses updates and
deletes, so the record can only grow. The eval script reads this table.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    at TEXT NOT NULL,
    run_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    tool TEXT NOT NULL,
    args TEXT NOT NULL,
    outcome TEXT NOT NULL,
    rule_id TEXT,
    reason TEXT
);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit
BEGIN SELECT RAISE(ABORT, 'audit rows cannot be changed'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit
BEGIN SELECT RAISE(ABORT, 'audit rows cannot be deleted'); END;
"""


class AuditLog:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.conn.executescript(SCHEMA)

    def write(
        self,
        *,
        run_id: str,
        task_id: str,
        actor: str,
        tool: str,
        args: dict[str, Any],
        outcome: str,
        rule_id: str | None = None,
        reason: str | None = None,
    ) -> int:
        cur = self.conn.execute(
            "INSERT INTO audit (at, run_id, task_id, actor, tool, args, outcome, rule_id, reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                datetime.now(UTC).isoformat(timespec="milliseconds"),
                run_id,
                task_id,
                actor,
                tool,
                json.dumps(args, sort_keys=True, default=str),
                outcome,
                rule_id,
                reason,
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid or 0)

    def rows(self, run_id: str | None = None) -> list[sqlite3.Row]:
        if run_id is None:
            return self.conn.execute("SELECT * FROM audit ORDER BY id").fetchall()
        return self.conn.execute("SELECT * FROM audit WHERE run_id = ? ORDER BY id", (run_id,)).fetchall()
