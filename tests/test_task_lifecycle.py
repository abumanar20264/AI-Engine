from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ai_engine.kaggle_executor import KERNEL_SLUG, KaggleExecutionError, KaggleExecutor
from ai_engine.project_store import ProjectStore, create_project
from ai_engine.task_manager import TaskManager
from ai_engine.task_store import TaskStore, TaskStoreError
from ai_engine.video_artifacts import VideoArtifactError, validate_video_evidence


class FakeExecutor:
    def __init__(
        self,
        failure_at: str | None = None,
        remote_status: str = "COMPLETE",
    ) -> None:
        self.failure_at = failure_at
        self.remote_status = remote_status
        self.submitted = threading.Event()
        self.release_wait = threading.Event()
        self.project_seen_after_restart: dict[str, Any] | None = None

    def prepare(self, task: dict[str, Any], project: dict[str, Any]) -> dict[str, str]:
        if self.failure_at == "prepare":
            raise KaggleExecutionError("Kaggle CLI is unavailable.")
        if project["id"] != task["project_id"]:
            raise AssertionError("Executor was given the wrong project.")
        return {
            "work_directory": task["work_directory"],
            "upload_directory": str(Path(task["work_directory"]) / "upload"),
        }

    def submit(self, prepared: dict[str, str]) -> str:
        if self.failure_at == "submit":
            raise KaggleExecutionError("Kaggle submission permission denied.")
        self.submitted.set()
        return "14"

    def wait(self, task: dict[str, Any], prepared: dict[str, str]) -> dict[str, Any]:
        project_file_value = prepared.get("project_file")
        project_file = Path(project_file_value) if project_file_value else None
        if project_file is not None and project_file.is_file():
            self.project_seen_after_restart = json.loads(project_file.read_text(encoding="utf-8"))
        self.release_wait.wait(timeout=5)
        if self.failure_at == "wait":
            raise KaggleExecutionError("Kaggle kernel ended with ERROR.")
        return {
            "run_id": task["run_id"],
            "stdout": "verified",
            "remote_status": self.remote_status,
        }

    def validate(
        self,
        task: dict[str, Any],
        prepared: dict[str, str],
        execution: dict[str, Any],
    ) -> dict[str, Any]:
        if self.failure_at == "validate":
            raise KaggleExecutionError("Blender report did not pass verification.")
        return {
            "task_id": task["id"],
            "project_id": task["project_id"],
            "remote_blend_file": "/kaggle/working/test.blend",
            "remote_video_file": "/kaggle/working/test.mp4",
            "blend_file": str(Path(task["work_directory"]) / "downloaded-artifacts" / "test.blend"),
            "blend_sha256": "b" * 64,
            "blend_size_bytes": 100,
            "video_file": str(Path(task["work_directory"]) / "downloaded-artifacts" / "test.mp4"),
            "video_sha256": "a" * 64,
            "video_size_bytes": 100,
            "video_report_file": str(Path(task["work_directory"]) / "video-report.json"),
            "audio_status": "NOT_AVAILABLE",
            "report_file": str(Path(task["work_directory"]) / "integration-report.json"),
            "logs_file": str(Path(task["work_directory"]) / "logs.json"),
            "blender_version": "4.0.2",
            "remote_status": execution["remote_status"],
        }


