"""Versioned project/scenario documents and safe local JSON persistence."""

from __future__ import annotations

import json
import math
import os
import re
import stat
import tempfile
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn, cast
from uuid import UUID, uuid4

SCHEMA_VERSION = 1
MAX_PROJECT_FILE_BYTES = 1_000_000
_PROJECT_ID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")
_PROJECT_STATUSES = {"draft", "ready", "running", "completed", "failed"}
_TASK_STATUSES = {"not_started", "queued", "running", "succeeded", "failed"}
_SHAPES = {"sphere", "box", "cylinder"}
_SCENARIO_TYPES = {"rigid_body_chain"}
_SAMPLE_COUNTS = {1, 2, 4, 8, 16, 32, 64, 128, 256}


class ProjectValidationError(ValueError):
    """Raised when a project document violates the version 1 contract."""


class ProjectStoreError(RuntimeError):
    """Raised when a project cannot safely be persisted or retrieved."""


def _fail(path: str, message: str) -> NoReturn:
    raise ProjectValidationError(f"{path}: {message}")


def _mapping(
    value: object,
    path: str,
    required: set[str],
    optional: set[str] | None = None,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _fail(path, "must be an object")
    if any(not isinstance(key, str) for key in value):
        _fail(path, "object keys must be text")
    mapping = cast(Mapping[str, object], value)
    allowed = required | (optional or set())
    missing = required - mapping.keys()
    extra = mapping.keys() - allowed
    if missing:
        _fail(path, f"missing required field(s): {', '.join(sorted(missing))}")
    if extra:
        _fail(path, f"unknown field(s): {', '.join(sorted(extra))}")
    return mapping


def _text(value: object, path: str, maximum: int = 200) -> str:
    if not isinstance(value, str):
        _fail(path, "must be text")
    normalized = value.strip()
    if not normalized:
        _fail(path, "must not be empty")
    if len(normalized) > maximum:
        _fail(path, f"must be at most {maximum} characters")
    if any(ord(character) < 32 for character in normalized):
        _fail(path, "must not contain control characters")
    return normalized


def _number(
    value: object,
    path: str,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(path, "must be a number")
    number = float(value)
    if not math.isfinite(number):
        _fail(path, "must be finite")
    if minimum is not None and number < minimum:
        _fail(path, f"must be at least {minimum}")
    if maximum is not None and number > maximum:
        _fail(path, f"must be at most {maximum}")
    return number


def _integer(
    value: object,
    path: str,
    minimum: int,
    maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(path, "must be an integer")
    if not minimum <= value <= maximum:
        _fail(path, f"must be between {minimum} and {maximum}")
    return value


def _vector(
    value: object,
    path: str,
    minimum: float | None = None,
    maximum: float | None = None,
) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        _fail(path, "must contain exactly 3 numbers")
    return [
        _number(component, f"{path}[{index}]", minimum, maximum)
        for index, component in enumerate(value)
    ]


def _timestamp(value: object, path: str) -> str:
    text = _text(value, path, maximum=40)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        _fail(path, "must be an ISO-8601 timestamp with a timezone")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _fail(path, "must include a timezone")
    return text


def _optional_timestamp(value: object, path: str) -> str | None:
    return None if value is None else _timestamp(value, path)


def _identifier(value: object, path: str) -> str:
    text = _text(value, path, maximum=64)
    if not _IDENTIFIER_PATTERN.fullmatch(text):
        _fail(path, "must start with a letter or digit and contain only letters, digits, '_' or '-'")
    return text


def _validate_object(value: object, index: int) -> dict[str, object]:
    path = f"scenario.objects[{index}]"
    item = _mapping(
        value,
        path,
        {"id", "shape", "position", "dimensions", "mass_kg", "friction", "restitution"},
    )
    object_id = _identifier(item["id"], f"{path}.id")
    shape = _text(item["shape"], f"{path}.shape", maximum=20)
    if shape not in _SHAPES:
        _fail(f"{path}.shape", f"must be one of {', '.join(sorted(_SHAPES))}")
    return {
        "id": object_id,
        "shape": shape,
        "position": _vector(item["position"], f"{path}.position"),
        "dimensions": _vector(item["dimensions"], f"{path}.dimensions", minimum=0.001),
        "mass_kg": _number(item["mass_kg"], f"{path}.mass_kg", minimum=0.001, maximum=100_000),
        "friction": _number(item["friction"], f"{path}.friction", minimum=0, maximum=1),
        "restitution": _number(item["restitution"], f"{path}.restitution", minimum=0, maximum=1),
    }


def _validate_scenario(value: object) -> dict[str, object]:
    scenario = _mapping(
        value,
        "scenario",
        {"type", "objects", "gravity_m_s2", "camera", "video"},
    )
    scenario_type = _text(scenario["type"], "scenario.type", maximum=40)
    if scenario_type not in _SCENARIO_TYPES:
        _fail("scenario.type", f"unsupported scenario type '{scenario_type}'")

    raw_objects = scenario["objects"]
    if not isinstance(raw_objects, (list, tuple)):
        _fail("scenario.objects", "must be a list")
    if not 2 <= len(raw_objects) <= 64:
        _fail("scenario.objects", "must contain between 2 and 64 objects")
    objects = [_validate_object(item, index) for index, item in enumerate(raw_objects)]
    object_ids = [item["id"] for item in objects]
    if len(object_ids) != len(set(object_ids)):
        _fail("scenario.objects", "object IDs must be unique")

    camera = _mapping(
        scenario["camera"],
        "scenario.camera",
        {"position", "target", "lens_mm"},
    )
    video = _mapping(
        scenario["video"],
        "scenario.video",
        {"width", "height", "fps", "frame_count", "eevee_samples"},
    )
    sample_count = _integer(
        video["eevee_samples"], "scenario.video.eevee_samples", 1, 256
    )
    if sample_count not in _SAMPLE_COUNTS:
        _fail(
            "scenario.video.eevee_samples",
            "must be a supported power-of-two sample count from 1 to 256",
        )

    return {
        "type": scenario_type,
        "objects": objects,
        "gravity_m_s2": _vector(scenario["gravity_m_s2"], "scenario.gravity_m_s2"),
        "camera": {
            "position": _vector(camera["position"], "scenario.camera.position"),
            "target": _vector(camera["target"], "scenario.camera.target"),
            "lens_mm": _number(camera["lens_mm"], "scenario.camera.lens_mm", 10, 200),
        },
        "video": {
            "width": _integer(video["width"], "scenario.video.width", 16, 4320),
            "height": _integer(video["height"], "scenario.video.height", 16, 7680),
            "fps": _integer(video["fps"], "scenario.video.fps", 1, 120),
            "frame_count": _integer(video["frame_count"], "scenario.video.frame_count", 1, 3600),
            "eevee_samples": sample_count,
        },
    }


def _validate_audio(value: object) -> dict[str, object]:
    audio = _mapping(value, "audio", {"enabled", "source", "volume"})
    if not isinstance(audio["enabled"], bool):
        _fail("audio.enabled", "must be true or false")
    source = audio["source"]
    if source is not None:
        source = _text(source, "audio.source", maximum=2048)
    if audio["enabled"] and source is None:
        _fail("audio.source", "is required when audio is enabled")
    return {
        "enabled": audio["enabled"],
        "source": source,
        "volume": _number(audio["volume"], "audio.volume", 0, 2),
    }


def _validate_task(value: object) -> dict[str, object]:
    task = _mapping(
        value,
        "task",
        {"status", "error", "run_id", "started_at", "completed_at"},
    )
    status = _text(task["status"], "task.status", maximum=20)
    if status not in _TASK_STATUSES:
        _fail("task.status", f"must be one of {', '.join(sorted(_TASK_STATUSES))}")
    error = task["error"]
    if error is not None:
        error = _text(error, "task.error", maximum=4000)
    if status == "failed" and error is None:
        _fail("task.error", "is required when task status is failed")
    if status != "failed" and error is not None:
        _fail("task.error", "is only allowed when task status is failed")
    run_id = task["run_id"]
    if run_id is not None:
        run_id = _text(run_id, "task.run_id", maximum=200)
    return {
        "status": status,
        "error": error,
        "run_id": run_id,
        "started_at": _optional_timestamp(task["started_at"], "task.started_at"),
        "completed_at": _optional_timestamp(task["completed_at"], "task.completed_at"),
    }


def _validate_outputs(value: object) -> dict[str, str | None]:
    outputs = _mapping(value, "outputs", {"video", "report"})
    validated: dict[str, str | None] = {}
    for name in ("video", "report"):
        reference = outputs[name]
        validated[name] = (
            None if reference is None else _text(reference, f"outputs.{name}", maximum=2048)
        )
    return validated


def validate_project(value: object) -> dict[str, Any]:
    """Validate and normalize a version 1 project document."""
    project = _mapping(
        value,
        "project",
        {"schema_version", "id", "name", "created_at", "status", "scenario", "audio", "task", "outputs"},
    )
    version = project["schema_version"]
    if isinstance(version, bool) or not isinstance(version, int):
        _fail("schema_version", "must be an integer")
    if version != SCHEMA_VERSION:
        _fail("schema_version", f"unsupported version {version}; supported version is {SCHEMA_VERSION}")

    project_id = _text(project["id"], "id", maximum=36)
    if not _PROJECT_ID_PATTERN.fullmatch(project_id):
        _fail("id", "must be a canonical lowercase UUID")
    try:
        if str(UUID(project_id)) != project_id:
            _fail("id", "must be a canonical lowercase UUID")
    except ValueError:
        _fail("id", "must be a canonical lowercase UUID")

    status = _text(project["status"], "status", maximum=20)
    if status not in _PROJECT_STATUSES:
        _fail("status", f"must be one of {', '.join(sorted(_PROJECT_STATUSES))}")
    task = _validate_task(project["task"])
    outputs = _validate_outputs(project["outputs"])
    expected_project_status = {
        "running": "running",
        "succeeded": "completed",
        "failed": "failed",
    }.get(str(task["status"]))
    if expected_project_status is not None and status != expected_project_status:
        _fail("status", f"must be '{expected_project_status}' when task status is '{task['status']}'")
    if task["status"] == "succeeded" and outputs["video"] is None:
        _fail("outputs.video", "is required when task status is succeeded")
    if status == "completed" and task["status"] != "succeeded":
        _fail("task.status", "must be succeeded when project status is completed")
    if status == "failed" and task["status"] != "failed":
        _fail("task.status", "must be failed when project status is failed")

    return {
        "schema_version": SCHEMA_VERSION,
        "id": project_id,
        "name": _text(project["name"], "name"),
        "created_at": _timestamp(project["created_at"], "created_at"),
        "status": status,
        "scenario": _validate_scenario(project["scenario"]),
        "audio": _validate_audio(project["audio"]),
        "task": task,
        "outputs": outputs,
    }


def _default_scenario() -> dict[str, object]:
    return {
        "type": "rigid_body_chain",
        "objects": [
            {
                "id": "starter",
                "shape": "sphere",
                "position": [-2.0, 0.0, 0.5],
                "dimensions": [0.5, 0.5, 0.5],
                "mass_kg": 1.0,
                "friction": 0.5,
                "restitution": 0.2,
            },
            {
                "id": "target",
                "shape": "box",
                "position": [0.0, 0.0, 0.5],
                "dimensions": [0.3, 0.3, 1.0],
                "mass_kg": 0.5,
                "friction": 0.5,
                "restitution": 0.1,
            },
        ],
        "gravity_m_s2": [0.0, 0.0, -9.81],
        "camera": {
            "position": [7.0, -10.0, 7.0],
            "target": [0.0, 0.0, 0.5],
            "lens_mm": 50.0,
        },
        "video": {
            "width": 720,
            "height": 1280,
            "fps": 24,
            "frame_count": 120,
            "eevee_samples": 8,
        },
    }


def create_project(name: str, scenario: Mapping[str, object] | None = None) -> dict[str, Any]:
    """Create a validated draft project with a minimal rigid-body scenario."""
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    project = {
        "schema_version": SCHEMA_VERSION,
        "id": str(uuid4()),
        "name": name,
        "created_at": now,
        "status": "draft",
        "scenario": _default_scenario() if scenario is None else scenario,
        "audio": {"enabled": False, "source": None, "volume": 1.0},
        "task": {
            "status": "not_started",
            "error": None,
            "run_id": None,
            "started_at": None,
            "completed_at": None,
        },
        "outputs": {"video": None, "report": None},
    }
    return validate_project(project)


class ProjectStore:
    """Persist each project as one validated, atomically replaced JSON file."""

    def __init__(self, root: str | os.PathLike[str]) -> None:
        supplied_root = Path(root).expanduser()
        if supplied_root.is_symlink():
            raise ProjectStoreError("Project storage root must not be a symbolic link.")
        self.root = supplied_root.resolve()

    def _ensure_root(self, create: bool) -> None:
        if self.root.exists():
            if not self.root.is_dir():
                raise ProjectStoreError(f"Project storage root is not a directory: {self.root}")
            return
        if not create:
            raise ProjectStoreError(f"Project storage directory does not exist: {self.root}")
        try:
            self.root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ProjectStoreError(f"Cannot create project storage directory: {exc}") from exc

    @staticmethod
    def _validated_id(project_id: str) -> str:
        if not isinstance(project_id, str) or not _PROJECT_ID_PATTERN.fullmatch(project_id):
            raise ProjectValidationError("id: must be a canonical lowercase UUID")
        try:
            if str(UUID(project_id)) != project_id:
                raise ValueError
        except ValueError as exc:
            raise ProjectValidationError("id: must be a canonical lowercase UUID") from exc
        return project_id

    def _path_for(self, project_id: str) -> Path:
        return self.root / f"{self._validated_id(project_id)}.json"

    def save(self, project: Mapping[str, object]) -> dict[str, Any]:
        """Validate and atomically persist a project; return the normalized document."""
        normalized = validate_project(project)
        self._ensure_root(create=True)
        destination = self._path_for(normalized["id"])
        if destination.is_symlink():
            raise ProjectStoreError("Refusing to overwrite a symbolic link in project storage.")

        temporary_path: Path | None = None
        failure: OSError | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{normalized['id']}.",
                suffix=".tmp",
                dir=self.root,
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(normalized, stream, ensure_ascii=False, indent=2, allow_nan=False)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, destination)
            temporary_path = None
        except OSError as exc:
            failure = exc
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError as cleanup_error:
                    if failure is None:
                        failure = cleanup_error
                    else:
                        failure = OSError(
                            f"{failure}; temporary-file cleanup also failed: {cleanup_error}"
                        )
        if failure is not None:
            raise ProjectStoreError(
                f"Cannot save project {normalized['id']}: {failure}"
            ) from failure
        return normalized

    def load(self, project_id: str) -> dict[str, Any]:
        """Load and validate a project by canonical UUID."""
        self._ensure_root(create=False)
        source = self._path_for(project_id)
        if source.is_symlink():
            raise ProjectStoreError("Refusing to read a symbolic link in project storage.")
        try:
            size = source.stat().st_size
            if not stat.S_ISREG(source.stat().st_mode):
                raise ProjectStoreError(f"Project is not a regular file: {source.name}")
            if size > MAX_PROJECT_FILE_BYTES:
                raise ProjectStoreError(
                    f"Project file exceeds the {MAX_PROJECT_FILE_BYTES}-byte size limit."
                )
            text = source.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ProjectStoreError(f"Project not found: {project_id}") from exc
        except UnicodeDecodeError as exc:
            raise ProjectStoreError(f"Project file is not valid UTF-8: {source.name}") from exc
        except OSError as exc:
            raise ProjectStoreError(f"Cannot read project {project_id}: {exc}") from exc
        try:
            document = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
        except (json.JSONDecodeError, ProjectStoreError) as exc:
            raise ProjectStoreError(f"Invalid project JSON in {source.name}: {exc}") from exc
        try:
            normalized = validate_project(document)
        except ProjectValidationError as exc:
            raise ProjectStoreError(f"Invalid project document in {source.name}: {exc}") from exc
        if normalized["id"] != project_id:
            raise ProjectStoreError("Project file ID does not match the requested ID.")
        return normalized

    def list_projects(self) -> list[dict[str, Any]]:
        """Return all valid stored projects in creation-time and ID order."""
        self._ensure_root(create=False)
        projects = []
        try:
            paths = sorted(self.root.glob("*.json"))
        except OSError as exc:
            raise ProjectStoreError(f"Cannot list project storage: {exc}") from exc
        for path in paths:
            if path.is_symlink():
                raise ProjectStoreError(f"Refusing to read symbolic link: {path.name}")
            try:
                project_id = path.stem
                projects.append(self.load(project_id))
            except ProjectValidationError:
                raise
        return sorted(projects, key=lambda item: (item["created_at"], item["id"]))


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ProjectStoreError(f"duplicate JSON key '{key}'")
        result[key] = value
    return result
