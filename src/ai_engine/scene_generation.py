"""Execute the Blender scene builder for projects already saved in ProjectStore."""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .project_store import ProjectStore, ProjectStoreError
from .scene_adapter import ScenePlan, project_to_scene_plan

_BLENDER_VERSION_PATTERN = re.compile(r"\bBlender\s+4\.0\.2\b")
_MAX_ERROR_OUTPUT = 4000


class SceneGenerationError(RuntimeError):
    """Raised when the requested saved project cannot be turned into a Blender file."""


@dataclass(frozen=True)
class SceneGenerationResult:
    project_id: str
    blend_file: Path
    report_file: Path
    blender_version: str
    scene_plan: ScenePlan


class SavedProjectSceneGenerator:
    """Load a project from the real store and run the Blender 4.0.2 builder."""

    def __init__(
        self,
        store: ProjectStore,
        blender_executable: str | Path,
        timeout_seconds: int = 600,
    ) -> None:
        if timeout_seconds < 1:
            raise ValueError("timeout_seconds must be positive.")
        self.store = store
        self.blender_executable = str(blender_executable)
        self.timeout_seconds = timeout_seconds

    def plan_saved_project(self, project_id: str) -> ScenePlan:
        try:
            project = self.store.load(project_id)
        except (ProjectStoreError, ValueError) as exc:
            raise SceneGenerationError(f"Cannot load saved project: {exc}") from exc
        return project_to_scene_plan(project)

    def generate(
        self,
        project_id: str,
        output_path: str | Path | None = None,
    ) -> SceneGenerationResult:
        try:
            project = self.store.load(project_id)
        except (ProjectStoreError, ValueError) as exc:
            raise SceneGenerationError(f"Cannot load saved project: {exc}") from exc
        plan = project_to_scene_plan(project)
        project_file = self.store.root / f"{plan.project_id}.json"
        blend_file = self._resolve_output(project_id, output_path)
        if blend_file.suffix.lower() != ".blend":
            raise SceneGenerationError("Scene output must use the .blend extension.")
        report_file = blend_file.with_suffix(".scene-report.json")
        if blend_file.exists() or blend_file.is_symlink():
            raise SceneGenerationError(f"Refusing to overwrite existing scene: {blend_file}")
        if report_file.exists() or report_file.is_symlink():
            raise SceneGenerationError(f"Refusing to overwrite existing report: {report_file}")
        version_result = self._run(
            [self.blender_executable, "--version"],
            operation="Blender version check",
            timeout=min(self.timeout_seconds, 30),
        )
        if version_result.returncode != 0:
            raise SceneGenerationError(
                f"Blender version check failed: {_output_tail(version_result)}"
            )
        version_text = version_result.stdout + version_result.stderr
        match = _BLENDER_VERSION_PATTERN.search(version_text)
        if match is None:
            raise SceneGenerationError(
                "Blender 4.0.2 is required; version check output did not confirm it."
            )

        blend_file.parent.mkdir(parents=True, exist_ok=True)
        builder_script = Path(__file__).with_name("blender_scene_builder.py")
        command = [
            self.blender_executable,
            "--background",
            "--factory-startup",
            "--threads",
            "1",
            "--python",
            str(builder_script),
            "--",
            "--project",
            str(project_file),
            "--output",
            str(blend_file),
            "--report",
            str(report_file),
        ]
        build_result = self._run(
            command,
            operation="Blender scene generation",
            timeout=self.timeout_seconds,
        )
        if build_result.returncode != 0:
            raise SceneGenerationError(
                "Blender scene generation failed: "
                f"{_output_tail(build_result)}"
            )
        if not blend_file.is_file() or blend_file.stat().st_size == 0:
            raise SceneGenerationError(
                "Blender exited successfully but did not create a non-empty .blend file."
            )
        if not report_file.is_file():
            raise SceneGenerationError(
                "Blender exited successfully but did not create a scene report."
            )
        try:
            report = json.loads(report_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SceneGenerationError(f"Blender scene report is invalid: {exc}") from exc
        if not isinstance(report, dict) or (
            report.get("status") != "SCENE_BUILT"
            or report.get("project_id") != plan.project_id
            or report.get("blender_version") != "4.0.2"
            or report.get("engine") != "BLENDER_EEVEE"
            or report.get("eevee_samples") != plan.eevee_samples
            or report.get("simulation_or_render_executed") is not False
            or report.get("device") is not None
        ):
            raise SceneGenerationError(
                "Blender scene report does not match the requested project and render settings."
            )
        return SceneGenerationResult(
            project_id=plan.project_id,
            blend_file=blend_file,
            report_file=report_file,
            blender_version="4.0.2",
            scene_plan=plan,
        )

    def _resolve_output(
        self,
        project_id: str,
        output_path: str | Path | None,
    ) -> Path:
        candidate = (
            self.store.root / "generated-scenes" / project_id / f"{project_id}.blend"
            if output_path is None
            else Path(output_path)
        )
        if not candidate.is_absolute():
            candidate = self.store.root / candidate
        lexical_path = Path(os.path.abspath(candidate))
        try:
            relative_path = lexical_path.relative_to(self.store.root)
        except ValueError as exc:
            raise SceneGenerationError(
                "Scene output must remain inside the configured project storage directory."
            ) from exc
        current = self.store.root
        for part in relative_path.parts[:-1]:
            current = current / part
            if current.is_symlink():
                raise SceneGenerationError(
                    f"Scene output directory must not contain a symbolic link: {current}"
                )
        if lexical_path.is_symlink():
            raise SceneGenerationError(
                f"Scene output must not be a symbolic link: {lexical_path}"
            )
        resolved = lexical_path.resolve()
        try:
            resolved.relative_to(self.store.root)
        except ValueError as exc:
            raise SceneGenerationError(
                "Resolved scene output escapes the configured project storage directory."
            ) from exc
        return resolved

    def _run(
        self,
        command: list[str],
        operation: str,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError as exc:
            raise SceneGenerationError(
                f"{operation} could not start: Blender executable was not found: "
                f"{self.blender_executable}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise SceneGenerationError(
                f"{operation} exceeded its {timeout}-second timeout."
            ) from exc
        except OSError as exc:
            raise SceneGenerationError(f"{operation} could not start: {exc}") from exc


def _output_tail(result: subprocess.CompletedProcess[str]) -> str:
    text = "\n".join(part for part in (result.stdout, result.stderr) if part)
    return text[-_MAX_ERROR_OUTPUT:] if text else "Blender produced no diagnostic output."


def scene_report_from_file(path: str | Path) -> dict[str, Any]:
    """Read a scene report for callers that need to inspect a generated artifact."""
    report_path = Path(path)
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SceneGenerationError(f"Cannot read scene report {report_path}: {exc}") from exc
    if not isinstance(report, dict):
        raise SceneGenerationError(f"Scene report {report_path} must contain a JSON object.")
    return report
