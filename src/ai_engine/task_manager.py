"""Coordinate durable task transitions and real background execution."""

from __future__ import annotations

import threading
import json
from pathlib import Path
from typing import Any, Protocol

from .kaggle_executor import KaggleExecutor
from .project_store import ProjectStore, validate_project
from .task_store import TERMINAL_STATUSES, TaskStore, TaskStoreError


class TaskExecutor(Protocol):
    def prepare(self, task: dict[str, Any], project: dict[str, Any]) -> dict[str, str]: ...

    def submit(self, prepared: dict[str, str]) -> str: ...

    def wait(self, task: dict[str, Any], prepared: dict[str, str]) -> dict[str, Any]: ...

    def validate(
        self,
        task: dict[str, Any],
        prepared: dict[str, str],
        execution: dict[str, Any],
    ) -> dict[str, Any]: ...


class TaskManager:
    """Persist tasks before starting a worker and persist every state transition."""

    def __init__(
        self,
        project_store: ProjectStore,
        task_store: TaskStore,
        executor: TaskExecutor | None = None,
    ) -> None:
        self.project_store = project_store
        self.task_store = task_store
        self.executor = executor or KaggleExecutor(
            Path(__file__).resolve().parents[2]
        )
        self._lock = threading.Lock()
        self._threads: dict[str, threading.Thread] = {}
        self._recover_active_tasks()

    def create_task(self, project_id: str) -> dict[str, Any]:
        project = self.project_store.load(project_id)
        with self._lock:
            active = self.task_store.active_tasks()
            if active:
                raise TaskStoreError(
                    f"Task {active[0]['id']} is already {active[0]['status']}; "
                    "wait for it to finish before starting another Kaggle task."
                )
            task = self.task_store.create(
                project["id"],
                self.task_store.database.parent / "runs",
            )
            snapshot_path = Path(task["work_directory"]) / "project-snapshot.json"
            try:
                snapshot_path.write_text(
                    json.dumps(project, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8",
                )
            except OSError as exc:
                self._fail(task["id"], f"Could not persist the task project snapshot: {exc}")
                raise TaskStoreError(
                    f"Cannot persist task project snapshot: {exc}"
                ) from exc
            self._launch(task["id"])
        return task

    def get_task(self, task_id: str) -> dict[str, Any]:
        return self.task_store.get(task_id)

    def list_for_project(self, project_id: str) -> list[dict[str, Any]]:
        self.project_store.load(project_id)
        return self.task_store.list_for_project(project_id)

    def _recover_active_tasks(self) -> None:
        for task in self.task_store.active_tasks():
            if task["status"] == "preparing":
                self._fail(
                    task["id"],
                    "The local service restarted during task preparation. "
                    "The remote submission state is unknown; start a new task after review.",
                )
            else:
                self._launch(task["id"])

    def _launch(self, task_id: str) -> None:
        existing = self._threads.get(task_id)
        if existing is not None and existing.is_alive():
            return
        thread = threading.Thread(
            target=self._run,
            args=(task_id,),
            name=f"ai-engine-task-{task_id[:8]}",
            daemon=True,
        )
        self._threads[task_id] = thread
        thread.start()

    def _run(self, task_id: str) -> None:
        try:
            task = self.task_store.get(task_id)
            snapshot_path = Path(task["work_directory"]) / "project-snapshot.json"
            if not snapshot_path.is_file():
                raise TaskStoreError(
                    "The immutable project snapshot is missing; refusing to resume this task."
                )
            try:
                project = validate_project(
                    json.loads(snapshot_path.read_text(encoding="utf-8"))
                )
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                raise TaskStoreError(f"The immutable project snapshot is invalid: {exc}") from exc
            if project["id"] != task["project_id"]:
                raise TaskStoreError("Task project snapshot identity does not match its task.")
            work_directory = Path(task["work_directory"])
            prepared = {
                "work_directory": str(work_directory),
                "upload_directory": str(work_directory / "upload"),
                "project_file": str(work_directory / "submitted-project.json"),
            }
            if task["status"] == "queued":
                self.task_store.transition(
                    task_id,
                    "preparing",
                    "Validating the saved project and preparing a CPU-only Kaggle job.",
                )
                prepared = self.executor.prepare(task, project)
                run_id = self.executor.submit(prepared)
                task = self.task_store.transition(
                    task_id,
                    "running",
                    f"Kaggle kernel version {run_id} was submitted; monitoring its status.",
                    run_id=run_id,
                )
            if task["status"] in {"running", "validating"}:
                execution = self.executor.wait(task, prepared)
                if task["status"] == "running":
                    task = self.task_store.transition(
                        task_id,
                        "validating",
                        "Kaggle returned terminal status "
                        f"{execution.get('remote_status', 'unknown')}; validating "
                        "the task-specific report and Blender evidence.",
                    )
                result = self.executor.validate(task, prepared, execution)
                completion_message = (
                    "Blender 4.0.2 scene, reopen, physics, MP4 render, decode, and motion checks passed."
                )
                if execution.get("remote_status") == "CANCEL_ACKNOWLEDGED":
                    completion_message = (
                        "Kaggle acknowledged cancellation after emitting this task's report; "
                        "the task-specific physics, render, and video checks passed."
                    )
                self.task_store.transition(
                    task_id,
                    "succeeded",
                    completion_message,
                    result=result,
                )
        except Exception as exc:
            self._fail(task_id, f"{type(exc).__name__}: {exc}")
        finally:
            with self._lock:
                self._threads.pop(task_id, None)

    def _fail(self, task_id: str, error: str) -> None:
        try:
            current = self.task_store.get(task_id)
            if current["status"] not in TERMINAL_STATUSES:
                self.task_store.transition(
                    task_id,
                    "failed",
                    "Task failed; the reason is recorded for the user.",
                    error=error[:4000],
                )
        except Exception as persistence_error:
            print(
                "[task-manager] Could not persist task failure: "
                f"{type(persistence_error).__name__}: {persistence_error}"
            )
