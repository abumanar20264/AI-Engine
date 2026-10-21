"""Run a bounded Blender reopen and rigid-body motion integration check."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .project_store import ProjectStore
from .scene_generation import SavedProjectSceneGenerator, SceneGenerationError

_REQUIRED_CHECKS = {
    "blender_version",
    "blend_reopened",
    "eevee_settings",
    "rigid_body_objects",
    "target_static_before_contact",
    "launcher_reached_contact",
    "target_moved_after_contact",
}


def validate_verification_report(
    report: object,
    project_id: str,
    blend_file: Path,
) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise ValueError("Blender verification report must be a JSON object.")
    checks = report.get("checks")
    if (
        report.get("schema_version") != 1
        or report.get("status") != "PASSED"
        or report.get("project_id") != project_id
        or Path(str(report.get("blend_file", ""))).resolve() != blend_file.resolve()
        or report.get("blender_version") != "4.0.2"
        or not isinstance(checks, dict)
        or not _REQUIRED_CHECKS.issubset(checks)
        or not all(checks.get(name) is True for name in _REQUIRED_CHECKS)
        or not isinstance(report.get("measurements"), dict)
        or not isinstance(report.get("errors"), list)
        or report["errors"]
    ):
        raise ValueError(
            "Blender verification report failed schema, identity, or required check validation."
        )
    return report


def run_saved_project_scene_integration(
    store: ProjectStore,
    blender_executable: str | Path,
    project_id: str,
    timeout_seconds: int = 600,
) -> dict[str, Any]:
    generator = SavedProjectSceneGenerator(
        store,
        blender_executable,
        timeout_seconds=timeout_seconds,
    )
    plan = generator.plan_saved_project(project_id)
    project_id = plan.project_id
    blend_file = generator._resolve_output(project_id, None)
    build_report_file = blend_file.with_suffix(".scene-report.json")
    verification_report_file = blend_file.with_suffix(".verification-report.json")
    integration_report_file = blend_file.with_suffix(".integration-report.json")
    if any(
        path.exists() or path.is_symlink()
        for path in (verification_report_file, integration_report_file)
    ):
        raise SceneGenerationError(
            "Refusing to overwrite existing integration evidence for this project."
        )

    report: dict[str, Any] = {
        "schema_version": 1,
        "status": "FAILED",
        "project_id": project_id,
        "blender_version": None,
        "blend_file": str(blend_file),
        "scene_report_file": str(build_report_file),
        "verification_report_file": str(verification_report_file),
        "verification_process_exit_code": None,
        "checks": {
            "scene_generation": False,
            "blend_reopened": False,
            "physics_verified": False,
        },
        "errors": [],
    }
    try:
        result = generator.generate(project_id)
        report["blender_version"] = result.blender_version
        report["checks"]["scene_generation"] = result.blend_file.is_file()
        verifier_script = Path(__file__).with_name(
            "blender_scene_integration_verifier.py"
        )
        command = [
            str(blender_executable),
            "--background",
            "--threads",
            "1",
            str(result.blend_file),
            "--python-exit-code",
            "1",
            "--python",
            str(verifier_script),
            "--",
            "--blend-file",
            str(result.blend_file),
            "--scene-report",
            str(result.report_file),
            "--report",
            str(verification_report_file),
        ]
        verification_result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        report["verification_process_exit_code"] = verification_result.returncode
        if verification_result.returncode != 0:
            report["errors"].append(
                "Blender reopen/physics verification failed: "
                + _output_tail(verification_result)
            )
        elif not verification_report_file.is_file():
            report["errors"].append(
                "Blender verification process exited successfully without a report."
            )
        else:
            try:
                verification = json.loads(
                    verification_report_file.read_text(encoding="utf-8")
                )
                validate_verification_report(
                    verification,
                    project_id,
                    result.blend_file,
                )
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                report["errors"].append(f"Invalid Blender verification evidence: {exc}")
            else:
                report["verification"] = verification
                report["checks"]["blend_reopened"] = verification["checks"][
                    "blend_reopened"
                ]
                report["checks"]["physics_verified"] = (
                    verification["checks"]["launcher_reached_contact"]
                    and verification["checks"]["target_moved_after_contact"]
                )
        if not report["errors"] and all(report["checks"].values()):
            report["status"] = "PASSED"
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")

    report["integration_report_file"] = str(integration_report_file)
    integration_report_file.parent.mkdir(parents=True, exist_ok=True)
    integration_report_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return report


def _output_tail(result: subprocess.CompletedProcess[str]) -> str:
    output = (result.stdout + "\n" + result.stderr).strip()
    return output[-4000:] if output else f"process exited with code {result.returncode}"
