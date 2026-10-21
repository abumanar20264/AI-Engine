"""Loopback-only standard-library web control UI for local AI-Engine projects."""

from __future__ import annotations

import argparse
import hashlib
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast
from urllib.parse import unquote, urlsplit

from .project_service import ProjectService, default_projects_directory, validation_field
from .project_store import ProjectStore, ProjectStoreError, ProjectValidationError
from .task_manager import TaskExecutor, TaskManager
from .task_store import TaskStore, TaskStoreError

MAX_REQUEST_BYTES = 1_000_000
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ASSETS = {
    "/assets/control.css": ("control.css", "text/css; charset=utf-8"),
    "/assets/control.js": ("control.js", "text/javascript; charset=utf-8"),
}


class ControlHTTPServer(ThreadingHTTPServer):
    """HTTP server carrying the single project service used by all requests."""

    def __init__(
        self,
        address: tuple[str, int],
        service: ProjectService,
        tasks: TaskManager,
    ) -> None:
        self.service = service
        self.tasks = tasks
        super().__init__(address, ControlRequestHandler)
        self.daemon_threads = True


class ControlRequestHandler(BaseHTTPRequestHandler):
    server_version = "AI-Engine-Control"
    sys_version = ""

    @property
    def control_server(self) -> ControlHTTPServer:
        return cast(ControlHTTPServer, self.server)

    def _send_bytes(
        self,
        status: HTTPStatus,
        content_type: str,
        body: bytes,
        *,
        download_name: str | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if download_name is not None:
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{download_name}"',
            )
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; connect-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: HTTPStatus, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self._send_bytes(status, "application/json; charset=utf-8", body)

    def _send_video_file(self, path: Path, download_name: str) -> None:
        size = path.stat().st_size
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", str(size))
        self.send_header("Content-Disposition", f'attachment; filename="{download_name}"')
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; connect-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'",
        )
        self.end_headers()
        with path.open("rb") as video_file:
            while chunk := video_file.read(1024 * 1024):
                self.wfile.write(chunk)

    def _send_error_json(
        self,
        status: HTTPStatus,
        message: str,
        field: str | None = None,
    ) -> None:
        payload: dict[str, str] = {"error": message}
        if field is not None:
            payload["field"] = field
        self._send_json(status, payload)

    def _valid_host(self) -> bool:
        expected_host = (
            f"{self.control_server.server_address[0]}:"
            f"{self.control_server.server_address[1]}"
        )
        return self.headers.get("Host", "").lower() == expected_host.lower()

    def _read_json(self) -> object:
        content_type = self.headers.get_content_type()
        if content_type != "application/json":
            raise ValueError("Content-Type must be application/json.")
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise ValueError("Content-Length is required.")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValueError("Content-Length must be an integer.") from exc
        if not 1 <= length <= MAX_REQUEST_BYTES:
            raise ValueError(f"Request body must be between 1 and {MAX_REQUEST_BYTES} bytes.")
        raw = self.rfile.read(length)
        if len(raw) != length:
            raise ValueError("Request body ended unexpectedly.")
        try:
            return json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_non_finite_number,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"Invalid JSON request: {exc}") from exc

    def do_GET(self) -> None:
        if not self._valid_host():
            self._send_error_json(HTTPStatus.BAD_REQUEST, "Unexpected Host header.")
            return

        path = urlsplit(self.path).path
        if path == "/":
            self._send_asset("index.html", "text/html; charset=utf-8")
            return
        if path in ASSETS:
            asset_name, content_type = ASSETS[path]
            self._send_asset(asset_name, content_type)
            return
        if path == "/api/projects":
            self._list_projects()
            return
        if path.startswith("/api/projects/") and path.endswith("/tasks"):
            project_id = unquote(path[len("/api/projects/") : -len("/tasks")].rstrip("/"))
            self._list_tasks(project_id)
            return
        if path.startswith("/api/tasks/") and path.endswith("/video"):
            task_id = unquote(path[len("/api/tasks/") : -len("/video")].rstrip("/"))
            self._download_task_video(task_id)
            return
        if path.startswith("/api/tasks/"):
            task_id = unquote(path.removeprefix("/api/tasks/"))
            self._get_task(task_id)
            return
        if path.startswith("/api/projects/"):
            project_id = unquote(path.removeprefix("/api/projects/"))
            self._load_project(project_id)
            return
        self._send_error_json(HTTPStatus.NOT_FOUND, "Page not found.")

    def do_POST(self) -> None:
        if not self._valid_host():
            self._send_error_json(HTTPStatus.BAD_REQUEST, "Unexpected Host header.")
            return
        try:
            payload = self._read_json()
        except ValueError as exc:
            self._send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return

        path = urlsplit(self.path).path
        if path == "/api/projects/new":
            self._new_project(payload)
        elif path == "/api/projects":
            self._save_project(payload)
        elif path.startswith("/api/projects/") and path.endswith("/tasks"):
            project_id = unquote(path[len("/api/projects/") : -len("/tasks")].rstrip("/"))
            self._start_task(project_id, payload)
        else:
            self._send_error_json(HTTPStatus.NOT_FOUND, "Page not found.")

    def _send_asset(self, filename: str, content_type: str) -> None:
        path = Path(__file__).with_name("web") / filename
        try:
            body = path.read_bytes()
        except OSError as exc:
            self._send_error_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Cannot read UI asset {filename}: {exc}",
            )
            return
        self._send_bytes(HTTPStatus.OK, content_type, body)

    def _list_projects(self) -> None:
        try:
            projects = self.control_server.service.list_projects()
        except ProjectStoreError as exc:
            self._send_error_json(HTTPStatus.UNPROCESSABLE_ENTITY, str(exc))
            return
        self._send_json(HTTPStatus.OK, {"projects": projects})

    def _load_project(self, project_id: str) -> None:
        try:
            project = self.control_server.service.load_project(project_id)
        except ProjectValidationError as exc:
            self._send_error_json(
                HTTPStatus.BAD_REQUEST,
                str(exc),
                validation_field(exc),
            )
            return
        except ProjectStoreError as exc:
            status = (
                HTTPStatus.NOT_FOUND
                if _project_not_found(exc)
                else HTTPStatus.UNPROCESSABLE_ENTITY
            )
            self._send_error_json(status, str(exc))
            return
        self._send_json(HTTPStatus.OK, {"project": project})

    def _new_project(self, payload: object) -> None:
        if not isinstance(payload, dict):
            self._send_error_json(HTTPStatus.BAD_REQUEST, "Request must be a JSON object.")
            return
        try:
            name = payload["name"]
            if not isinstance(name, str):
                raise ProjectValidationError("name: must be text")
            project = self.control_server.service.new_project(name)
        except KeyError:
            self._send_error_json(HTTPStatus.BAD_REQUEST, "name: is required.", "name")
            return
        except ProjectValidationError as exc:
            self._send_error_json(
                HTTPStatus.BAD_REQUEST,
                str(exc),
                validation_field(exc),
            )
            return
        self._send_json(HTTPStatus.CREATED, {"project": project})

    def _save_project(self, payload: object) -> None:
        if not isinstance(payload, dict):
            self._send_error_json(HTTPStatus.BAD_REQUEST, "Request must be a JSON object.")
            return
        try:
            project = self.control_server.service.save_project(
                cast(dict[str, object], payload)
            )
        except ProjectValidationError as exc:
            self._send_error_json(
                HTTPStatus.BAD_REQUEST,
                str(exc),
                validation_field(exc),
            )
            return
        except ProjectStoreError as exc:
            self._send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        self._send_json(HTTPStatus.OK, {"project": project})

    def _list_tasks(self, project_id: str) -> None:
        try:
            tasks = self.control_server.tasks.list_for_project(project_id)
        except ProjectValidationError as exc:
            self._send_error_json(HTTPStatus.BAD_REQUEST, str(exc), validation_field(exc))
            return
        except ProjectStoreError as exc:
            status = (
                HTTPStatus.NOT_FOUND
                if _project_not_found(exc)
                else HTTPStatus.UNPROCESSABLE_ENTITY
            )
            self._send_error_json(status, str(exc))
            return
        except TaskStoreError as exc:
            self._send_error_json(HTTPStatus.UNPROCESSABLE_ENTITY, str(exc))
            return
        self._send_json(HTTPStatus.OK, {"tasks": [_public_task(task) for task in tasks]})

    def _get_task(self, task_id: str) -> None:
        try:
            task = self.control_server.tasks.get_task(task_id)
        except TaskStoreError as exc:
            status = (
                HTTPStatus.NOT_FOUND
                if str(exc).startswith("Task not found:")
                else HTTPStatus.BAD_REQUEST
            )
            self._send_error_json(status, str(exc))
            return
        self._send_json(HTTPStatus.OK, {"task": _public_task(task)})

    def _download_task_video(self, task_id: str) -> None:
        try:
            task = self.control_server.tasks.get_task(task_id)
        except TaskStoreError as exc:
            status = (
                HTTPStatus.NOT_FOUND
                if str(exc).startswith("Task not found:")
                else HTTPStatus.BAD_REQUEST
            )
            self._send_error_json(status, str(exc))
            return
        result = task.get("result")
        if task.get("status") != "succeeded" or not isinstance(result, dict):
            self._send_error_json(HTTPStatus.CONFLICT, "Task has no verified video output.")
            return
        if result.get("task_id") != task_id or result.get("project_id") != task.get("project_id"):
            self._send_error_json(HTTPStatus.CONFLICT, "Video output identity does not match its task.")
            return
        video_path = Path(str(result.get("video_file", "")))
        task_root = Path(task["work_directory"])
        artifact_root = task_root / "downloaded-artifacts"
        try:
            if video_path.name != f"{task['project_id']}.mp4":
                raise ValueError("Unexpected video filename.")
            if not artifact_root.is_dir() or artifact_root.is_symlink():
                raise ValueError("Task video artifact directory is unavailable.")
            relative = video_path.relative_to(artifact_root)
            current = artifact_root
            if current.is_symlink():
                raise ValueError("Task video artifact directory is a symbolic link.")
            for part in relative.parts:
                current = current / part
                if current.is_symlink():
                    raise ValueError("Task video path contains a symbolic link.")
            resolved = video_path.resolve(strict=True)
            resolved.relative_to(artifact_root.resolve(strict=True))
            if not resolved.is_file() or resolved.stat().st_size != result.get("video_size_bytes"):
                raise ValueError("Task video file is missing or has an unexpected size.")
            digest_builder = hashlib.sha256()
            with resolved.open("rb") as video_file:
                for chunk in iter(lambda: video_file.read(1024 * 1024), b""):
                    digest_builder.update(chunk)
            digest = digest_builder.hexdigest()
            if digest != result.get("video_sha256"):
                raise ValueError("Task video checksum does not match its verified result.")
            self._send_video_file(resolved, f"{task['project_id']}.mp4")
        except (OSError, ValueError):
            self._send_error_json(HTTPStatus.NOT_FOUND, "Verified task video is unavailable.")

    def _start_task(self, project_id: str, payload: object) -> None:
        if payload != {}:
            self._send_error_json(
                HTTPStatus.BAD_REQUEST,
                "Starting a production task requires an empty JSON object; settings come from the saved project.",
            )
            return
        try:
            task = self.control_server.tasks.create_task(project_id)
        except ProjectValidationError as exc:
            self._send_error_json(HTTPStatus.BAD_REQUEST, str(exc), validation_field(exc))
            return
        except ProjectStoreError as exc:
            status = (
                HTTPStatus.NOT_FOUND
                if _project_not_found(exc)
                else HTTPStatus.UNPROCESSABLE_ENTITY
            )
            self._send_error_json(status, str(exc))
            return
        except TaskStoreError as exc:
            self._send_error_json(HTTPStatus.CONFLICT, str(exc))
            return
        self._send_json(HTTPStatus.ACCEPTED, {"task": _public_task(task)})

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[control-ui] {self.address_string()} {format % args}")


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key '{key}'")
        result[key] = value
    return result


