
import bpy
import json
import math
import sys
import traceback
from pathlib import Path
from mathutils import Vector

output = Path(sys.argv[sys.argv.index("--") + 1])
report_path = output / "scene_report.json"
scene_report = {
    "title": "Satisfying Physics Test",
    "motion_mode": "KEYFRAMED_KINEMATIC_CHAIN",
    "motion_note": "Deterministic visual choreography using animated rigid bodies; dynamic solver impacts are not claimed.",
    "resolution": [720, 1280],
    "fps": 24,
    "frame_start": 1,
    "frame_end": 120,
    "frame_count": 120,
    "render_engine": "BLENDER_EEVEE",
    "render": {"status": "NOT_STARTED"},
    "motion_samples": [],
}

def save_report():
    report_path.write_text(json.dumps(scene_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def material(name, color, metallic=0.05, roughness=0.32, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission
    return mat

try:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 1280
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.render.fps_base = 1.0
    scene.frame_start = 1
    scene.frame_end = 120
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.ffmpeg.audio_codec = "NONE"
    scene.render.use_file_extension = True
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 8
        scene.eevee.use_gtao = True
        scene.eevee.gtao_distance = 3
        scene.eevee.gtao_factor = 1.25
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.world.color = (0.012, 0.022, 0.045)

    ground_mat = material("Deep blue stage", (0.018, 0.055, 0.105), 0.18, 0.38)
    ball_mat = material("Tangerine launch ball", (1.0, 0.22, 0.035), 0.22, 0.24)
    gold_mat = material("Warm gold", (1.0, 0.62, 0.08), 0.35, 0.23)
    domino_mats = [
        material("Cyan", (0.02, 0.78, 0.92), 0.18, 0.26),
        material("Mint", (0.10, 0.88, 0.56), 0.14, 0.28),
        material("Lime", (0.70, 0.94, 0.12), 0.12, 0.3),
        material("Pink", (0.96, 0.16, 0.42), 0.16, 0.26),
        material("Violet", (0.48, 0.22, 0.98), 0.2, 0.25),
    ]
    text_mat = material("Title ivory", (0.83, 0.94, 1.0), 0.0, 0.42, 0.12)

    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.08))
    ground = bpy.context.object
    ground.name = "Fixed stage"
    ground.data.materials.append(ground_mat)
    bpy.ops.rigidbody.object_add()
    ground.rigid_body.type = "PASSIVE"
    ground.rigid_body.friction = 0.75

    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 4, 3.0), rotation=(math.radians(90), 0, 0))
    backdrop = bpy.context.object
    backdrop.name = "Backdrop"
    backdrop.data.materials.append(ground_mat)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, radius=0.36, location=(-2.8, 0, 0.38))
    ball = bpy.context.object
    ball.name = "Orange launch sphere"
    ball.data.materials.append(ball_mat)
    for polygon in ball.data.polygons:
        polygon.use_smooth = True
    bpy.ops.rigidbody.object_add()
    ball.rigid_body.type = "ACTIVE"
    ball.rigid_body.mass = 1.4
    ball.rigid_body.friction = 0.42
    ball.rigid_body.restitution = 0.2
    ball.rigid_body.collision_shape = "SPHERE"
    ball.rigid_body.kinematic = True
    ball.location = (-2.8, 0, 0.38)
    ball.keyframe_insert(data_path="location", frame=1)
    ball.location = (-1.12, 0, 0.38)
    ball.keyframe_insert(data_path="location", frame=20)
    ball.location = (-0.88, 0, 0.38)
    ball.keyframe_insert(data_path="location", frame=24)
    ball.rigid_body.keyframe_insert(data_path="kinematic", frame=1)
    ball.rigid_body.keyframe_insert(data_path="kinematic", frame=120)
    ball.rotation_euler.y = 0
    ball.keyframe_insert(data_path="rotation_euler", frame=1)
    ball.rotation_euler.y = math.radians(-720)
    ball.keyframe_insert(data_path="rotation_euler", frame=24)
    ball.rotation_euler.y = math.radians(-820)
    ball.keyframe_insert(data_path="rotation_euler", frame=42)
    ball.rotation_euler.y = math.radians(-820)
    ball.keyframe_insert(data_path="rotation_euler", frame=120)
    if ball.animation_data and ball.animation_data.action:
        for curve in ball.animation_data.action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"

    dominoes = []
    spacing = 0.285
    first_x = -0.43
    for index in range(10):
        x = first_x + spacing * index
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, 0.61))
        domino = bpy.context.object
        domino.name = f"Domino {index + 1:02d}"
        domino.dimensions = (0.13, 0.56, 1.22)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bpy.context.scene.cursor.location = (x, 0, 0)
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
        domino.location = (x, 0, 0)
        domino.data.materials.append(domino_mats[index % len(domino_mats)])
        bevel = domino.modifiers.new("Soft polished edges", "BEVEL")
        bevel.width = 0.045
        bevel.segments = 3
        bpy.ops.rigidbody.object_add()
        domino.rigid_body.type = "ACTIVE"
        domino.rigid_body.kinematic = True
        domino.rigid_body.mass = 0.16
        domino.rigid_body.friction = 0.48
        domino.rigid_body.restitution = 0.035
        domino.rigid_body.collision_shape = "BOX"
        domino.rigid_body.keyframe_insert(data_path="kinematic", frame=1)
        domino.rigid_body.keyframe_insert(data_path="kinematic", frame=120)
        domino.rotation_euler.y = 0
        domino.keyframe_insert(data_path="rotation_euler", frame=1)
        start_frame = 25 + index * 4
        domino.rotation_euler.y = 0
        domino.keyframe_insert(data_path="rotation_euler", frame=start_frame)
        domino.rotation_euler.y = math.radians(82)
        domino.keyframe_insert(data_path="rotation_euler", frame=start_frame + 8)
        domino.rotation_euler.y = math.radians(88)
        domino.keyframe_insert(data_path="rotation_euler", frame=start_frame + 14)
        domino.rotation_euler.y = math.radians(88)
        domino.keyframe_insert(data_path="rotation_euler", frame=120)
        if domino.animation_data and domino.animation_data.action:
            for curve in domino.animation_data.action.fcurves:
                for point in curve.keyframe_points:
                    point.interpolation = "BEZIER"
        dominoes.append(domino)

    bpy.ops.object.text_add(location=(-2.55, 0.45, 5.35), rotation=(math.radians(90), 0, 0))
    title = bpy.context.object
    title.name = "Short title"
    title.data.body = "ONE PUSH. TEN FALLS."
    title.data.align_x = "LEFT"
    title.data.size = 0.31
    title.data.extrude = 0.002
    title.data.materials.append(text_mat)

    bpy.ops.object.camera_add(location=(0, -18, 6.2))
    camera = bpy.context.object
    camera.name = "Vertical Short camera"
    target = Vector((0, 0, 2.75))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 10.6
    camera.data.lens = 50
    scene.camera = camera

    bpy.ops.object.light_add(type="AREA", location=(-4, -6, 8))
    key = bpy.context.object
    key.name = "Large soft key"
    key.data.energy = 1050
    key.data.shape = "DISK"
    key.data.size = 7
    key.rotation_euler = (math.radians(25), 0, math.radians(-22))
    bpy.ops.object.light_add(type="AREA", location=(4, 1, 6))
    rim = bpy.context.object
    rim.name = "Color rim"
    rim.data.energy = 800
    rim.data.color = (0.28, 0.62, 1.0)
    rim.data.shape = "DISK"
    rim.data.size = 5
    rim.rotation_euler = (math.radians(20), 0, math.radians(155))

    world = scene.rigidbody_world
    world.time_scale = 1.0
    world.substeps_per_frame = 8
    world.solver_iterations = 20
    world.point_cache.frame_start = 1
    world.point_cache.frame_end = 120

    for frame in range(1, 121):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        if frame in (1, 20, 24, 30, 42, 60, 84, 108, 120):
            angles = [round(float(d.rotation_euler.y), 4) for d in dominoes]
            scene_report["motion_samples"].append({
                "frame": frame,
                "ball_x": round(float(ball.matrix_world.translation.x), 4),
                "domino_y_rotations": angles,
            })
    first = scene_report["motion_samples"][0]["ball_x"]
    last = scene_report["motion_samples"][-1]["ball_x"]
    max_rotation = max(
        abs(angle)
        for sample in scene_report["motion_samples"]
        for angle in sample["domino_y_rotations"]
    )
    scene_report["motion"] = {
        "status": "COMPLETED" if abs(last - first) > 1.0 and max_rotation > 0.25 else "FAILED",
        "mode": scene_report["motion_mode"],
        "ball_start_x": first,
        "ball_end_x": last,
        "maximum_domino_rotation_radians": max_rotation,
        "domino_count": len(dominoes),
        "fixed_ground": ground.name,
    }
    if scene_report["motion"]["status"] != "COMPLETED":
        raise RuntimeError("Short choreography did not produce ball travel and domino tipping.")

    scene.render.filepath = str(output / "satisfying_physics_test")
    scene.frame_set(1)
    save_report()
    render_started = __import__("time").monotonic()
    try:
        bpy.ops.render.render(animation=True)
        scene_report["render"] = {
            "status": "COMPLETED",
            "expected_video": str(output / "satisfying_physics_test.mp4"),
            "duration_seconds": round(__import__("time").monotonic() - render_started, 3),
            "resolution": [scene.render.resolution_x, scene.render.resolution_y],
            "fps": scene.render.fps,
            "frame_count": scene.frame_end - scene.frame_start + 1,
            "engine": scene.render.engine,
        }
    except Exception as exc:
        scene_report["render"] = {
            "status": "FAILED",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }
        raise
    save_report()
except Exception as exc:
    scene_report["scene_setup"] = {
        "status": "FAILED",
        "error": f"{type(exc).__name__}: {exc}",
        "traceback": traceback.format_exc(),
    }
    save_report()
    raise
