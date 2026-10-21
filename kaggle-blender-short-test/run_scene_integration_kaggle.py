from __future__ import annotations

import ast
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, cast
from uuid import UUID, uuid4

from ai_engine.project_store import ProjectStore
from ai_engine.scene_integration import run_saved_project_scene_integration
from ai_engine.video_artifacts import verify_video_artifact

OUTPUT = Path("/kaggle/working/ai-engine-scene-integration")
PROJECT_FILE = Path(__file__).with_name("project.json")
JOB_CONTEXT_FILE = Path(__file__).with_name("job-context.json")
_RESTORE_CONSTANTS = {
    "KAGGLE_INPUT",
    "BLENDER_DATASET_REF",
    "BLENDER_ARCHIVE_NAME",
    "BLENDER_ARCHIVE_SHA256",
    "BUILD_MANIFEST_NAME",
    "BUILD_MANIFEST_SHA256",
    "BLENDER_TREE_NAME",
    "BLENDER_RUNTIME_ROOT",
    "BLENDER_TREE_ROOT",
}
_RESTORE_FUNCTIONS = {
    "sha256_file",
    "find_unique_input_file",
    "validate_archive_member",
    "inspect_blender_tree",
    "restore_blender_runtime",
}


def _load_verified_runtime_restorer(
    runner_path: Path,
) -> Callable[[], dict[str, Any]]:
    source = runner_path.read_text(encoding="utf-8")
    original = ast.parse(source, filename=str(runner_path))
    selected = []
    found_functions = set()
    found_constants = set()
    for node in original.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            selected.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in _RESTORE_FUNCTIONS:
            selected.append(node)
            found_functions.add(node.name)
        elif isinstance(node, ast.Assign):
            target_names = {
                target.id
                for target in node.targets
                if isinstance(target, ast.Name)
            }
            if target_names & _RESTORE_CONSTANTS:
                selected.append(node)
                found_constants.update(target_names & _RESTORE_CONSTANTS)
    missing_functions = _RESTORE_FUNCTIONS - found_functions
    missing_constants = _RESTORE_CONSTANTS - found_constants
    if missing_functions or missing_constants:
        raise RuntimeError(
            "Could not isolate the existing integrity-checked Blender restorer: "
            f"missing functions={sorted(missing_functions)}, "
            f"missing constants={sorted(missing_constants)}"
        )
    module = ast.Module(body=selected, type_ignores=[])
    namespace: dict[str, Any] = {"__name__": "_ai_engine_blender_restore"}
    exec(compile(module, str(runner_path), "exec"), namespace)
    return cast(Callable[[], dict[str, Any]], namespace["restore_blender_runtime"])


def main() -> int:
    if not PROJECT_FILE.is_file() or not JOB_CONTEXT_FILE.is_file():
        raise RuntimeError("The submitted job must include project.json and job-context.json.")
    project_document = json.loads(PROJECT_FILE.read_text(encoding="utf-8"))
    job_context = json.loads(JOB_CONTEXT_FILE.read_text(encoding="utf-8"))
    task_id = job_context.get("task_id")
    expected_project_id = job_context.get("project_id")
    if (
        not isinstance(task_id, str)
        or not isinstance(expected_project_id, str)
        or project_document.get("id") != expected_project_id
    ):
        raise RuntimeError("Submitted project identity does not match the job context.")
    try:
        if str(UUID(task_id)) != task_id:
            raise ValueError
    except ValueError as exc:
        raise RuntimeError("Submitted task ID is not a canonical UUID.") from exc
    task_output = OUTPUT / task_id
    task_output.mkdir(parents=True, exist_ok=False)
    run_id = str(uuid4())
    report_path = task_output / f"integration-report-{run_id}.json"
    report = {
        "schema_version": 1,
        "task_id": task_id,
        "project_id": expected_project_id,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "kaggle_kernel_slug": "haroonbaaraabumanar/ai-engine-blender-runtime-preflight",
        "kaggle_kernel_version": os.environ.get("KAGGLE_KERNEL_VERSION"),
        "platform": platform.platform(),
        "python_version": sys.version,
        "gpu_enabled_in_kernel_metadata": False,
        "tpu_enabled_in_kernel_metadata": False,
        "render_performed": False,
        "benchmark_performed": False,
        "status": "FAILED",
        "errors": [],
    }
    try:
        runner_path = Path(__file__).with_name("short_test_runner.py")
        restore_blender_runtime = _load_verified_runtime_restorer(runner_path)
        runtime = restore_blender_runtime()
        report["runtime_restore"] = runtime["report"]
        os.environ.update(runtime["environment"])
        store = ProjectStore(task_output / "project-store")
        saved_project = store.save(project_document)
        if saved_project["id"] != expected_project_id:
            raise RuntimeError("Saved project ID changed during Kaggle transfer.")
        report["saved_project_file"] = str(store.root / f"{saved_project['id']}.json")
        report["saved_project_id"] = saved_project["id"]
        scene_report = run_saved_project_scene_integration(
            store,
            runtime["blender"],
            saved_project["id"],
            timeout_seconds=240,
        )
        report["scene_integration"] = scene_report
        report["status"] = scene_report["status"]
        if report["status"] != "PASSED":
            report["errors"].extend(scene_report["errors"])
        else:
            if saved_project["audio"]["enabled"]:
                raise RuntimeError(
                    "Audio is required by this project, but audio rendering is not implemented."
                )
            blend_file = Path(scene_report["blend_file"])
            video_file = blend_file.with_suffix(".mp4")
            if video_file.exists() or video_file.is_symlink():
                raise RuntimeError("Refusing to overwrite an existing task video.")
            rendered = subprocess.run(
                [
                    runtime["blender"],
                    "--background",
                    "--threads",
                    "1",
                    str(blend_file),
                    "--render-anim",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=1800,
                env=os.environ.copy(),
            )
            video_candidates = [
                path
                for path in blend_file.parent.glob(f"{blend_file.stem}*.mp4")
                if path.is_file() and not path.is_symlink() and path.stat().st_size > 0
            ]
            if rendered.returncode != 0 or len(video_candidates) != 1:
                raise RuntimeError(
                    "Blender did not produce exactly one non-empty project MP4: "
                    + (rendered.stderr or rendered.stdout)[-4000:]
                )
            if video_candidates[0] != video_file:
                video_candidates[0].replace(video_file)
            report["render_performed"] = True
            video_report = verify_video_artifact(
                video_file,
                saved_project,
                task_id,
                ffmpeg=shutil.which("ffmpeg"),
                ffprobe=shutil.which("ffprobe"),
            )
            video_report["kaggle_kernel_slug"] = report["kaggle_kernel_slug"]
            video_report["kaggle_kernel_version"] = report["kaggle_kernel_version"]
            blend_digest = hashlib.sha256()
            with blend_file.open("rb") as blend_stream:
                for chunk in iter(lambda: blend_stream.read(1024 * 1024), b""):
                    blend_digest.update(chunk)
            scene_report["blend_size_bytes"] = blend_file.stat().st_size
            scene_report["blend_sha256"] = blend_digest.hexdigest()
            video_report_path = task_output / "video-report.json"
            video_report_path.write_text(
                json.dumps(video_report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                encoding="utf-8",
            )
            report["video"] = video_report
            report["video_report_file"] = str(video_report_path)
    except Exception as exc:
        report["status"] = "FAILED"
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        report["traceback"] = traceback.format_exc()
    report["completed_utc"] = datetime.now(timezone.utc).isoformat()
    report["report_file"] = str(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if report["status"] == "PASSED" else 1


if __name__ == "__main__":
    RESULT = main()
else:
    RESULT = None
