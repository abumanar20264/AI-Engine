"""Create and save a Blender 4.0.2 EEVEE scene from a validated project JSON file."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback
from pathlib import Path
from typing import Any


def build_blender_scene(
    project: object,
    blend_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    try:
        bpy = importlib.import_module("bpy")
        Vector = importlib.import_module("mathutils").Vector
    except ImportError as exc:
        raise RuntimeError(
            "Blender Python API is unavailable; run this builder with Blender 4.0.2."
        ) from exc

    from ai_engine.scene_adapter import project_to_scene_plan

    if bpy.app.version != (4, 0, 2):
        raise RuntimeError(
            f"Blender 4.0.2 is required; found {bpy.app.version_string}."
        )
    plan = project_to_scene_plan(project)
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if blend_path.exists() or report_path.exists():
        raise FileExistsError(
            f"Refusing to overwrite an existing scene or report for project {plan.project_id}."
        )

    scene = bpy.context.scene
    for item in list(bpy.data.objects):
        bpy.data.objects.remove(item, do_unlink=True)

    scene.render.engine = plan.render_engine
    if not hasattr(scene, "eevee") or not hasattr(scene.eevee, "taa_render_samples"):
        raise RuntimeError("Blender EEVEE TAA sample configuration is unavailable.")
    scene.eevee.taa_render_samples = plan.eevee_samples
    scene.render.resolution_x = plan.resolution_x
    scene.render.resolution_y = plan.resolution_y
    scene.render.resolution_percentage = 100
    scene.render.fps = plan.fps
    scene.render.fps_base = 1.0
    scene.frame_start = plan.frame_start
    scene.frame_end = plan.frame_end
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.audio_codec = "NONE"
    scene.render.filepath = str(blend_path.with_suffix(".mp4"))
    scene.gravity = Vector(plan.gravity_m_s2)
    scene.world.color = (0.018, 0.03, 0.045)

    ground_material = _create_material(
        bpy,
        "AI Engine Ground",
        (0.045, 0.075, 0.09),
        0.15,
        0.44,
    )
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
    ground = bpy.context.object
    ground.name = "Ground"
    ground.data.materials.append(ground_material)
    bpy.ops.rigidbody.object_add()
    ground.rigid_body.type = "PASSIVE"
    ground.rigid_body.friction = 0.75

    object_materials = [
        _create_material(bpy, "AI Engine Object 1", (0.95, 0.23, 0.08), 0.18, 0.28),
        _create_material(bpy, "AI Engine Object 2", (0.04, 0.62, 0.76), 0.12, 0.3),
        _create_material(bpy, "AI Engine Object 3", (0.34, 0.76, 0.36), 0.1, 0.3),
        _create_material(bpy, "AI Engine Object 4", (0.78, 0.36, 0.68), 0.15, 0.27),
    ]
    scene_objects: dict[str, Any] = {}
    for index, item in enumerate(plan.objects):
        obj = _create_mesh_object(bpy, item.shape, item.dimensions, item.position)
        obj.name = f"Physics Object {item.object_id}"
        obj.data.materials.append(object_materials[index % len(object_materials)])
        if item.shape == "sphere":
            for polygon in obj.data.polygons:
                polygon.use_smooth = True
        bpy.ops.rigidbody.object_add()
        obj.rigid_body.type = "ACTIVE"
        obj.rigid_body.mass = item.mass_kg
        obj.rigid_body.friction = item.friction
        obj.rigid_body.restitution = item.restitution
        obj.rigid_body.collision_shape = item.shape.upper()
        obj.rigid_body.use_margin = True
        obj.rigid_body.collision_margin = 0.001
        scene_objects[item.object_id] = obj

    launcher = scene_objects[plan.launch_object_id]
    launcher.rigid_body.kinematic = True
    launcher.location = plan.launch_start_position
    launcher.keyframe_insert(data_path="location", frame=plan.launch_start_frame)
    launcher.location = plan.launch_end_position
    launcher.keyframe_insert(data_path="location", frame=plan.launch_end_frame)
    launcher.rigid_body.keyframe_insert(
        data_path="kinematic",
        frame=plan.launch_start_frame,
    )
    launcher.rigid_body.keyframe_insert(
        data_path="kinematic",
        frame=plan.launch_end_frame,
    )
    launcher.rigid_body.kinematic = False
    launcher.rigid_body.keyframe_insert(
        data_path="kinematic",
        frame=plan.launch_release_frame,
    )
    _set_launch_interpolation(launcher)

    world = scene.rigidbody_world
    if world is None:
        raise RuntimeError("Blender did not create a rigid-body world.")
    world.time_scale = 1.0
    world.substeps_per_frame = plan.physics_substeps_per_frame
    world.solver_iterations = plan.physics_solver_iterations
    world.point_cache.frame_start = plan.frame_start
    world.point_cache.frame_end = plan.frame_end

    bpy.ops.object.camera_add(location=plan.camera_position)
    camera = bpy.context.object
    camera.name = "Project Camera"
    camera.rotation_euler = (
        Vector(plan.camera_target) - camera.location
    ).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = plan.camera_lens_mm
    scene.camera = camera

    bpy.ops.object.light_add(type="AREA", location=(0, -5, 8))
    key_light = bpy.context.object
    key_light.name = "Large Soft Key"
    key_light.data.energy = 1200
    key_light.data.shape = "DISK"
    key_light.data.size = 7
    key_light.rotation_euler = (
        Vector((0, 0, 0)) - key_light.location
    ).to_track_quat("-Z", "Y").to_euler()

    bpy.ops.object.light_add(type="AREA", location=(4, 2, 5))
    fill_light = bpy.context.object
    fill_light.name = "Cool Fill"
    fill_light.data.energy = 700
    fill_light.data.color = (0.42, 0.68, 1.0)
    fill_light.data.shape = "DISK"
    fill_light.data.size = 5
    fill_light.rotation_euler = (
        Vector((0, 0, 1)) - fill_light.location
    ).to_track_quat("-Z", "Y").to_euler()

    report = {
        "status": "SCENE_BUILT",
        "project_id": plan.project_id,
        "blender_version": bpy.app.version_string,
        "engine": scene.render.engine,
        "device": plan.render_device,
        "resolution": [plan.resolution_x, plan.resolution_y],
        "fps": plan.fps,
        "frame_start": plan.frame_start,
        "frame_end": plan.frame_end,
        "frame_count": plan.frame_end - plan.frame_start + 1,
        "eevee_samples": scene.eevee.taa_render_samples,
        "gravity_m_s2": list(plan.gravity_m_s2),
        "object_count": len(plan.objects),
        "dynamic_object_ids": [item.object_id for item in plan.objects],
        "kinematic_launcher_id": plan.launch_object_id,
        "first_collision_target_id": plan.target_object_id,
        "launcher_release_frame": plan.launch_release_frame,
        "movement_mode": "KINEMATIC_LAUNCH_THEN_RIGID_BODY_SIMULATION",
        "simulation_or_render_executed": False,
        "blend_file": str(blend_path),
        "scene_plan": plan.to_dict(),
    }
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return report


def _create_material(
    bpy: Any,
    name: str,
    color: tuple[float, float, float],
    metallic: float,
    roughness: float,
) -> Any:
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader is None:
        raise RuntimeError(f"Material '{name}' has no Principled BSDF node.")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return material


def _create_mesh_object(
    bpy: Any,
    shape: str,
    dimensions: tuple[float, float, float],
    position: tuple[float, float, float],
) -> Any:
    if shape == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=32,
            ring_count=20,
            radius=0.5,
            location=position,
        )
    elif shape == "box":
        bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    elif shape == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=32,
            radius=0.5,
            depth=1,
            location=position,
        )
    else:
        raise RuntimeError(f"Unsupported Blender mesh shape '{shape}'.")
    obj = bpy.context.object
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def _set_launch_interpolation(obj: Any) -> None:
    animation_data = obj.animation_data
    if animation_data is None or animation_data.action is None:
        return
    action = animation_data.action
    curves = getattr(action, "fcurves", ())
    for curve in curves:
        if curve.data_path == "location":
            interpolation = "LINEAR"
        elif curve.data_path == "rigid_body.kinematic":
            interpolation = "CONSTANT"
        else:
            continue
        for point in curve.keyframe_points:
            point.interpolation = interpolation


def _arguments_after_separator(arguments: list[str]) -> list[str]:
    if "--" not in arguments:
        raise ValueError("Blender arguments must include '--' before builder options.")
    return arguments[arguments.index("--") + 1 :]


def main(arguments: list[str] | None = None) -> int:
    script_path = Path(__file__).resolve()
    source_root = script_path.parents[1]
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))

    parser = argparse.ArgumentParser(description="Build a Blender scene from project JSON.")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    try:
        options = parser.parse_args(_arguments_after_separator(sys.argv if arguments is None else arguments))
        project = json.loads(
            options.project.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite_number,
        )
        report = build_blender_scene(project, options.output, options.report)
        print(json.dumps(report, ensure_ascii=False, allow_nan=False))
        return 0
    except Exception as exc:
        print(f"SCENE_BUILD_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key '{key}'")
        result[key] = value
    return result


def _reject_non_finite_number(value: str) -> None:
    raise ValueError(f"non-finite JSON number {value} is not allowed")


if __name__ == "__main__":
    raise SystemExit(main())
