from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class SQLiteStateStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                requested_by TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS approvals (
                queue_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                status TEXT NOT NULL,
                approver_group TEXT,
                updated_at TEXT NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS approval_actions (
                action_id TEXT PRIMARY KEY,
                queue_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS run_idempotency (
                task_id TEXT NOT NULL,
                idem_key TEXT NOT NULL,
                task_ref TEXT NOT NULL,
                PRIMARY KEY (task_id, idem_key)
            );
            """
        )
        self.conn.commit()

    @staticmethod
    def _json(value: dict[str, Any]) -> str:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    def load_state(self) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]], dict[tuple[str, str], str]]:
        tasks: dict[str, dict[str, Any]] = {}
        events: list[dict[str, Any]] = []
        approvals: dict[str, dict[str, Any]] = {}
        actions: list[dict[str, Any]] = []
        idempotency: dict[tuple[str, str], str] = {}

        for row in self.conn.execute("SELECT payload FROM tasks"):
            item = json.loads(row["payload"])
            tasks[item["task_id"]] = item

        for row in self.conn.execute("SELECT payload FROM events ORDER BY created_at ASC"):
            events.append(json.loads(row["payload"]))

        for row in self.conn.execute("SELECT payload FROM approvals"):
            item = json.loads(row["payload"])
            approvals[item["queue_id"]] = item

        for row in self.conn.execute("SELECT payload FROM approval_actions ORDER BY created_at ASC"):
            actions.append(json.loads(row["payload"]))

        for row in self.conn.execute("SELECT task_id, idem_key, task_ref FROM run_idempotency"):
            idempotency[(row["task_id"], row["idem_key"])] = row["task_ref"]

        return tasks, events, approvals, actions, idempotency

    def save_task(self, task: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO tasks(task_id, status, requested_by, updated_at, payload)
            VALUES(?,?,?,?,?)
            ON CONFLICT(task_id) DO UPDATE SET
              status=excluded.status,
              requested_by=excluded.requested_by,
              updated_at=excluded.updated_at,
              payload=excluded.payload
            """,
            (
                task["task_id"],
                task["status"],
                task["requested_by"],
                task["updated_at"],
                self._json(task),
            ),
        )
        self.conn.commit()

    def save_event(self, event: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO events(event_id, task_id, event_type, created_at, payload)
            VALUES(?,?,?,?,?)
            """,
            (
                event["event_id"],
                event["task_id"],
                event["event_type"],
                event["created_at"],
                self._json(event),
            ),
        )
        self.conn.commit()

    def save_approval(self, approval: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO approvals(queue_id, task_id, status, approver_group, updated_at, payload)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(queue_id) DO UPDATE SET
              task_id=excluded.task_id,
              status=excluded.status,
              approver_group=excluded.approver_group,
              updated_at=excluded.updated_at,
              payload=excluded.payload
            """,
            (
                approval["queue_id"],
                approval["task_id"],
                approval["status"],
                approval.get("approver_group"),
                approval.get("resolved_at") or approval.get("created_at"),
                self._json(approval),
            ),
        )
        self.conn.commit()

    def save_approval_action(self, action: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO approval_actions(action_id, queue_id, task_id, action, created_at, payload)
            VALUES(?,?,?,?,?,?)
            """,
            (
                action["action_id"],
                action["queue_id"],
                action["task_id"],
                action["action"],
                action["created_at"],
                self._json(action),
            ),
        )
        self.conn.commit()

    def save_idempotency(self, task_id: str, idem_key: str, task_ref: str) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO run_idempotency(task_id, idem_key, task_ref)
            VALUES(?,?,?)
            """,
            (task_id, idem_key, task_ref),
        )
        self.conn.commit()
