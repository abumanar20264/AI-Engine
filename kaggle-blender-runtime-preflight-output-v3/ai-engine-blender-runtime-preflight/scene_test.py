import bpy
import json
import math
import sys
import traceback
from pathlib import Path
from mathutils import Vector

output = Path(sys.argv[sys.argv.index("--") + 1])
result = {"simulation": {"status": "NOT TESTED"}, "render": {"status": "NOT TESTED"}}

def save_result():
    (output / "scene_test.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

try:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    engine_items = [item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items]
    engine = next((name for name in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE") if name in engine_items), None)
    result["render"]["engine"] = engine

    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
    ground = bpy.context.object
    ground.name = "Ground"
    bpy.ops.rigidbody.object_add()
    ground.rigid_body.type = "PASSIVE"
    ground.rigid_body.friction = 0.65

    cubes = []
    for index, height in enumerate((1.1, 2.25, 3.4), start=1):
        bpy.ops.mesh.primitive_cube_add(size=0.8, location=(0, 0, height))
        cube = bpy.context.object
        cube.name = f"DropCube{index}"
        bpy.ops.rigidbody.object_add()
        cube.rigid_body.mass = 1.0
        cube.rigid_body.friction = 0.55
        cube.rigid_body.restitution = 0.25
        cube.rigid_body.collision_shape = "BOX"
        cubes.append(cube)

    bpy.ops.object.camera_add(location=(6, -8, 6))
    camera = bpy.context.object
    camera.name = "PreflightCamera"
    direction = Vector((0, 0, 1.5)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 48
    scene.camera = camera

    bpy.ops.object.light_add(type="AREA", location=(1, -4, 7))
    light = bpy.context.object
    light.name = "PreflightAreaLight"
    light.data.energy = 600
    light.data.shape = "DISK"
    light.data.size = 5

    scene.render.resolution_x = 128
    scene.render.resolution_y = 128
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.frame_start = 1
    scene.frame_end = 48
    if scene.rigidbody_world:
        scene.rigidbody_world.substeps_per_frame = 4
        scene.rigidbody_world.solver_iterations = 10

    simulation_ok = False
    try:
        frames = []
        for frame in range(scene.frame_start, scene.frame_end + 1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            if frame in (1, 12, 24, 36, 48):
                frames.append({
                    "frame": frame,
                    "cube_z": [round(float(cube.matrix_world.translation.z), 5) for cube in cubes],
                })
        result["simulation"] = {
            "status": "COMPLETED",
            "frames_simulated": scene.frame_end,
            "samples": frames,
            "objects": [cube.name for cube in cubes],
            "ground": ground.name,
        }
        simulation_ok = True
    except Exception as exc:
        result["simulation"] = {
            "status": "FAILED",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }

    render_ok = False
    if engine is None:
        result["render"] = {"status": "FAILED", "reason": "This Blender build exposes no EEVEE engine."}
    else:
        try:
            scene.render.engine = engine
            if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
                scene.eevee.taa_render_samples = 8
            scene.render.filepath = str(output / "eevee_preflight.png")
            scene.frame_set(24)
            bpy.ops.render.render(write_still=True)
            image_path = Path(scene.render.filepath)
            result["render"] = {
                "status": "COMPLETED" if image_path.is_file() and image_path.stat().st_size > 0 else "FAILED",
                "engine": engine,
                "path": str(image_path),
                "size_bytes": image_path.stat().st_size if image_path.exists() else 0,
            }
            render_ok = result["render"]["status"] == "COMPLETED"
        except Exception as exc:
            result["render"] = {
                "status": "FAILED",
                "engine": engine,
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            }
    save_result()
    if not simulation_ok or not render_ok:
        sys.exit(3)
except Exception as exc:
    result["scene_setup"] = {
        "status": "FAILED",
        "error": f"{type(exc).__name__}: {exc}",
        "traceback": traceback.format_exc(),
    }
    save_result()
    raise