def _reject_non_finite_number(value: str) -> None:
    raise ValueError(f"non-finite number {value} is not allowed")


def _public_task(task: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in task.items() if key != "work_directory"}


def _project_not_found(error: ProjectStoreError) -> bool:
    return str(error).startswith(
        ("Project not found:", "Project storage directory does not exist:")
    )


def create_server(
    projects_directory: str | Path | None = None,
    port: int = 8765,
    task_executor: TaskExecutor | None = None,
) -> ControlHTTPServer:
    store_path = (
        default_projects_directory(REPOSITORY_ROOT)
        if projects_directory is None
        else Path(projects_directory)
    )
    store = ProjectStore(store_path)
    service = ProjectService(store)
    task_store = TaskStore(store.root.parent / ".ai-engine-task-state" / "tasks.sqlite3")
    tasks = TaskManager(store, task_store, task_executor)
    return ControlHTTPServer(("127.0.0.1", port), service, tasks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local AI-Engine project control UI.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--projects-dir",
        type=Path,
        default=default_projects_directory(REPOSITORY_ROOT),
    )
    arguments = parser.parse_args()
    if not 1 <= arguments.port <= 65535:
        parser.error("--port must be between 1 and 65535.")

    server = create_server(arguments.projects_dir, arguments.port)
    print(f"AI-Engine control UI: http://127.0.0.1:{server.server_address[1]}/")
    print(f"Project storage: {server.service.store.root}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping control UI.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
