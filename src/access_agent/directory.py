"""A local, generated directory in SQLite.

This is the whole "identity system" of the example. There is no code here that
talks to a real directory, so a fork can't change one by accident.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from .models import Group, Status, Tier, User

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL,
    status TEXT NOT NULL,
    manager_id TEXT
);
CREATE TABLE IF NOT EXISTS groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    tier TEXT NOT NULL,
    owner_id TEXT,
    allowed_departments TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS memberships (
    user_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    added_at TEXT NOT NULL,
    added_by TEXT NOT NULL,
    PRIMARY KEY (user_id, group_id)
);
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    approver_id TEXT NOT NULL,
    approved INTEGER NOT NULL,
    decided_at TEXT NOT NULL
);
"""

MAX_RESULTS = 8


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        department=row["department"],
        status=Status(row["status"]),
        manager_id=row["manager_id"],
    )


def _group(row: sqlite3.Row) -> Group:
    departments = tuple(d for d in row["allowed_departments"].split(",") if d)
    return Group(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        tier=Tier(row["tier"]),
        owner_id=row["owner_id"],
        allowed_departments=departments,
    )


class Directory:
    def __init__(self, path: str = ":memory:") -> None:
        # LangGraph may run a node on a worker thread. Calls are still one at a time.
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    # Writes used by the seed and by tests.

    def put_user(self, user: User) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?)",
            (user.id, user.name, user.email, user.department, user.status.value, user.manager_id),
        )
        self.conn.commit()

    def put_group(self, group: Group) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO groups VALUES (?, ?, ?, ?, ?, ?)",
            (
                group.id,
                group.name,
                group.description,
                group.tier.value,
                group.owner_id,
                ",".join(group.allowed_departments),
            ),
        )
        self.conn.commit()

    # Reads.

    def get_user(self, user_id: str) -> User | None:
        row = self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _user(row) if row else None

    def get_group(self, group_id: str) -> Group | None:
        row = self.conn.execute("SELECT * FROM groups WHERE id = ?", (group_id,)).fetchone()
        return _group(row) if row else None

    def search_users(self, query: str) -> list[User]:
        like = f"%{query.lower()}%"
        rows = self.conn.execute(
            "SELECT * FROM users WHERE lower(name) LIKE ? OR lower(email) LIKE ? ORDER BY id LIMIT ?",
            (like, like, MAX_RESULTS),
        ).fetchall()
        return [_user(r) for r in rows]

    def search_groups(self, query: str) -> list[Group]:
        """Match every word of the query against the name or the description."""
        words = [w for w in query.lower().split() if w]
        clause = " AND ".join("(lower(name) LIKE ? OR lower(description) LIKE ?)" for _ in words)
        params: list[str | int] = []
        for word in words:
            params += [f"%{word}%", f"%{word}%"]
        rows = self.conn.execute(
            f"SELECT * FROM groups WHERE {clause} ORDER BY id LIMIT ?",  # noqa: S608 - clause is built from fixed text
            (*params, MAX_RESULTS),
        ).fetchall()
        return [_group(r) for r in rows]

    def is_member(self, user_id: str, group_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM memberships WHERE user_id = ? AND group_id = ?", (user_id, group_id)
        ).fetchone()
        return row is not None

    # The one write the agent can cause, and only through the gateway.

    def add_member(self, user_id: str, group_id: str, added_by: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO memberships VALUES (?, ?, ?, ?)",
            (user_id, group_id, _now(), added_by),
        )
        self.conn.commit()

    # Approvals are written by the approval step, never by a tool the model can call.

    def record_approval(self, user_id: str, group_id: str, approver_id: str, approved: bool) -> int:
        cur = self.conn.execute(
            "INSERT INTO approvals (user_id, group_id, approver_id, approved, decided_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, group_id, approver_id, int(approved), _now()),
        )
        self.conn.commit()
        return int(cur.lastrowid or 0)

    def latest_approval(self, user_id: str, group_id: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM approvals WHERE user_id = ? AND group_id = ? ORDER BY id DESC LIMIT 1",
            (user_id, group_id),
        ).fetchone()