def _passed_report(
    task_id: str,
    project_id: str,
    kernel_version: str,
) -> dict[str, Any]:
    checks = {
        "blender_version": True,
        "blend_reopened": True,
        "eevee_settings": True,
        "rigid_body_objects": True,
        "target_static_before_contact": True,
        "launcher_reached_contact": True,
        "target_moved_after_contact": True,
    }
    return {
        "schema_version": 1,
        "task_id": task_id,
        "project_id": project_id,
        "kaggle_kernel_slug": KERNEL_SLUG,
        "kaggle_kernel_version": kernel_version,
        "status": "PASSED",
        "errors": [],
        "scene_integration": {
            "status": "PASSED",
            "project_id": project_id,
            "blender_version": "4.0.2",
            "verification_process_exit_code": 0,
            "blend_file": "/kaggle/working/task.blend",
            "blend_size_bytes": len(b"verified blend bytes"),
            "blend_sha256": hashlib.sha256(b"verified blend bytes").hexdigest(),
            "verification": {
                "checks": checks,
                "measurements": {"target_motion_toward_chain_m": 0.5},
            },
        },
        "video": {
            "schema_version": 1,
            "status": "PASSED",
            "task_id": task_id,
            "project_id": project_id,
            "kaggle_kernel_slug": KERNEL_SLUG,
            "kaggle_kernel_version": kernel_version,
            "video_file": f"/kaggle/working/task/{project_id}.mp4",
            "size_bytes": 1200,
            "sha256": "a" * 64,
            "metadata": {
                "codec": "h264",
                "width": 720,
                "height": 1280,
                "fps": 24,
                "frame_count": 120,
                "duration_seconds": 5.0,
            },
            "checks": {
                "h264_codec": True,
                "resolution_matches_project": True,
                "frame_rate_matches_project": True,
                "frame_count_matches_project": True,
                "duration_matches_project": True,
                "full_decode": True,
                "visible_motion": True,
            },
            "audio": {"status": "NOT_AVAILABLE"},
        },
    }


class TaskLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix=".test-task-lifecycle-", dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project_store = ProjectStore(self.root / "projects")
        self.project = self.project_store.save(create_project("Tracked scene task"))
        self.task_store = TaskStore(self.root / "task-state" / "tasks.sqlite3")

    def mock_output_retrieval(
        self,
        task: dict[str, Any],
        prepared: dict[str, str],
        report: dict[str, Any],
    ) -> Any:
        project_file = Path(task["work_directory"]) / "submitted-project.json"
        project_file.write_text(json.dumps(self.project), encoding="utf-8")
        prepared["project_file"] = str(project_file)
        video_data = b"verified mp4 bytes"
        blend_data = b"verified blend bytes"
        report["video"]["size_bytes"] = len(video_data)
        report["video"]["sha256"] = hashlib.sha256(video_data).hexdigest()

        def retrieve(arguments: list[str], *, timeout: int) -> str:
            output_path = Path(arguments[arguments.index("--path") + 1])
            (output_path / f"{task['project_id']}.blend").write_bytes(blend_data)
            (output_path / f"{task['project_id']}.mp4").write_bytes(video_data)
            (output_path / "video-report.json").write_text(
                json.dumps(report["video"]), encoding="utf-8"
            )
            return "downloaded"

        return retrieve

    def test_video_evidence_requires_matching_task_project_and_all_checks(self) -> None:
        task_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        evidence = {
            "schema_version": 1,
            "status": "PASSED",
            "task_id": task_id,
            "project_id": self.project["id"],
            "kaggle_kernel_slug": KERNEL_SLUG,
            "kaggle_kernel_version": "44",
            "video_file": f"/kaggle/working/task/{self.project['id']}.mp4",
            "size_bytes": 1200,
            "sha256": "a" * 64,
            "metadata": {
                "codec": "h264",
                "width": 720,
                "height": 1280,
                "fps": 24,
                "frame_count": 120,
                "duration_seconds": 5.0,
            },
            "checks": {
                "h264_codec": True,
                "resolution_matches_project": True,
                "frame_rate_matches_project": True,
                "frame_count_matches_project": True,
                "duration_matches_project": True,
                "full_decode": True,
                "visible_motion": True,
            },
            "audio": {"status": "NOT_AVAILABLE"},
        }
        self.assertEqual(
            validate_video_evidence(evidence, self.project, task_id, "44")["sha256"],
            "a" * 64,
        )
        with self.assertRaisesRegex(VideoArtifactError, "identity or acceptance"):
            validate_video_evidence(
                {**evidence, "task_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"},
                self.project,
                task_id,
                "44",
            )
        failed_checks = {**evidence, "checks": {**evidence["checks"], "full_decode": False}}
        with self.assertRaisesRegex(VideoArtifactError, "identity or acceptance"):
            validate_video_evidence(failed_checks, self.project, task_id, "44")
        task = self.task_store.create(self.project["id"], self.root / "runs")
        self.task_store.transition(task["id"], "preparing", "Preparing.")
        self.task_store.transition(task["id"], "running", "Running.", run_id="14")
        self.task_store.transition(task["id"], "validating", "Validating.")
        with self.assertRaisesRegex(TaskStoreError, "verified video results"):
            self.task_store.transition(task["id"], "succeeded", "No video evidence.")

    def test_mp4_verifier_checks_project_metadata_decode_motion_and_hash(self) -> None:
        video_file = self.root / f"{self.project['id']}.mp4"
        video_file.write_bytes(b"encoded video")
        probe = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 720,
                    "height": 1280,
                    "avg_frame_rate": "24/1",
                    "nb_frames": "120",
                    "duration": "5.0",
                }
            ],
            "format": {"duration": "5.0", "size": str(video_file.stat().st_size)},
        }
        frame_size = 64 * 64 * 3
        motion_frames = bytes(frame_size) + bytes([20]) * frame_size + bytes([40]) * frame_size
        responses = iter(
            [
                CompletedProcess([], 0, json.dumps(probe).encode(), b""),
                CompletedProcess([], 0, b"", b""),
                CompletedProcess([], 0, motion_frames, b""),
            ]
        )
        from ai_engine.video_artifacts import verify_video_artifact

        with patch("ai_engine.video_artifacts._run", side_effect=lambda *_args: next(responses)):
            evidence = verify_video_artifact(
                video_file,
                self.project,
                "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                ffmpeg="ffmpeg",
                ffprobe="ffprobe",
            )
        self.assertEqual(evidence["status"], "PASSED")
        self.assertTrue(evidence["checks"]["full_decode"])
        self.assertTrue(evidence["checks"]["visible_motion"])
        self.assertEqual(evidence["size_bytes"], video_file.stat().st_size)
        self.assertEqual(evidence["audio"]["status"], "NOT_AVAILABLE")

    def wait_for(self, task_id: str, status: str) -> dict[str, Any]:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            task = self.task_store.get(task_id)
            if task["status"] == status:
                return task
            time.sleep(0.01)
        self.fail(f"Task did not reach {status}; current status: {self.task_store.get(task_id)['status']}")

    def test_transition_graph_rejects_skips_and_terminal_mutation(self) -> None:
        task = self.task_store.create(
            self.project["id"],
            self.root / "runs",
        )
        with self.assertRaisesRegex(TaskStoreError, "Invalid task transition"):
            self.task_store.transition(task["id"], "running", "Skip preparation")
        with self.assertRaisesRegex(TaskStoreError, "explicit error"):
            self.task_store.transition(task["id"], "failed", "No cause")
        failed = self.task_store.transition(
            task["id"],
            "failed",
            "Preparation failed.",
            error="Kaggle CLI unavailable.",
        )
        self.assertEqual(failed["status"], "failed")
        self.assertIsNotNone(failed["completed_at"])
        with self.assertRaisesRegex(TaskStoreError, "Invalid task transition"):
            self.task_store.transition(task["id"], "preparing", "Cannot restart terminal task")

    def test_task_and_event_history_survive_store_reopen(self) -> None:
        task = self.task_store.create(self.project["id"], self.root / "runs")
        self.task_store.transition(task["id"], "preparing", "Preparing transfer.")
        self.task_store.transition(
            task["id"],
            "running",
            "Submitted.",
            run_id="14",
        )
        reopened = TaskStore(self.task_store.database).get(task["id"])
        self.assertEqual(reopened["status"], "running")
        self.assertEqual(reopened["project_id"], self.project["id"])
        self.assertEqual(reopened["run_id"], "14")
        self.assertIsNotNone(reopened["started_at"])
        self.assertEqual(
            [event["to_status"] for event in reopened["events"]],
            ["queued", "preparing", "running"],
        )

    def test_recovered_running_task_uses_immutable_submitted_project(self) -> None:
        task = self.task_store.create(self.project["id"], self.root / "runs")
        task_directory = Path(task["work_directory"])
        snapshot = task_directory / "project-snapshot.json"
        submitted = task_directory / "submitted-project.json"
        snapshot.write_text(json.dumps(self.project), encoding="utf-8")
        submitted.write_text(json.dumps(self.project), encoding="utf-8")
        self.task_store.transition(task["id"], "preparing", "Preparing.")
        self.task_store.transition(task["id"], "running", "Submitted.", run_id="14")
        changed_project = {**self.project, "name": "Edited after submission"}
        self.project_store.save(changed_project)

        executor = FakeExecutor()
        executor.release_wait.set()
        manager = TaskManager(self.project_store, self.task_store, executor)
        recovered = self.wait_for_manager(manager, task["id"], "succeeded")
        self.assertEqual(recovered["result"]["project_id"], self.project["id"])
        self.assertIsNotNone(executor.project_seen_after_restart)
        self.assertEqual(executor.project_seen_after_restart["name"], self.project["name"])

    def test_manager_tracks_success_only_after_result_validation(self) -> None:
        executor = FakeExecutor(remote_status="CANCEL_ACKNOWLEDGED")
        manager = TaskManager(
            self.project_store,
            self.task_store,
            executor,
        )
        task = manager.create_task(self.project["id"])
        self.assertTrue(executor.submitted.wait(timeout=2))
        running = self.wait_for(task["id"], "running")
        self.assertEqual(running["run_id"], "14")
        self.assertIsNone(running["completed_at"])
        executor.release_wait.set()
        completed = self.wait_for_manager(manager, task["id"], "succeeded")
        self.assertEqual(completed["result"]["blender_version"], "4.0.2")
        self.assertEqual(completed["result"]["remote_status"], "CANCEL_ACKNOWLEDGED")
        self.assertIn("acknowledged cancellation", completed["events"][-1]["message"])
        self.assertEqual(
            [event["to_status"] for event in completed["events"]],
            ["queued", "preparing", "running", "validating", "succeeded"],
        )
        self.assertIsNotNone(completed["completed_at"])

    def test_manager_persists_submission_and_validation_failures(self) -> None:
        executor = FakeExecutor(failure_at="submit")
        manager = TaskManager(self.project_store, self.task_store, executor)
        failed = manager.create_task(self.project["id"])
        result = self.wait_for_manager(manager, failed["id"], "failed")
        self.assertIn("permission denied", result["error"])
        self.assertEqual(
            [event["to_status"] for event in result["events"]],
            ["queued", "preparing", "failed"],
        )

        second_store = TaskStore(self.root / "second-state" / "tasks.sqlite3")
        second_executor = FakeExecutor(failure_at="validate")
        second_manager = TaskManager(self.project_store, second_store, second_executor)
        second = second_manager.create_task(self.project["id"])
        self.assertTrue(second_executor.submitted.wait(timeout=2))
        second_executor.release_wait.set()
        second_result = self.wait_for_manager(
            second_manager,
            second["id"],
            "failed",
        )
        self.assertEqual(second_result["events"][-2]["to_status"], "validating")
        self.assertIn("did not pass verification", second_result["error"])
        self.assertEqual(second_result["result"], {})

    def test_only_one_nonterminal_task_can_be_started(self) -> None:
        executor = FakeExecutor()
        manager = TaskManager(self.project_store, self.task_store, executor)
        first = manager.create_task(self.project["id"])
        self.assertTrue(executor.submitted.wait(timeout=2))
        self.wait_for(first["id"], "running")
        with self.assertRaisesRegex(TaskStoreError, "already running"):
            manager.create_task(self.project["id"])
        executor.release_wait.set()
        self.wait_for_manager(manager, first["id"], "succeeded")

    def test_kaggle_preparation_transfers_the_saved_project_and_cpu_only_metadata(self) -> None:
        task = self.task_store.create(self.project["id"], self.root / "runs")
        executor = KaggleExecutor(ROOT)
        prepared = executor.prepare(task, self.project)
        with zipfile.ZipFile(prepared["bundle_file"]) as bundle:
            payload = json.loads(bundle.read("project.json"))
            context = json.loads(bundle.read("job-context.json"))
            self.assertEqual(payload, self.project)
            self.assertEqual(context, {"task_id": task["id"], "project_id": self.project["id"]})
            self.assertIn("src/ai_engine/video_artifacts.py", bundle.namelist())
            self.assertNotIn("main", {
                item.filename for item in bundle.infolist()
                if item.filename == "production-main.py"
            })
            self.assertFalse(any("kaggle.json" in name.lower() for name in bundle.namelist()))
        notebook = json.loads(Path(prepared["notebook_file"]).read_text(encoding="utf-8"))
        self.assertEqual(notebook["metadata"]["kaggle"]["accelerator"], "none")
        self.assertIs(notebook["metadata"]["kaggle"]["isGpuEnabled"], False)
        self.assertNotIn("render", "".join(notebook["cells"][1]["source"]).lower())
        embedded = re.search(
            r'^BUNDLE_B64 = "([A-Za-z0-9+/=]+)"$',
            "".join(notebook["cells"][1]["source"]),
            re.MULTILINE,
        )
        self.assertIsNotNone(embedded)
        if embedded is None:
            self.fail("Prepared notebook did not contain its embedded source bundle.")
        decoded = base64.b64decode(embedded.group(1), validate=True)
        self.assertEqual(decoded, Path(prepared["bundle_file"]).read_bytes())

        audio_project = {
            **self.project,
            "audio": {"enabled": True, "source": "licensed-audio.wav", "volume": 1.0},
        }
        audio_project = self.project_store.save(audio_project)
        audio_task = self.task_store.create(audio_project["id"], self.root / "audio-runs")
        with self.assertRaisesRegex(KaggleExecutionError, "audio rendering is not implemented"):
            executor.prepare(audio_task, audio_project)

    def test_kaggle_cli_submission_status_and_logs_use_supported_commands(self) -> None:
        executor = KaggleExecutor(ROOT, job_timeout_seconds=10)
        executor.kaggle_cli = Path("kaggle.exe")
        logs = json.dumps(
            [
                {"stream_name": "stdout", "data": "{\"status\": \"PASSED\"}\n"},
                {"stream_name": "stderr", "data": ""},
            ]
        )

        def run(command: list[str], **kwargs: object) -> CompletedProcess[str]:
            if "push" in command:
                return CompletedProcess(
                    command,
                    0,
                    "Kernel version 27 successfully pushed.",
                    "",
                )
            if "status" in command:
                self.assertEqual(command[-1], f"{KERNEL_SLUG}/27")
                return CompletedProcess(command, 0, "KernelWorkerStatus.COMPLETE", "")
            self.assertIn("logs", command)
            self.assertEqual(command[-1], f"{KERNEL_SLUG}/27")
            return CompletedProcess(command, 0, logs, "")

        with patch("ai_engine.kaggle_executor.subprocess.run", side_effect=run) as mocked:
            version = executor.submit({"upload_directory": str(self.root)})
            execution = executor.wait(
                {"run_id": version},
                {"work_directory": str(self.root)},
            )
        self.assertEqual(version, "27")
        self.assertEqual(mocked.call_count, 3)
        self.assertIn("status", execution["stdout"])
        self.assertEqual(execution["run_id"], "27")
        self.assertEqual(execution["remote_status"], "COMPLETE")

    def test_cancel_request_waits_until_terminal_status(self) -> None:
        executor = KaggleExecutor(ROOT, job_timeout_seconds=10)
        executor.kaggle_cli = Path("kaggle.exe")
        status_outputs = iter(
            [
                "KernelWorkerStatus.CANCEL_REQUESTED",
                "KernelWorkerStatus.COMPLETE",
            ]
        )
        logs = json.dumps([{"stream_name": "stdout", "data": "complete"}])

        def run(command: list[str], **_kwargs: object) -> CompletedProcess[str]:
            if "status" in command:
                return CompletedProcess(command, 0, next(status_outputs), "")
            return CompletedProcess(command, 0, logs, "")

        with (
            patch("ai_engine.kaggle_executor.subprocess.run", side_effect=run) as mocked,
            patch("ai_engine.kaggle_executor.time.sleep"),
        ):
            execution = executor.wait(
                {"run_id": "30"},
                {"work_directory": str(self.root)},
            )
        self.assertEqual(execution["remote_status"], "COMPLETE")
        self.assertEqual(mocked.call_count, 3)
        self.assertTrue((self.root / "kaggle-kernel-30-logs.json").is_file())

    def test_cancel_acknowledged_logs_still_require_task_specific_blender_validation(self) -> None:
        task = self.task_store.create(self.project["id"], self.root / "runs")
        report = _passed_report(task["id"], self.project["id"], "31")
        prepared = {"work_directory": task["work_directory"]}
        retrieve = self.mock_output_retrieval(task, prepared, report)
        wrapper = {
            "status": "PASSED",
            "embedded_bundle_sha256": "known-bundle-hash",
        }
        stdout = json.dumps(report) + "\n" + json.dumps(wrapper) + "\n"
        raw_logs = json.dumps([{"stream_name": "stdout", "data": stdout}])
        executor = KaggleExecutor(ROOT, job_timeout_seconds=1)
        executor.kaggle_cli = Path("kaggle.exe")

        def run(command: list[str], **_kwargs: object) -> CompletedProcess[str]:
            if "status" in command:
                return CompletedProcess(
                    command,
                    0,
                    "KernelWorkerStatus.CANCEL_ACKNOWLEDGED",
                    "",
                )
            return CompletedProcess(command, 0, raw_logs, "")

        task_with_run = {**task, "run_id": "31"}
        with (
            patch("ai_engine.kaggle_executor.subprocess.run", side_effect=run),
            patch("ai_engine.kaggle_executor.time.sleep"),
        ):
            execution = executor.wait(task_with_run, prepared)
        self.assertEqual(execution["remote_status"], "CANCEL_ACKNOWLEDGED")
        with patch.object(executor, "_run_cli", side_effect=retrieve):
            result = executor.validate(task, prepared, execution)
        self.assertEqual(result["remote_status"], "CANCEL_ACKNOWLEDGED")
        self.assertEqual(result["blender_version"], "4.0.2")
        self.assertTrue(Path(result["video_file"]).is_file())

    def test_kaggle_failure_includes_and_persists_remote_execution_logs(self) -> None:
        executor = KaggleExecutor(ROOT)
        executor.kaggle_cli = Path("kaggle.exe")
        run_directory = self.root / "failed-run"
        run_directory.mkdir()
        logs = json.dumps(
            [{"stream_name": "stderr", "data": "Traceback: scene builder failed"}]
        )

        def run(command: list[str], **_kwargs: object) -> CompletedProcess[str]:
            if "status" in command:
                return CompletedProcess(
                    command,
                    0,
                    "KernelWorkerStatus.ERROR",
                    "",
                )
            self.assertIn("logs", command)
            return CompletedProcess(command, 0, logs, "")

        with patch("ai_engine.kaggle_executor.subprocess.run", side_effect=run):
            with self.assertRaisesRegex(
                KaggleExecutionError,
                "scene builder failed",
            ):
                executor.wait(
                    {"run_id": "28"},
                    {"work_directory": str(run_directory)},
                )
        failure_logs = run_directory / "kaggle-kernel-28-failed-logs.json"
        self.assertEqual(json.loads(failure_logs.read_text(encoding="utf-8")), json.loads(logs))

    def test_kaggle_error_message_points_to_logs_without_dumping_success_output(self) -> None:
        executor = KaggleExecutor(ROOT)
        executor.kaggle_cli = Path("kaggle.exe")
        run_directory = self.root / "cancelled-run"
        run_directory.mkdir()
        logs = json.dumps(
            [
                {
                    "stream_name": "stdout",
                    "data": json.dumps(
                        {
                            "status": "PASSED",
                            "embedded_bundle_sha256": "bundle-hash",
                            "large_report": "report-data" * 500,
                        }
                    ),
                },
                {"stream_name": "stderr", "data": "Runtime completed with warnings only."},
            ]
        )

        def run(command: list[str], **_kwargs: object) -> CompletedProcess[str]:
            if "status" in command:
                return CompletedProcess(
                    command,
                    0,
                    "KernelWorkerStatus.ERROR",
                    "",
                )
            self.assertIn("logs", command)
            return CompletedProcess(command, 0, logs, "")

        with patch("ai_engine.kaggle_executor.subprocess.run", side_effect=run):
            with self.assertRaises(KaggleExecutionError) as raised:
                executor.wait(
                    {"run_id": "29"},
                    {"work_directory": str(run_directory)},
                )
        self.assertIn("KernelWorkerStatus.ERROR", str(raised.exception))
        self.assertIn("full remote execution logs saved at", str(raised.exception))
        self.assertNotIn("embedded_bundle_sha256", str(raised.exception))
        self.assertLess(len(str(raised.exception)), 400)

    def test_success_result_requires_matching_project_and_real_blender_checks(self) -> None:
        task = self.task_store.create(self.project["id"], self.root / "runs")
        self.task_store.transition(task["id"], "preparing", "Preparing.")
        self.task_store.transition(task["id"], "running", "Running.", run_id="14")
        task = self.task_store.transition(task["id"], "validating", "Validating.")
        report = _passed_report(task["id"], self.project["id"], "14")
        prepared = {"work_directory": task["work_directory"]}
        retrieve = self.mock_output_retrieval(task, prepared, report)
        wrapper = {
            "status": "PASSED",
            "embedded_bundle_sha256": "known-bundle-hash",
        }
        stdout = json.dumps(report) + "\n" + json.dumps(wrapper) + "\n"
        execution = {
            "run_id": "14",
            "stdout": stdout,
            "rows": [{"stream_name": "stdout", "data": stdout}],
        }
        executor = KaggleExecutor(ROOT)
        with patch.object(executor, "_run_cli", side_effect=retrieve):
            result = executor.validate(task, prepared, execution)
        self.assertEqual(result["blender_version"], "4.0.2")
        self.assertEqual(result["project_id"], self.project["id"])
        self.assertEqual(result["audio_status"], "NOT_AVAILABLE")
        self.assertTrue(Path(result["video_report_file"]).is_file())
        self.assertTrue(Path(result["report_file"]).is_file())
        self.assertTrue(Path(result["logs_file"]).is_file())

        wrong_kernel_report = {**report, "kaggle_kernel_version": "13"}
        wrong_kernel_stdout = json.dumps(wrong_kernel_report) + "\n" + json.dumps(wrapper) + "\n"
        with self.assertRaisesRegex(KaggleExecutionError, "report did not pass"):
            executor.validate(
                task,
                prepared,
                {
                    **execution,
                    "stdout": wrong_kernel_stdout,
                    "rows": [{"stream_name": "stdout", "data": wrong_kernel_stdout}],
                },
            )

        report["scene_integration"]["verification"]["checks"][
            "target_moved_after_contact"
        ] = False
        failed_stdout = json.dumps(report) + "\n" + json.dumps(wrapper) + "\n"
        failed_execution = {
            "run_id": "14",
            "stdout": failed_stdout,
            "rows": [{"stream_name": "stdout", "data": failed_stdout}],
        }
        with self.assertRaisesRegex(KaggleExecutionError, "every required"):
            executor.validate(
                task,
                prepared,
                failed_execution,
            )

    @staticmethod
    def _wait_for_store(
        store: TaskStore,
        task_id: str,
        status: str,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            task = store.get(task_id)
            if task["status"] == status:
                return task
            time.sleep(0.01)
        raise AssertionError(f"Task did not reach {status}: {store.get(task_id)['status']}")

    def wait_for_manager(
        self,
        manager: TaskManager,
        task_id: str,
        status: str,
    ) -> dict[str, Any]:
        task = self._wait_for_store(manager.task_store, task_id, status)
        worker = manager._threads.get(task_id)
        if worker is not None:
            worker.join(timeout=2)
            if worker.is_alive():
                self.fail(f"Task worker did not exit after reaching {status}.")
        return task


if __name__ == "__main__":
    unittest.main()
