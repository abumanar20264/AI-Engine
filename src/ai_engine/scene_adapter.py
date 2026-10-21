"""Translate the versioned project contract into a Blender-independent scene plan."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

from .project_store import ProjectValidationError, validate_project


class SceneAdapterError(ValueError):
    """Raised when a valid project cannot be represented by the current scene adapter."""


@dataclass(frozen=True)
class SceneObject:
    object_id: str
    shape: str
    position: tuple[float, float, float]
    dimensions: tuple[float, float, float]
    mass_kg: float
    friction: float
    restitution: float


@dataclass(frozen=True)
class ScenePlan:
    project_id: str
    project_name: str
    scenario_type: str
    gravity_m_s2: tuple[float, float, float]
    frame_start: int
    frame_end: int
    fps: int
    resolution_x: int
    resolution_y: int
    eevee_samples: int
    camera_position: tuple[float, float, float]
    camera_target: tuple[float, float, float]
    camera_lens_mm: float
    objects: tuple[SceneObject, ...]
    launch_object_id: str
    target_object_id: str
    launch_start_position: tuple[float, float, float]
    launch_end_position: tuple[float, float, float]
    launch_start_frame: int
    launch_end_frame: int
    launch_release_frame: int
    physics_substeps_per_frame: int = 8
    physics_solver_iterations: int = 20
    render_engine: str = "BLENDER_EEVEE"
    render_device: str | None = None
    blender_version: str = "4.0.2"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _horizontal_support_radius(item: SceneObject, direction: tuple[float, float]) -> float:
    dx, dy = direction
    width, depth, _ = item.dimensions
    if item.shape == "sphere":
        return math.hypot(width * dx / 2, depth * dy / 2)
    if item.shape == "box":
        return abs(dx) * width / 2 + abs(dy) * depth / 2
    if item.shape == "cylinder":
        return max(width, depth) / 2
    raise SceneAdapterError(f"Unsupported object shape '{item.shape}'.")


def project_to_scene_plan(project: object) -> ScenePlan:
    """Validate a project and map every supported field to a deterministic scene plan."""
    try:
        normalized = validate_project(project)
    except ProjectValidationError as exc:
        if str(exc).startswith("scenario.type: unsupported scenario type"):
            raise SceneAdapterError(
                "Unsupported experiment type; only 'rigid_body_chain' is implemented."
            ) from exc
        raise SceneAdapterError(f"Invalid project: {exc}") from exc

    scenario = normalized["scenario"]
    if scenario["type"] != "rigid_body_chain":
        raise SceneAdapterError(
            f"Unsupported experiment type '{scenario['type']}'; "
            "only 'rigid_body_chain' is implemented."
        )

    video = scenario["video"]
    frame_count = int(video["frame_count"])
    fps = int(video["fps"])
    if frame_count < 4:
        raise SceneAdapterError(
            "A rigid-body chain needs at least 4 frames for its launch and release."
        )

    objects = tuple(
        SceneObject(
            object_id=str(item["id"]),
            shape=str(item["shape"]),
            position=tuple(item["position"]),
            dimensions=tuple(item["dimensions"]),
            mass_kg=float(item["mass_kg"]),
            friction=float(item["friction"]),
            restitution=float(item["restitution"]),
        )
        for item in scenario["objects"]
    )
    launcher = objects[0]
    targets = tuple(
        item
        for item in objects[1:]
        if abs(item.position[2] - launcher.position[2])
        <= (item.dimensions[2] + launcher.dimensions[2]) / 2
    )
    if not targets:
        raise SceneAdapterError(
            "At least one target object must overlap the launcher's vertical collision band."
        )
    target = min(
        targets,
        key=lambda item: math.hypot(
            item.position[0] - launcher.position[0],
            item.position[1] - launcher.position[1],
        ),
    )
    dx = target.position[0] - launcher.position[0]
    dy = target.position[1] - launcher.position[1]
    distance = math.hypot(dx, dy)
    if distance < 1e-6:
        raise SceneAdapterError(
            "The first object and its nearest target must have different X/Y positions."
        )
    direction = (dx / distance, dy / distance)
    combined_radius = _horizontal_support_radius(launcher, direction) + _horizontal_support_radius(
        target, direction
    )
    if distance <= combined_radius:
        raise SceneAdapterError(
            "The first object overlaps its nearest target; separate their X/Y positions."
        )
    if scenario["gravity_m_s2"][2] >= 0:
        raise SceneAdapterError(
            "Gravity Z must be negative for the ground-supported rigid-body chain."
        )

    end_position = (
        target.position[0] - direction[0] * combined_radius,
        target.position[1] - direction[1] * combined_radius,
        launcher.position[2],
    )
    frame_start = 1
    frame_end = frame_start + frame_count - 1
    camera_delta = tuple(
        target_component - camera_component
        for camera_component, target_component in zip(
            scenario["camera"]["position"],
            scenario["camera"]["target"],
        )
    )
    if math.sqrt(sum(component * component for component in camera_delta)) < 1e-6:
        raise SceneAdapterError("Camera position and target must be different.")
    launch_frames = min(max(2, round(fps * 0.8)), frame_count - 2)
    launch_end_frame = frame_start + launch_frames
    release_frame = launch_end_frame + 1

    return ScenePlan(
        project_id=normalized["id"],
        project_name=normalized["name"],
        scenario_type=scenario["type"],
        gravity_m_s2=tuple(scenario["gravity_m_s2"]),
        frame_start=frame_start,
        frame_end=frame_end,
        fps=fps,
        resolution_x=int(video["width"]),
        resolution_y=int(video["height"]),
        eevee_samples=int(video["eevee_samples"]),
        camera_position=tuple(scenario["camera"]["position"]),
        camera_target=tuple(scenario["camera"]["target"]),
        camera_lens_mm=float(scenario["camera"]["lens_mm"]),
        objects=objects,
        launch_object_id=launcher.object_id,
        target_object_id=target.object_id,
        launch_start_position=launcher.position,
        launch_end_position=end_position,
        launch_start_frame=frame_start,
        launch_end_frame=launch_end_frame,
        launch_release_frame=release_frame,
    )
