import hashlib
import json
import math
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


OUTPUT = Path("/kaggle/working/ai-engine-satisfying-physics-short")
OUTPUT.mkdir(parents=True, exist_ok=True)
REPORT_PATH = OUTPUT / "short_test_report.json"
report = {
    "title": "Satisfying Physics Test",
    "started_utc": datetime.now(timezone.utc).isoformat(),
    "python": sys.version,
    "platform": platform.platform(),
    "stages": {},
    "artifacts": [],
}
total_started = time.monotonic()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_command(name, command, timeout=60, extra_env=None):
    started = time.monotonic()
    log_path = OUTPUT / f"{name}.log"
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
            check=False,
            env=env,
        )
        output = (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")
        combined = (
            f"COMMAND: {json.dumps([str(part) for part in command])}\n"
            f"EXIT_CODE: {result.returncode}\n"
            f"{output}"
        )
        log_path.write_text(combined, encoding="utf-8", errors="replace")
        stage = {
            "status": "COMPLETED" if result.returncode == 0 else "FAILED",
            "exit_code": result.returncode,
            "command": [str(part) for part in command],
            "duration_seconds": round(time.monotonic() - started, 3),
            "log": log_path.name,
            "output_tail": combined[-5000:],
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="replace")
        combined = (
            f"COMMAND: {json.dumps([str(part) for part in command])}\n"
            f"TIMEOUT after {timeout}s\n{stdout}\n{stderr}"
        )
        log_path.write_text(combined, encoding="utf-8", errors="replace")
        stage = {
            "status": "FAILED",
            "exit_code": None,
            "error": f"Timeout after {timeout} seconds",
            "command": [str(part) for part in command],
            "duration_seconds": round(time.monotonic() - started, 3),
            "log": log_path.name,
            "output_tail": combined[-5000:],
        }
    except Exception as exc:
        combined = (
            f"COMMAND: {json.dumps([str(part) for part in command])}\n"
            f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        )
        log_path.write_text(combined, encoding="utf-8", errors="replace")
        stage = {
            "status": "FAILED",
            "exit_code": None,
            "error": f"{type(exc).__name__}: {exc}",
            "command": [str(part) for part in command],
            "duration_seconds": round(time.monotonic() - started, 3),
            "log": log_path.name,
            "output_tail": combined[-5000:],
        }
    report["stages"][name] = stage
    print(f"{name}: {stage['status']} (exit_code={stage['exit_code']})")
    return stage


def find_executable(name, candidates=()):
    found = shutil.which(name)
    if found:
        return str(Path(found).resolve())
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file() and os.access(path, os.X_OK):
            return str(path.resolve())
    return None


def find_new_video_candidates(output, existing_video_states):
    candidates = []
    for path in sorted(output.glob("satisfying_physics_test*.mp4")):
        if not path.is_file() or path.stat().st_size == 0:
            continue
        previous_state = existing_video_states.get(path.resolve())
        current_state = (path.stat().st_size, path.stat().st_mtime_ns)
        if previous_state != current_state:
            candidates.append(path)
    return candidates


def ubuntu_release():
    result = {}
    release_file = Path("/etc/os-release")
    if release_file.exists():
        for line in release_file.read_text(errors="replace").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                result[key] = value.strip().strip('"')
    return result


def official_policy_hosts(text):
    hosts = re.findall(r"https?://([A-Za-z0-9.-]+)", text)
    normalized = sorted(set(host.lower() for host in hosts))
    trusted = all(
        host == "ubuntu.com" or host.endswith(".ubuntu.com")
        or host == "debian.org" or host.endswith(".debian.org")
        for host in normalized
    )
    return bool(normalized) and trusted, normalized


def install_remote_tools_if_needed():
    blender = find_executable("blender", ("/usr/bin/blender", "/usr/local/bin/blender", "/opt/blender/blender"))
    ffmpeg = find_executable("ffmpeg")
    ffprobe = find_executable("ffprobe")
    report["stages"]["initial_tool_detection"] = {
        "status": "COMPLETED",
        "blender": blender,
        "ffmpeg": ffmpeg,
        "ffprobe": ffprobe,
    }
    if blender and ffmpeg and ffprobe:
        report["stages"]["runtime_tool_installation"] = {
            "status": "NOT_NEEDED",
            "reason": "Blender, ffmpeg, and ffprobe are already available.",
        }
        return blender, ffmpeg, ffprobe

    apt_get = shutil.which("apt-get")
    apt_cache = shutil.which("apt-cache")
    release = ubuntu_release()
    keyring = Path("/usr/share/keyrings/ubuntu-archive-keyring.gpg")
    codename = release.get("VERSION_CODENAME", "")
    distro_verified = (
        release.get("ID") == "ubuntu"
        and bool(re.fullmatch(r"[a-z][a-z0-9-]{1,19}", codename))
        and platform.machine() in ("x86_64", "amd64")
        and keyring.is_file()
        and keyring.stat().st_size > 0
    )
    usage = shutil.disk_usage("/kaggle/working")
    if not apt_get or not apt_cache or not distro_verified or usage.free < 2 * 1024**3:
        report["stages"]["runtime_tool_installation"] = {
            "status": "BLOCKED",
            "reason": "Official Ubuntu package tooling/keyring or 2 GiB free disk requirement not met.",
            "distribution": release.get("ID"),
            "codename": codename,
            "architecture": platform.machine(),
            "keyring_present": keyring.is_file(),
            "free_disk_bytes": usage.free,
        }
        return None, None, None

    sources = OUTPUT / "ubuntu-official.sources"
    lists = OUTPUT / "apt-state" / "lists"
    lists.mkdir(parents=True, exist_ok=True)
    sources.write_text(
        "Types: deb\n"
        "URIs: https://archive.ubuntu.com/ubuntu\n"
        f"Suites: {codename} {codename}-updates\n"
        "Components: main universe\n"
        f"Signed-By: {keyring}\n\n"
        "Types: deb\n"
        "URIs: https://security.ubuntu.com/ubuntu\n"
        f"Suites: {codename}-security\n"
        "Components: main universe\n"
        f"Signed-By: {keyring}\n",
        encoding="utf-8",
    )
    apt_options = [
        "-o", f"Dir::Etc::sourcelist={sources}",
        "-o", "Dir::Etc::sourceparts=-",
        "-o", f"Dir::State::lists={lists}",
        "-o", "APT::Get::List-Cleanup=0",
    ]
    policy = run_command(
        "apt_policy_initial",
        [apt_cache, *apt_options, "policy", "blender", "ffmpeg"],
        60,
    )
    candidate_lines = re.findall(r"Candidate:\s+(\S+)", policy.get("output_tail", ""))
    if policy["status"] != "COMPLETED" or len(candidate_lines) < 2 or "(none)" in candidate_lines:
        update = run_command(
            "apt_update",
            [apt_get, *apt_options, "update"],
            600,
            {"DEBIAN_FRONTEND": "noninteractive"},
        )
        if update["status"] != "COMPLETED":
            report["stages"]["runtime_tool_installation"] = {
                "status": "BLOCKED",
                "reason": "Isolated official Ubuntu apt update failed.",
                "source_list": str(sources),
            }
            return None, None, None
        policy = run_command(
            "apt_policy_after_update",
            [apt_cache, *apt_options, "policy", "blender", "ffmpeg"],
            60,
        )
    policy_text = policy.get("output_tail", "")
    official, hosts = official_policy_hosts(policy_text)
    candidate_lines = re.findall(r"Candidate:\s+(\S+)", policy_text)
    if policy["status"] != "COMPLETED" or not official or len(candidate_lines) < 2 or "(none)" in candidate_lines:
        report["stages"]["runtime_tool_installation"] = {
            "status": "BLOCKED",
            "reason": "No Blender/ffmpeg candidates verified from official Ubuntu package hosts.",
            "policy_hosts": hosts,
            "source_list": str(sources),
        }
        return None, None, None
    install = run_command(
        "runtime_tool_install",
        [apt_get, *apt_options, "install", "-y", "--no-install-recommends", "blender", "ffmpeg"],
        900,
        {"DEBIAN_FRONTEND": "noninteractive"},
    )
    report["stages"]["runtime_tool_installation"] = {
        "status": install["status"],
        "exit_code": install["exit_code"],
        "source_list": str(sources),
        "verified_package_hosts": hosts,
        "official_distribution_source_verified": official,
        "free_disk_before_install_bytes": usage.free,
        "install_log": install["log"],
    }
    if install["status"] != "COMPLETED":
        return None, None, None
    blender = find_executable("blender", ("/usr/bin/blender", "/usr/local/bin/blender", "/opt/blender/blender"))
    ffmpeg = find_executable("ffmpeg")
    ffprobe = find_executable("ffprobe")
    if not blender or not ffmpeg or not ffprobe:
        report["stages"]["runtime_tool_installation"]["status"] = "FAILED"
        report["stages"]["runtime_tool_installation"]["reason"] = "Expected executable still missing after official package installation."
        return None, None, None
    return blender, ffmpeg, ffprobe


SCENE_SCRIPT = r'''
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
            "output_basename": str(output / "satisfying_physics_test"),
            "expected_video_pattern": "satisfying_physics_test*.mp4",
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
'''


def main():
    print("AI-Engine first vertical Short export")
    print("Timestamp UTC:", report["started_utc"])
    print("Python:", sys.version.replace("\n", " "))
    print("Runtime:", platform.platform(), platform.machine())
    print("Kaggle run type:", os.environ.get("KAGGLE_KERNEL_RUN_TYPE", "not reported"))
    print("Accelerator inventory: GPU query", "available" if shutil.which("nvidia-smi") else "no nvidia-smi")
    print("TPU devices:", [str(path) for path in Path("/dev").glob("accel*")])
    blender, ffmpeg, ffprobe = install_remote_tools_if_needed()
    report["blender_executable"] = blender
    report["ffmpeg_executable"] = ffmpeg
    report["ffprobe_executable"] = ffprobe
    if not (blender and ffmpeg and ffprobe):
        report["overall_status"] = "BLOCKED"
        report["completed_utc"] = datetime.now(timezone.utc).isoformat()
        report["elapsed_seconds"] = round(time.monotonic() - total_started, 3)
        report["artifacts"] = [
            {
                "name": str(path.relative_to(OUTPUT)),
                "size_bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in sorted(OUTPUT.rglob("*"))
            if path.is_file() and path != REPORT_PATH
        ]
        write_json(REPORT_PATH, report)
        print("Overall status: BLOCKED; required runtime tools unavailable.")
        return 2

    version = run_command("blender_version", [blender, "--background", "--version"], 30)
    if version["status"] != "COMPLETED":
        report["overall_status"] = "FAILED"
        write_json(REPORT_PATH, report)
        return 2

    scene_script = OUTPUT / "short_scene.py"
    scene_script.write_text(SCENE_SCRIPT, encoding="utf-8")
    report["scene_source"] = scene_script.name
    existing_video_states = {
        path.resolve(): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in OUTPUT.glob("satisfying_physics_test*.mp4")
        if path.is_file()
    }
    blender_stage = run_command(
        "blender_short_render",
        [blender, "--background", "--python", str(scene_script), "--", str(OUTPUT)],
        timeout=1500,
    )
    report["stages"]["blender_short_render"] = blender_stage
    scene_report_path = OUTPUT / "scene_report.json"
    if scene_report_path.exists():
        try:
            report["scene"] = json.loads(scene_report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report["scene"] = {"status": "FAILED", "error": f"Invalid scene report: {exc}"}
    if report.get("scene", {}).get("render", {}).get("status") != "COMPLETED":
        blender_stage["status"] = "FAILED"
        blender_stage["error"] = (
            report.get("scene", {}).get("scene_setup", {}).get("error")
            or "Scene report does not confirm that Blender rendered the animation."
        )
    video_candidates = find_new_video_candidates(OUTPUT, existing_video_states)
    video = video_candidates[0] if len(video_candidates) == 1 else None
    if blender_stage["status"] != "COMPLETED" or video is None:
        candidate_details = [
            {"path": str(path), "size_bytes": path.stat().st_size}
            for path in sorted(OUTPUT.glob("satisfying_physics_test*.mp4"))
            if path.is_file()
        ]
        report["stages"]["video_probe"] = {
            "status": "FAILED",
            "reason": (
                "Blender render failed."
                if blender_stage["status"] != "COMPLETED"
                else "Expected exactly one non-empty satisfying_physics_test*.mp4; "
                f"found {len(video_candidates)} newly created or modified files. "
                "Inspect blender_short_render.log."
            ),
            "candidate_files": candidate_details,
        }
        report["overall_status"] = "FAILED"
    else:
        probe = run_command(
            "ffprobe_video_metadata",
            [
                ffprobe, "-v", "error", "-select_streams", "v:0",
                "-show_entries",
                "stream=codec_name,profile,width,height,r_frame_rate,avg_frame_rate,nb_frames,duration:format=duration,size",
                "-of", "json", str(video),
            ],
            60,
        )
        probe_data = None
        if probe["status"] == "COMPLETED":
            try:
                probe_data = json.loads(probe["output_tail"].split("\n", 2)[-1])
            except json.JSONDecodeError:
                try:
                    raw = probe["output_tail"]
                    json_start = raw.find("{")
                    probe_data = json.loads(raw[json_start:])
                except Exception as exc:
                    report["stages"]["video_probe_parse"] = {
                        "status": "FAILED",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
        report["video_metadata"] = probe_data
        if probe_data and probe_data.get("streams"):
            stream = probe_data["streams"][0]
            stream_duration = float(stream.get("duration", probe_data.get("format", {}).get("duration", 0)))
            frame_rate = stream.get("avg_frame_rate", "")
            report["stages"]["video_probe"] = {
                "status": "COMPLETED",
                "codec_is_h264": stream.get("codec_name") == "h264",
                "resolution_is_720x1280": (stream.get("width"), stream.get("height")) == (720, 1280),
                "frame_rate_is_24": frame_rate in ("24/1", "24/1.000"),
                "frame_count_is_120": stream.get("nb_frames") == "120",
                "duration_seconds": stream_duration,
                "duration_is_approximately_five_seconds": 4.95 <= stream_duration <= 5.05,
            }
            report["stages"]["video_probe"]["status"] = (
                "COMPLETED"
                if all(
                    report["stages"]["video_probe"][key]
                    for key in (
                        "codec_is_h264",
                        "resolution_is_720x1280",
                        "frame_rate_is_24",
                        "frame_count_is_120",
                        "duration_is_approximately_five_seconds",
                    )
                )
                else "FAILED"
            )
        else:
            report["stages"]["video_probe"] = {"status": "FAILED", "reason": "ffprobe metadata unavailable."}

        decode = run_command(
            "ffmpeg_full_decode",
            [ffmpeg, "-v", "error", "-i", str(video), "-f", "null", "-"],
            300,
        )
        report["stages"]["full_video_decode"] = decode
        preview = OUTPUT / "short_contact_sheet.png"
        contact = run_command(
            "extract_first_middle_last_frames",
            [
                ffmpeg, "-y", "-i", str(video),
                "-vf", "select='eq(n,0)+eq(n,59)+eq(n,119)',scale=240:426,tile=3x1",
                "-frames:v", "1", str(preview),
            ],
            120,
        )
        report["stages"]["contact_sheet"] = {
            **contact,
            "path": preview.name,
            "exists_nonempty": preview.is_file() and preview.stat().st_size > 0,
        }
        motion_command = [
            ffmpeg, "-v", "error", "-i", str(video),
            "-vf", "select='eq(n,0)+eq(n,59)+eq(n,119)',scale=64:114",
            "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ]
        motion_started = time.monotonic()
        try:
            motion_run = subprocess.run(
                motion_command,
                capture_output=True,
                timeout=120,
                check=False,
            )
            frame_size = 64 * 114 * 3
            raw = motion_run.stdout
            frame_count = len(raw) // frame_size if frame_size else 0
            means = []
            for index in range(frame_count):
                frame = raw[index * frame_size:(index + 1) * frame_size]
                means.append(sum(frame) / len(frame))
            differences = []
            for left, right in zip(range(len(means) - 1), range(1, len(means))):
                a = raw[left * frame_size:(left + 1) * frame_size]
                b = raw[right * frame_size:(right + 1) * frame_size]
                differences.append(sum(abs(x - y) for x, y in zip(a, b)) / frame_size)
            motion = {
                "status": "COMPLETED" if motion_run.returncode == 0 and frame_count == 3 else "FAILED",
                "exit_code": motion_run.returncode,
                "frames_decoded": frame_count,
                "mean_rgb_values": means,
                "mean_absolute_rgb_difference": differences,
                "visible_motion_threshold_passed": bool(differences and max(differences) > 3.0),
                "duration_seconds": round(time.monotonic() - motion_started, 3),
                "stderr_tail": motion_run.stderr.decode(errors="replace")[-2000:],
            }
            if motion["status"] == "COMPLETED" and not motion["visible_motion_threshold_passed"]:
                motion["status"] = "FAILED"
        except Exception as exc:
            motion = {
                "status": "FAILED",
                "exit_code": None,
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            }
        report["stages"]["visible_motion_check"] = motion

    report["video"] = {
        "path": str(video) if video is not None else None,
        "size_bytes": video.stat().st_size if video is not None else 0,
        "sha256": hashlib.sha256(video.read_bytes()).hexdigest() if video is not None else None,
    }
    required = (
        "video_probe",
        "full_video_decode",
        "contact_sheet",
        "visible_motion_check",
    )
    statuses = [report["stages"].get(stage, {}).get("status") for stage in required]
    motion_status = report.get("scene", {}).get("motion", {}).get("status")
    report["overall_status"] = (
        "COMPLETED"
        if all(status == "COMPLETED" for status in statuses)
        and motion_status == "COMPLETED"
        and report.get("scene", {}).get("render", {}).get("status") == "COMPLETED"
        else "FAILED"
    )

    for path in sorted(OUTPUT.rglob("*")):
        if path.is_file() and path != REPORT_PATH:
            report["artifacts"].append({
                "name": str(path.relative_to(OUTPUT)),
                "size_bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
    report["completed_utc"] = datetime.now(timezone.utc).isoformat()
    report["elapsed_seconds"] = round(time.monotonic() - total_started, 3)
    write_json(REPORT_PATH, report)
    print("Overall status:", report["overall_status"])
    print("Video:", video, report["video"]["size_bytes"], "bytes", report["video"]["sha256"])
    print("Metadata:", json.dumps(report.get("video_metadata"), sort_keys=True))
    print("Physics:", json.dumps(report.get("scene", {}).get("physics"), sort_keys=True))
    print("Visible motion:", json.dumps(report["stages"].get("visible_motion_check"), sort_keys=True))
    print("Elapsed seconds:", report["elapsed_seconds"])
    print("Report:", REPORT_PATH, REPORT_PATH.stat().st_size, "bytes")
    print("Artifact inventory:")
    for artifact in report["artifacts"]:
        print(json.dumps(artifact, sort_keys=True))
    return 0 if report["overall_status"] == "COMPLETED" else 1


exit_code = main()
if exit_code:
    sys.exit(exit_code)
