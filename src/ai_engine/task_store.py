"""Persistent task state and append-only task event history."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

TASK_STATUSES = {
    "queued",
    "preparing",
    "running",
    "validating",
    "succeeded",
    "failed",
}
TERMINAL_STATUSES = {"succeeded", "failed"}
_TRANSITIONS = {
    "queued": {"preparing", "failed"},
    "preparing": {"running", "failed"},
    "running": {"validating", "failed"},
    "validating": {"succeeded", "failed"},
    "succeeded": set(),
    "failed": set(),
}


class TaskStoreError(RuntimeError):
    """Raised when task state cannot safely be persisted or loaded."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _validate_id(task_id: str) -> str:
    try:
        parsed = UUID(task_id)
    except (ValueError, AttributeError, TypeError) as exc:
        raise TaskStoreError("Task ID must be a canonical lowercase UUID.") from exc
    if str(parsed) != task_id:
        raise TaskStoreError("Task ID must be a canonical lowercase UUID.")
    return task_id


class TaskStore:
    """Store task state in SQLite and retain every accepted state transition."""

    def __init__(self, database: str | Path) -> None:
        self.database = Path(database).expanduser()
        if self.database.is_symlink():
            raise TaskStoreError("Task database must not be a symbolic link.")
        self.database = self.database.resolve()
        try:
            self.database.parent.mkdir(parents=True, exist_ok=True)
            self._initialize()
        except OSError as exc:
            raise TaskStoreError(f"Cannot initialize task storage: {exc}") from exc

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    error TEXT,
                    run_id TEXT,
                    result_json TEXT NOT NULL,
                    work_directory TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS task_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL REFERENCES tasks(id),
                    created_at TEXT NOT NULL,
                    from_status TEXT,
                    to_status TEXT NOT NULL,
                    message TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS task_project_idx ON tasks(project_id, created_at)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS task_events_idx ON task_events(task_id, sequence)"
            )

    def create(self, project_id: str, work_directory_root: str | Path) -> dict[str, Any]:
        task_id = str(uuid4())
        created_at = _now()
        work_path = Path(work_directory_root).resolve() / task_id
        try:
            work_path.mkdir(parents=True, exist_ok=False)
            with closing(self._connect()) as connection, connection:
                connection.execute(
                    """
                    INSERT INTO tasks (
                        id, project_id, status, created_at, result_json, work_directory
                    ) VALUES (?, ?, 'queued', ?, '{}', ?)
                    """,
                    (task_id, project_id, created_at, str(work_path)),
                )
                connection.execute(
                    """
                    INSERT INTO task_events (
                        task_id, created_at, from_status, to_status, message
                    ) VALUES (?, ?, NULL, 'queued', ?)
                    """,
                    (task_id, created_at, "Task accepted and queued."),
                )
        except sqlite3.Error as exc:
            raise TaskStoreError(f"Cannot create task: {exc}") from exc
        except OSError as exc:
            raise TaskStoreError(f"Cannot create task work directory: {exc}") from exc
        return self.get(task_id)

    def transition(
        self,
        task_id: str,
        status: str,
        message: str,
        *,
        run_id: str | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        _validate_id(task_id)
        if status not in TASK_STATUSES:
            raise TaskStoreError(f"Unsupported task status: {status}")
        if not isinstance(message, str) or not message.strip():
            raise TaskStoreError("Task event message must not be empty.")
        now = _now()
        try:
            with closing(self._connect()) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT * FROM tasks WHERE id = ?", (task_id,)
                ).fetchone()
                if row is None:
                    raise TaskStoreError(f"Task not found: {task_id}")
                previous = str(row["status"])
                if status not in _TRANSITIONS.get(previous, set()):
                    raise TaskStoreError(
                        f"Invalid task transition: {previous} -> {status}."
                    )
                started_at = row["started_at"]
                completed_at = row["completed_at"]
                if status == "preparing" and started_at is None:
                    started_at = now
                if status in TERMINAL_STATUSES:
                    completed_at = now
                if status == "failed" and (not isinstance(error, str) or not error.strip()):
                    raise TaskStoreError("A failed task requires an explicit error message.")
                if status != "failed" and error is not None:
                    raise TaskStoreError("Only failed tasks may contain an error message.")
                if result is not None and status != "succeeded":
                    raise TaskStoreError("Task results may only be recorded on success.")
                existing_result = json.loads(str(row["result_json"]))
                updated_result = existing_result if result is None else result
                serialized_result = json.dumps(
                    updated_result,
                    ensure_ascii=False,
                    allow_nan=False,
                    sort_keys=True,
                )
                connection.execute(
                    """
                    UPDATE tasks SET status = ?, started_at = ?, completed_at = ?,
                        error = ?, run_id = COALESCE(?, run_id), result_json = ?
                    WHERE id = ?
                    """,
                    (
                        status,
                        started_at,
                        completed_at,
                        error,
                        run_id,
                        serialized_result,
                        task_id,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO task_events (
                        task_id, created_at, from_status, to_status, message
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (task_id, now, previous, status, message.strip()),
                )
        except sqlite3.Error as exc:
            raise TaskStoreError(f"Cannot update task {task_id}: {exc}") from exc
        return self.get(task_id)

    def get(self, task_id: str) -> dict[str, Any]:
        _validate_id(task_id)
        try:
            with closing(self._connect()) as connection, connection:
                row = connection.execute(
                    "SELECT * FROM tasks WHERE id = ?", (task_id,)
                ).fetchone()
                if row is None:
                    raise TaskStoreError(f"Task not found: {task_id}")
                events = connection.execute(
                    """
                    SELECT created_at, from_status, to_status, message
                    FROM task_events WHERE task_id = ? ORDER BY sequence
                    """,
                    (task_id,),
                ).fetchall()
        except sqlite3.Error as exc:
            raise TaskStoreError(f"Cannot load task {task_id}: {exc}") from exc
        return {
            "id": row["id"],
            "project_id": row["project_id"],
            "status": row["status"],
            "created_at": row["created_at"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "error": row["error"],
            "run_id": row["run_id"],
            "result": json.loads(str(row["result_json"])),
            "work_directory": row["work_directory"],
            "events": [
                {
                    "created_at": event["created_at"],
                    "from_status": event["from_status"],
                    "to_status": event["to_status"],
                    "message": event["message"],
                }
                for event in events
            ],
        }

    def list_for_project(self, project_id: str) -> list[dict[str, Any]]:
        try:
            with closing(self._connect()) as connection, connection:
                rows = connection.execute(
                    "SELECT id FROM tasks WHERE project_id = ? ORDER BY created_at DESC",
                    (project_id,),
                ).fetchall()
        except sqlite3.Error as exc:
            raise TaskStoreError(f"Cannot list tasks for project {project_id}: {exc}") from exc
        return [self.get(str(row["id"])) for row in rows]

    def active_tasks(self) -> list[dict[str, Any]]:
        try:
            with closing(self._connect()) as connection, connection:
                rows = connection.execute(
                    """
                    SELECT id FROM tasks
                    WHERE status NOT IN ('succeeded', 'failed')
                    ORDER BY created_at
                    """
                ).fetchall()
        except sqlite3.Error as exc:
            raise TaskStoreError(f"Cannot list active tasks: {exc}") from exc
        return [self.get(str(row["id"])) for row in rows]
