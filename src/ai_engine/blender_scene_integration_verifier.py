"""Verify a saved scene and measure rigid-body motion when run inside Blender."""

from __future__ import annotations

import argparse
import importlib
import json
import math
import sys
import traceback
from pathlib import Path
from typing import Any


def verify_scene(
    bpy: Any,
    expected_blend_file: Path,
    scene_report_file: Path,
) -> dict[str, Any]:
    scene_report = json.loads(scene_report_file.read_text(encoding="utf-8"))
    plan = scene_report["scene_plan"]
    scene = bpy.context.scene
    project_id = scene_report["project_id"]
    resolved_blend = expected_blend_file.resolve()
    checks: dict[str, bool] = {
        "blender_version": bpy.app.version == (4, 0, 2),
        "blend_reopened": (
            bool(bpy.data.filepath)
            and Path(bpy.data.filepath).resolve() == resolved_blend
        ),
        "eevee_settings": (
            scene.render.engine == "BLENDER_EEVEE"
            and scene.eevee.taa_render_samples == plan["eevee_samples"]
            and scene.render.resolution_x == plan["resolution_x"]
            and scene.render.resolution_y == plan["resolution_y"]
            and scene.render.fps == plan["fps"]
            and scene.frame_start == plan["frame_start"]
            and scene.frame_end == plan["frame_end"]
        ),
    }
    objects = {
        item["object_id"]: bpy.data.objects.get(f"Physics Object {item['object_id']}")
        for item in plan["objects"]
    }
    rigid_objects_valid = all(
        obj is not None
        and obj.rigid_body is not None
        and obj.rigid_body.type == "ACTIVE"
        and math.isclose(obj.rigid_body.mass, item["mass_kg"], rel_tol=1e-6)
        and math.isclose(obj.rigid_body.friction, item["friction"], rel_tol=1e-6)
        and math.isclose(obj.rigid_body.restitution, item["restitution"], rel_tol=1e-6)
        and obj.rigid_body.collision_shape == item["shape"].upper()
        for item, obj in zip(plan["objects"], objects.values())
    )
    ground = bpy.data.objects.get("Ground")
    checks["rigid_body_objects"] = (
        rigid_objects_valid
        and ground is not None
        and ground.rigid_body is not None
        and ground.rigid_body.type == "PASSIVE"
        and scene.rigidbody_world is not None
    )

    launcher = objects.get(plan["launch_object_id"])
    target = objects.get(plan["target_object_id"])
    world = scene.rigidbody_world
    if launcher is None or target is None or world is None:
        raise RuntimeError("The saved scene is missing its launcher, target, or rigid-body world.")

    start_frame = plan["frame_start"]
    contact_frame = plan["launch_end_frame"]
    pre_contact_frame = max(start_frame, contact_frame - 1)
    post_contact_frame = min(
        plan["frame_end"],
        plan["launch_release_frame"] + 8,
    )
    if post_contact_frame <= contact_frame:
        raise ValueError("The project timeline is too short to verify post-contact motion.")

    positions: dict[str, tuple[float, float, float]] = {}
    launcher_positions: dict[str, tuple[float, float, float]] = {}
    for frame in range(start_frame, post_contact_frame + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        if frame in (start_frame, pre_contact_frame, contact_frame, post_contact_frame):
            evaluated_target = target.evaluated_get(depsgraph)
            positions[str(frame)] = _vector3(
                evaluated_target.matrix_world.translation
            )
        if frame == contact_frame:
            evaluated_launcher = launcher.evaluated_get(depsgraph)
            launcher_positions[str(frame)] = _vector3(
                evaluated_launcher.matrix_world.translation
            )
    launcher_contact_position = launcher_positions[str(contact_frame)]
    expected_position = plan["launch_end_position"]
    launch_error = math.dist(launcher_contact_position, expected_position)
    before = positions[str(pre_contact_frame)]
    after = positions[str(post_contact_frame)]
    launch_dx = (
        plan["launch_end_position"][0] - plan["launch_start_position"][0]
    )
    launch_dy = (
        plan["launch_end_position"][1] - plan["launch_start_position"][1]
    )
    launch_length = math.hypot(launch_dx, launch_dy)
    projected_target_motion = (
        (after[0] - before[0]) * launch_dx
        + (after[1] - before[1]) * launch_dy
    ) / launch_length
    start_position = positions[str(start_frame)]
    pre_contact_motion = (
        (before[0] - start_position[0]) * launch_dx
        + (before[1] - start_position[1]) * launch_dy
    ) / launch_length
    checks["target_static_before_contact"] = pre_contact_motion <= 0.02
    checks["launcher_reached_contact"] = launch_error <= 0.1
    checks["target_moved_after_contact"] = projected_target_motion > 0.01

    failed = [name for name, passed in checks.items() if not passed]
    errors = [f"Check failed: {name}" for name in failed]
    report = {
        "schema_version": 1,
        "status": "FAILED" if failed else "PASSED",
        "project_id": project_id,
        "blender_version": bpy.app.version_string,
        "blend_file": str(resolved_blend),
        "checks": checks,
        "measurements": {
            "frame_start": start_frame,
            "pre_contact_frame": pre_contact_frame,
            "contact_frame": contact_frame,
            "post_contact_frame": post_contact_frame,
            "target_location_at_start": positions[str(start_frame)],
            "target_location_before_contact": before,
            "target_location_after_contact": after,
            "target_motion_toward_chain_before_contact_m": pre_contact_motion,
            "target_motion_toward_chain_m": projected_target_motion,
            "launcher_contact_position": launcher_contact_position,
            "launcher_contact_position_error_m": launch_error,
        },
        "errors": errors,
    }
    return report


def _vector3(value: Any) -> tuple[float, float, float]:
    return (float(value[0]), float(value[1]), float(value[2]))


def _arguments_after_separator(arguments: list[str]) -> list[str]:
    if "--" not in arguments:
        raise ValueError("Blender arguments must include '--' before verifier options.")
    return arguments[arguments.index("--") + 1 :]


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend-file", type=Path, required=True)
    parser.add_argument("--scene-report", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    options = parser.parse_args(
        _arguments_after_separator(sys.argv if arguments is None else arguments)
    )
    report: dict[str, Any]
    try:
        bpy = importlib.import_module("bpy")

        if bpy.app.version != (4, 0, 2):
            raise RuntimeError(
                f"Blender 4.0.2 is required; found {bpy.app.version_string}."
            )
        report = verify_scene(
            bpy,
            options.blend_file,
            options.scene_report,
        )
        exit_code = 0 if report["status"] == "PASSED" else 1
    except Exception as exc:
        report = {
            "schema_version": 1,
            "status": "FAILED",
            "project_id": None,
            "blender_version": None,
            "blend_file": None,
            "checks": {},
            "measurements": {},
            "errors": [f"{type(exc).__name__}: {exc}", traceback.format_exc()],
        }
        exit_code = 1
    options.report.parent.mkdir(parents=True, exist_ok=True)
    options.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, allow_nan=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
