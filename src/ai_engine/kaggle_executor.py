"""Prepare, submit, monitor, and validate bounded Kaggle Blender jobs."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
import zipfile
from json import JSONDecoder
from pathlib import Path
from typing import Any

from .project_store import validate_project
from .video_artifacts import VideoArtifactError, validate_video_evidence

KERNEL_SLUG = "haroonbaaraabumanar/ai-engine-blender-runtime-preflight"
KERNEL_TIMEOUT_SECONDS = 300
JOB_TIMEOUT_SECONDS = 900
POLL_INTERVAL_SECONDS = 10
_BUNDLE_ASSIGNMENT = re.compile(r'(?m)^BUNDLE_B64 = "[A-Za-z0-9+/=]*"$')
_VERSION_PATTERN = re.compile(r"Kernel version (\d+) successfully pushed")
_STATUS_PATTERN = re.compile(r"KernelWorkerStatus\.([A-Z_]+)", re.IGNORECASE)
_REDACT_PATTERNS = (
    (re.compile(r"(?i)(token|password|secret|api[_-]?key)\s*[:=]\s*\S+"), r"\1=[REDACTED]"),
    (re.compile(r"\bKGAT_[A-Za-z0-9_-]+\b"), "[REDACTED]"),
)


class KaggleExecutionError(RuntimeError):
    """Raised with an explicit, user-safe reason when a Kaggle operation fails."""


def _safe_error(text: str) -> str:
    value = text.strip()[-3000:]
    for pattern, replacement in _REDACT_PATTERNS:
        value = pattern.sub(replacement, value)
    return value or "Kaggle CLI returned no diagnostic output."


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_json_objects(text: str) -> list[dict[str, Any]]:
    decoder = JSONDecoder()
    objects: list[dict[str, Any]] = []
    index = 0
    while index < len(text):
        start = text.find("{", index)
        if start < 0:
            break
        try:
            value, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            index = start + 1
            continue
        if isinstance(value, dict):
            objects.append(value)
        index = end
    return objects


class KaggleExecutor:
    """Use the installed Kaggle CLI and the previously verified test notebook."""

    def __init__(self, repository_root: Path, *, job_timeout_seconds: int = JOB_TIMEOUT_SECONDS) -> None:
        if job_timeout_seconds < 1:
            raise ValueError("job_timeout_seconds must be positive.")
        self.repository_root = repository_root.resolve()
        self.job_timeout_seconds = job_timeout_seconds
        self.template_directory = (
            self.repository_root
            / "kaggle-blender-short-test"
            / "scene-integration-kernel-template"
        )
        self.kaggle_cli: Path | None = None

    @staticmethod
    def _find_cli() -> Path:
        executable = shutil.which("kaggle")
        if executable:
            return Path(executable)
        candidate = Path(sys.executable).resolve().parent / (
            "kaggle.exe" if sys.platform == "win32" else "kaggle"
        )
        if candidate.is_file():
            return candidate
        raise KaggleExecutionError(
            "Kaggle CLI is unavailable. Install/configure it in this project environment "
            "and retry; no remote task was submitted."
        )

    def prepare(self, task: dict[str, Any], project: dict[str, Any]) -> dict[str, str]:
        project = validate_project(project)
        if task["project_id"] != project["id"]:
            raise KaggleExecutionError("Task project ID does not match the saved project.")
        if project["audio"]["enabled"]:
            raise KaggleExecutionError(
                "Audio is required by this project, but audio rendering is not implemented; "
                "no Kaggle task was submitted."
            )
        notebook_template = self.template_directory / "ai-engine-satisfying-physics-short.ipynb"
        metadata_template = self.template_directory / "kernel-metadata.json"
        restorer = self.repository_root / "kaggle-blender-short-test" / "short_test_runner.py"
        runner = self.repository_root / "kaggle-blender-short-test" / "run_scene_integration_kaggle.py"
        required_sources = [
            self.repository_root / "src" / "ai_engine" / "__init__.py",
            self.repository_root / "src" / "ai_engine" / "project_store.py",
            self.repository_root / "src" / "ai_engine" / "scene_adapter.py",
            self.repository_root / "src" / "ai_engine" / "scene_generation.py",
            self.repository_root / "src" / "ai_engine" / "scene_integration.py",
            self.repository_root / "src" / "ai_engine" / "blender_scene_builder.py",
            self.repository_root
            / "src"
            / "ai_engine"
            / "blender_scene_integration_verifier.py",
            self.repository_root / "src" / "ai_engine" / "video_artifacts.py",
        ]
        required = [notebook_template, metadata_template, restorer, runner, *required_sources]
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise KaggleExecutionError(
                "Cannot prepare the Kaggle job because required files are missing: "
                + ", ".join(missing)
            )
        metadata = json.loads(metadata_template.read_text(encoding="utf-8"))
        if (
            metadata.get("id") != KERNEL_SLUG
            or metadata.get("enable_gpu") is not False
            or metadata.get("enable_tpu") is not False
        ):
            raise KaggleExecutionError(
                "The approved test kernel metadata is not the expected CPU-only kernel."
            )

        work_directory = Path(task["work_directory"])
        upload_directory = work_directory / "upload"
        upload_directory.mkdir(parents=True, exist_ok=False)
        bundle_path = upload_directory / "ai_engine_blender_task_bundle.zip"
        sources: list[tuple[Path, str]] = [
            (restorer, "short_test_runner.py"),
            (runner, "run_scene_integration_kaggle.py"),
            *[
                (path, str(Path("src") / "ai_engine" / path.name))
                for path in required_sources
            ],
        ]
        with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as bundle:
            for path, archive_name in sources:
                bundle.write(path, archive_name)
            bundle.writestr(
                "project.json",
                json.dumps(project, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            )
            bundle.writestr(
                "job-context.json",
                json.dumps(
                    {"task_id": task["id"], "project_id": project["id"]},
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
            )
        submitted_project_path = work_directory / "submitted-project.json"
        submitted_project_path.write_text(
            json.dumps(project, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        with zipfile.ZipFile(bundle_path) as bundle:
            if bundle.testzip() is not None:
                raise KaggleExecutionError("Prepared Kaggle source bundle failed CRC validation.")
            members = set(bundle.namelist())
            if (
                "project.json" not in members
                or "job-context.json" not in members
                or any("kaggle.json" in name.lower() for name in members)
            ):
                raise KaggleExecutionError("Prepared Kaggle source bundle failed safety checks.")

        notebook = json.loads(notebook_template.read_text(encoding="utf-8"))
        if (
            not isinstance(notebook.get("cells"), list)
            or len(notebook["cells"]) != 2
            or notebook["cells"][1].get("cell_type") != "code"
        ):
            raise KaggleExecutionError("The verified Kaggle test notebook has an unexpected layout.")
        cell = "".join(notebook["cells"][1]["source"])
        assignment = f'BUNDLE_B64 = "{base64.b64encode(bundle_path.read_bytes()).decode("ascii")}"'
        cell, replacements = _BUNDLE_ASSIGNMENT.subn(lambda _: assignment, cell, count=1)
        if replacements != 1:
            raise KaggleExecutionError("Cannot replace the test notebook's source-bundle payload.")
        compile(cell, "kaggle-task-notebook-cell", "exec")
        notebook["cells"][1]["source"] = cell.splitlines(keepends=True)
        notebook_path = upload_directory / str(metadata["code_file"])
        notebook_path.write_text(
            json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        (upload_directory / "kernel-metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return {
            "work_directory": str(work_directory),
            "upload_directory": str(upload_directory),
            "bundle_file": str(bundle_path),
            "notebook_file": str(notebook_path),
            "project_file": str(submitted_project_path),
        }

    def submit(self, prepared: dict[str, str]) -> str:
        output = self._run_cli(
            [
                "kernels",
                "push",
                "--path",
                prepared["upload_directory"],
                "--timeout",
                str(KERNEL_TIMEOUT_SECONDS),
            ],
            timeout=120,
        )
        match = _VERSION_PATTERN.search(output)
        if match is None:
            raise KaggleExecutionError(
                "Kaggle accepted no identifiable kernel version. "
                + _safe_error(output)
            )
        return match.group(1)

    def wait(self, task: dict[str, Any], prepared: dict[str, str]) -> dict[str, Any]:
        run_id = task.get("run_id")
        if not isinstance(run_id, str) or not run_id.isdigit():
            raise KaggleExecutionError("Kaggle task has no valid remote kernel version ID.")
        slug_version = f"{KERNEL_SLUG}/{run_id}"
        deadline = time.monotonic() + self.job_timeout_seconds
        remote_status: str | None = None
        while True:
            output = self._run_cli(
                ["kernels", "status", slug_version],
                timeout=30,
            )
            status_match = _STATUS_PATTERN.search(output)
            status = status_match.group(1).upper() if status_match is not None else None
            if status in {"COMPLETE", "CANCEL_ACKNOWLEDGED"}:
                remote_status = status
                break
            if status in {"ERROR", "FAILED"}:
                detail = _safe_error(output)
                try:
                    raw_failure_logs = self._run_cli(
                        ["kernels", "logs", slug_version],
                        timeout=120,
                    )
                    failure_logs_path = (
                        Path(prepared["work_directory"])
                        / f"kaggle-kernel-{run_id}-failed-logs.json"
                    )
                    failure_logs_path.write_text(raw_failure_logs + "\n", encoding="utf-8")
                    failure_rows = json.loads(raw_failure_logs)
                    if isinstance(failure_rows, list):
                        failure_lines = [
                            line
                            for row in failure_rows
                            if isinstance(row, dict)
                            and row.get("stream_name") == "stderr"
                            for line in str(row.get("data", "")).splitlines()
                            if re.search(
                                r"\b(traceback|error|exception|failed|failure)\b",
                                line,
                                re.IGNORECASE,
                            )
                        ]
                        if failure_lines:
                            diagnostics = _safe_error("\n".join(failure_lines[-12:]))
                            detail += f"; execution diagnostics: {diagnostics}"
                        else:
                            detail += f"; full remote execution logs saved at {failure_logs_path}"
                except (KaggleExecutionError, OSError, json.JSONDecodeError) as exc:
                    detail += f"; logs unavailable: {_safe_error(str(exc))}"
                raise KaggleExecutionError(
                    f"Kaggle kernel version {run_id} ended unsuccessfully: {detail}"
                )
            if time.monotonic() >= deadline:
                raise KaggleExecutionError(
                    f"Kaggle kernel version {run_id} did not finish within "
                    f"{self.job_timeout_seconds} seconds."
                )
            time.sleep(POLL_INTERVAL_SECONDS)

        raw_logs = self._run_cli(
            ["kernels", "logs", slug_version],
            timeout=120,
        )
        try:
            rows = json.loads(raw_logs)
        except json.JSONDecodeError as exc:
            raise KaggleExecutionError(
                "Kaggle returned logs in an unreadable format; task results were not accepted."
            ) from exc
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise KaggleExecutionError("Kaggle logs did not match the expected JSON event format.")
        stdout = "".join(
            str(row.get("data", ""))
            for row in rows
            if row.get("stream_name") == "stdout"
        )
        if remote_status is None:
            raise KaggleExecutionError(
                f"Kaggle kernel version {run_id} reached an unknown terminal state."
            )
        logs_path = Path(prepared["work_directory"]) / f"kaggle-kernel-{run_id}-logs.json"
        logs_path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return {
            "rows": rows,
            "stdout": stdout,
            "run_id": run_id,
            "remote_status": remote_status,
        }

    def validate(
        self,
        task: dict[str, Any],
        prepared: dict[str, str],
        execution: dict[str, Any],
    ) -> dict[str, Any]:
        stdout = execution["stdout"]
        reports = [
            value
            for value in _extract_json_objects(stdout)
            if value.get("schema_version") == 1 and value.get("task_id") == task["id"]
        ]
        if not reports:
            raise KaggleExecutionError(
                "Kaggle completed without a verifiable report for this task ID."
            )
        report = reports[-1]
        if (
            report.get("status") != "PASSED"
            or report.get("project_id") != task["project_id"]
            or report.get("kaggle_kernel_slug") != KERNEL_SLUG
            or report.get("kaggle_kernel_version") != execution.get("run_id")
            or report.get("errors") != []
        ):
            errors = report.get("errors")
            details = "; ".join(str(item) for item in errors) if isinstance(errors, list) else ""
            raise KaggleExecutionError(
                "Kaggle report did not pass task/project validation."
                + (f" {details}" if details else "")
            )
        scene = report.get("scene_integration")
        if not isinstance(scene, dict):
            raise KaggleExecutionError("Kaggle report is missing scene integration evidence.")
        verification = scene.get("verification")
        if not isinstance(verification, dict):
            raise KaggleExecutionError("Kaggle report is missing Blender verification results.")
        checks = verification.get("checks")
        expected_checks = {
            "blender_version",
            "blend_reopened",
            "eevee_settings",
            "rigid_body_objects",
            "target_static_before_contact",
            "launcher_reached_contact",
            "target_moved_after_contact",
        }
        if (
            scene.get("status") != "PASSED"
            or scene.get("project_id") != task["project_id"]
            or scene.get("blender_version") != "4.0.2"
            or scene.get("verification_process_exit_code") != 0
            or not isinstance(checks, dict)
            or not expected_checks.issubset(checks)
            or not all(checks.get(name) is True for name in expected_checks)
            or not isinstance(scene.get("blend_file"), str)
            or not isinstance(scene.get("blend_size_bytes"), int)
            or scene.get("blend_size_bytes", 0) <= 0
            or not isinstance(scene.get("blend_sha256"), str)
            or len(scene.get("blend_sha256", "")) != 64
        ):
            raise KaggleExecutionError(
                "Blender did not pass every required .blend reopen and physics verification check."
            )
        measurements = verification.get("measurements")
        if not isinstance(measurements, dict):
            raise KaggleExecutionError(
                "Blender report has no measurable post-contact target motion."
            )
        motion = measurements.get("target_motion_toward_chain_m")
        if isinstance(motion, bool) or not isinstance(motion, (int, float)) or motion <= 0.01:
            raise KaggleExecutionError("Blender report has no measurable post-contact target motion.")
        try:
            project = json.loads(Path(prepared["project_file"]).read_text(encoding="utf-8"))
            video = validate_video_evidence(
                report.get("video"),
                project,
                task["id"],
                execution["run_id"],
            )
        except (
            KeyError,
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValueError,
            TypeError,
            VideoArtifactError,
        ) as exc:
            raise KaggleExecutionError(f"Kaggle video validation failed: {exc}") from exc

        work_directory = Path(prepared["work_directory"])
        downloaded = self._download_verified_outputs(
            task,
            prepared,
            execution,
            scene,
            video,
        )
        logs_path = work_directory / f"kaggle-kernel-{execution['run_id']}-logs.json"
        report_path = work_directory / "integration-report.json"
        video_report_path = downloaded["video_report_file"]
        logs_path.write_text(
            json.dumps(execution["rows"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        video_report_path.write_text(
            json.dumps(video, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        wrapper_reports = [
            value
            for value in _extract_json_objects(stdout)
            if value.get("status") == "PASSED"
            and value.get("embedded_bundle_sha256") is not None
        ]
        if not wrapper_reports:
            raise KaggleExecutionError("Kaggle wrapper did not confirm the submitted bundle.")
        return {
            "report_file": str(report_path),
            "logs_file": str(logs_path),
            "remote_blend_file": scene["blend_file"],
            "remote_video_file": video["video_file"],
            "blend_file": str(downloaded["blend_file"]),
            "blend_sha256": scene["blend_sha256"],
            "blend_size_bytes": scene["blend_size_bytes"],
            "video_file": str(downloaded["video_file"]),
            "video_sha256": video["sha256"],
            "video_size_bytes": video["size_bytes"],
            "video_report_file": str(video_report_path),
            "audio_status": video["audio"]["status"],
            "task_id": task["id"],
            "project_id": task["project_id"],
            "blender_version": scene["blender_version"],
            "remote_status": execution.get("remote_status", "unknown"),
            "measurements": measurements,
            "checks": {name: checks[name] for name in sorted(expected_checks)},
            "wrapper": wrapper_reports[-1],
        }

    def _download_verified_outputs(
        self,
        task: dict[str, Any],
        prepared: dict[str, str],
        execution: dict[str, Any],
        scene: dict[str, Any],
        video: dict[str, Any],
    ) -> dict[str, Path]:
        run_id = execution.get("run_id")
        if not isinstance(run_id, str) or not run_id.isdigit():
            raise KaggleExecutionError("Cannot retrieve artifacts without a valid Kaggle run ID.")
        project_id = task["project_id"]
        output_directory = Path(prepared["work_directory"]) / "downloaded-artifacts"
        if output_directory.is_symlink():
            raise KaggleExecutionError("Task artifact directory must not be a symbolic link.")
        output_directory.mkdir(parents=True, exist_ok=True)
        if not output_directory.is_dir():
            raise KaggleExecutionError("Task artifact destination is not a directory.")
        pattern = rf"(^|/)({re.escape(project_id)}\.(blend|mp4)|video-report\.json)$"
        self._run_cli(
            [
                "kernels",
                "output",
                f"{KERNEL_SLUG}/{run_id}",
                "--path",
                str(output_directory),
                "--force",
                "--file-pattern",
                pattern,
            ],
            timeout=600,
        )
        blend_files = [path for path in output_directory.rglob(f"{project_id}.blend") if path.is_file() and not path.is_symlink()]
        video_files = [path for path in output_directory.rglob(f"{project_id}.mp4") if path.is_file() and not path.is_symlink()]
        report_files = [path for path in output_directory.rglob("video-report.json") if path.is_file() and not path.is_symlink()]
        if len(blend_files) != 1 or len(video_files) != 1 or len(report_files) != 1:
            raise KaggleExecutionError(
                "Kaggle output retrieval did not return exactly one .blend, MP4, and video report."
            )
        local_video = video_files[0]
        local_blend = blend_files[0]
        if (
            local_blend.stat().st_size != scene["blend_size_bytes"]
            or _sha256_file(local_blend) != scene["blend_sha256"]
        ):
            raise KaggleExecutionError("Downloaded .blend size or SHA-256 does not match remote verification.")
        if (
            local_video.stat().st_size != video["size_bytes"]
            or _sha256_file(local_video) != video["sha256"]
        ):
            raise KaggleExecutionError("Downloaded MP4 size or SHA-256 does not match remote verification.")
        try:
            downloaded_report = json.loads(report_files[0].read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise KaggleExecutionError(f"Downloaded video report is unreadable: {exc}") from exc
        if downloaded_report != video:
            raise KaggleExecutionError("Downloaded video report differs from task-validated evidence.")
        return {
            "blend_file": local_blend,
            "video_file": local_video,
            "video_report_file": report_files[0],
        }

    def _run_cli(self, arguments: list[str], *, timeout: int) -> str:
        if self.kaggle_cli is None:
            self.kaggle_cli = self._find_cli()
        command = [str(self.kaggle_cli), *arguments]
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError as exc:
            raise KaggleExecutionError(
                "Kaggle CLI could not be started. No task result was assumed."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise KaggleExecutionError(
                f"Kaggle CLI command exceeded its {timeout}-second timeout."
            ) from exc
        except OSError as exc:
            raise KaggleExecutionError(
                f"Kaggle CLI could not complete the requested operation: {_safe_error(str(exc))}"
            ) from exc
        output = result.stdout + "\n" + result.stderr
        if result.returncode != 0:
            raise KaggleExecutionError(
                f"Kaggle CLI command failed ({result.returncode}): {_safe_error(output)}"
            )
        return output.strip()
