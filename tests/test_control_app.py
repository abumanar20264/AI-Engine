from __future__ import annotations

import json
import hashlib
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from typing import Any, cast
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ai_engine.control_app import create_server
from ai_engine.project_store import create_project


class ImmediateTaskExecutor:
    def prepare(self, task: dict[str, Any], project: dict[str, Any]) -> dict[str, str]:
        return {
            "work_directory": task["work_directory"],
            "upload_directory": str(Path(task["work_directory"]) / "upload"),
        }

    def submit(self, prepared: dict[str, str]) -> str:
        return "test-version"

    def wait(self, task: dict[str, Any], prepared: dict[str, str]) -> dict[str, Any]:
        return {"run_id": task["run_id"]}

    def validate(
        self,
        task: dict[str, Any],
        prepared: dict[str, str],
        execution: dict[str, Any],
    ) -> dict[str, Any]:
        video = Path(task["work_directory"]) / "downloaded-artifacts" / f"{task['project_id']}.mp4"
        video.parent.mkdir(parents=True, exist_ok=True)
        video_bytes = b"verified video"
        video.write_bytes(video_bytes)
        return {
            "task_id": task["id"],
            "project_id": task["project_id"],
            "remote_blend_file": "/kaggle/working/test.blend",
            "blend_file": str(video.with_suffix(".blend")),
            "blend_sha256": hashlib.sha256(b"verified blend").hexdigest(),
            "blend_size_bytes": len(b"verified blend"),
            "remote_video_file": "/kaggle/working/test.mp4",
            "video_file": str(video),
            "video_sha256": hashlib.sha256(video_bytes).hexdigest(),
            "video_size_bytes": len(video_bytes),
            "video_report_file": str(video.with_name("video-report.json")),
            "audio_status": "NOT_AVAILABLE",
            "report_file": str(video.with_name("integration-report.json")),
            "logs_file": str(video.with_name("logs.json")),
            "blender_version": "4.0.2",
            "remote_status": execution.get("remote_status", "unknown"),
        }


class ControlAppHTTPTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix=".test-control-app-",
            dir=ROOT,
        )
        self.addCleanup(self.temporary.cleanup)
        self.server = create_server(
            Path(self.temporary.name) / "projects",
            port=0,
            task_executor=ImmediateTaskExecutor(),
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._stop_server)
        host = str(self.server.server_address[0])
        port = int(self.server.server_address[1])
        self.base_url = f"http://{host}:{port}"

    def _stop_server(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def request_json(
        self,
        path: str,
        payload: object | None = None,
    ) -> tuple[int, dict[str, Any]]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=data,
            headers={"Content-Type": "application/json"} if data is not None else {},
        )
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as exc:
            response = exc
        with response:
            return cast(int, response.status), json.loads(response.read().decode("utf-8"))

    def test_ui_assets_and_empty_library_are_served(self) -> None:
        with urlopen(self.base_url + "/", timeout=5) as response:
            html = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("/assets/control.js", html)
            self.assertIn("MP4 rendering", html)
            self.assertIn("start-task", html)

        status, listing = self.request_json("/api/projects")
        self.assertEqual(status, 200)
        self.assertEqual(listing["projects"], [])

    def test_http_create_edit_save_list_and_load_round_trip(self) -> None:
        status, created = self.request_json(
            "/api/projects/new",
            {"name": "Browser project"},
        )
        self.assertEqual(status, 201)
        project = created["project"]
        self.assertEqual(project["scenario"]["video"]["eevee_samples"], 8)

        project["name"] = "Updated through UI API"
        project["scenario"]["objects"][0]["mass_kg"] = 2.5
        status, saved = self.request_json("/api/projects", project)
        self.assertEqual(status, 200)
        project_id = saved["project"]["id"]

        status, listing = self.request_json("/api/projects")
        self.assertEqual(status, 200)
        self.assertEqual(listing["projects"][0]["name"], "Updated through UI API")

        status, loaded = self.request_json(f"/api/projects/{project_id}")
        self.assertEqual(status, 200)
        self.assertEqual(loaded["project"], saved["project"])

    def test_validation_errors_include_field_path_and_do_not_write(self) -> None:
        project = create_project("Invalid edit")
        project["scenario"]["video"]["width"] = 1
        status, result = self.request_json("/api/projects", project)
        self.assertEqual(status, 400)
        self.assertEqual(result["field"], "scenario.video.width")
        self.assertIn("between 16 and 4320", result["error"])
        self.assertFalse((Path(self.temporary.name) / "projects").exists())

        project["scenario"]["video"]["width"] = 720
        project["scenario"]["objects"][0]["dimensions"][1] = 0
        status, result = self.request_json("/api/projects", project)
        self.assertEqual(status, 400)
        self.assertEqual(result["field"], "scenario.objects[0].dimensions")

    def test_corrupt_saved_project_returns_clear_error_without_server_failure(self) -> None:
        project_id = "9c36c2a5-55be-4d88-8b23-8cbdb683b297"
        projects = Path(self.temporary.name) / "projects"
        projects.mkdir()
        (projects / f"{project_id}.json").write_text("{broken", encoding="utf-8")

        status, result = self.request_json(f"/api/projects/{project_id}")
        self.assertEqual(status, 422)
        self.assertIn("Invalid project JSON", result["error"])

        status, health = self.request_json("/api/projects/new", {"name": "Still responsive"})
        self.assertEqual(status, 201)
        self.assertIn("project", health)

        status, listing = self.request_json("/api/projects")
        self.assertEqual(status, 422)
        self.assertIn("Invalid project JSON", listing["error"])

    def test_rejects_duplicate_json_keys_and_invalid_content_type(self) -> None:
        duplicate = Request(
            self.base_url + "/api/projects/new",
            data=b'{"name":"one","name":"two"}',
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(HTTPError) as duplicate_error:
            urlopen(duplicate, timeout=5)
        self.assertEqual(duplicate_error.exception.code, 400)

        wrong_type = Request(
            self.base_url + "/api/projects/new",
            data=b'{"name":"one"}',
            headers={"Content-Type": "text/plain"},
        )
        with self.assertRaises(HTTPError) as type_error:
            urlopen(wrong_type, timeout=5)
        self.assertEqual(type_error.exception.code, 400)

    def test_saved_project_task_is_started_and_status_history_is_retrievable(self) -> None:
        project = create_project("HTTP task project")
        status, saved = self.request_json("/api/projects", project)
        self.assertEqual(status, 200)
        project_id = saved["project"]["id"]

        status, started = self.request_json(f"/api/projects/{project_id}/tasks", {})
        self.assertEqual(status, 202)
        task_id = started["task"]["id"]
        self.assertEqual(started["task"]["project_id"], project_id)
        self.assertNotIn("work_directory", started["task"])

        current: dict[str, Any] | None = None
        end_time = time.monotonic() + 5
        while time.monotonic() < end_time:
            status, task_response = self.request_json(f"/api/tasks/{task_id}")
            current = task_response
            if current["task"]["status"] == "succeeded":
                break
            time.sleep(0.01)
        if current is None:
            self.fail("No task status response was received.")
        self.assertEqual(current["task"]["status"], "succeeded")
        self.assertEqual(current["task"]["result"]["remote_blend_file"], "/kaggle/working/test.blend")
        with urlopen(self.base_url + f"/api/tasks/{task_id}/video", timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers["Content-Type"], "video/mp4")
            self.assertIn("attachment", response.headers["Content-Disposition"])
            self.assertEqual(response.read(), b"verified video")
        Path(current["task"]["result"]["video_file"]).write_bytes(b"corrupted")
        status, download_error = self.request_json(f"/api/tasks/{task_id}/video")
        self.assertEqual(status, 404)
        self.assertIn("unavailable", download_error["error"])

        status, history = self.request_json(f"/api/projects/{project_id}/tasks")
        self.assertEqual(status, 200)
        self.assertEqual(history["tasks"][0]["id"], task_id)
        self.assertEqual(
            [event["to_status"] for event in history["tasks"][0]["events"]],
            ["queued", "preparing", "running", "validating", "succeeded"],
        )

    def test_starting_task_for_unsaved_project_reports_blocker(self) -> None:
        project_id = create_project("Unsaved task project")["id"]
        status, result = self.request_json(f"/api/projects/{project_id}/tasks", {})
        self.assertEqual(status, 404)
        self.assertIn("storage directory does not exist", result["error"])


if __name__ == "__main__":
    unittest.main()
