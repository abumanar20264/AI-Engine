import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


OUTPUT = Path("/kaggle/working/ai-engine-blender-runtime-preflight")
OUTPUT.mkdir(parents=True, exist_ok=True)
REPORT_PATH = OUTPUT / "preflight_report.json"
report = {
    "started_utc": datetime.now(timezone.utc).isoformat(),
    "python": sys.version,
    "platform": platform.platform(),
    "stages": {},
    "artifacts": [],
}


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
            "output_tail": combined[-4000:],
        }
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        err = exc.stderr or ""
        if isinstance(out, bytes):
            out = out.decode(errors="replace")
        if isinstance(err, bytes):
            err = err.decode(errors="replace")
        combined = f"COMMAND: {json.dumps([str(part) for part in command])}\nTIMEOUT after {timeout}s\n{out}\n{err}"
        log_path.write_text(combined, encoding="utf-8", errors="replace")
        stage = {
            "status": "FAILED",
            "exit_code": None,
            "error": f"Timeout after {timeout} seconds",
            "command": [str(part) for part in command],
            "duration_seconds": round(time.monotonic() - started, 3),
            "log": log_path.name,
            "output_tail": combined[-4000:],
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
            "output_tail": combined[-4000:],
        }
    report["stages"][name] = stage
    print(f"{name}: {stage['status']} (exit_code={stage['exit_code']})")
    return stage


def official_apt_hosts():
    hosts = []
    sources = list(Path("/etc/apt").glob("sources.list"))
    sources += list(Path("/etc/apt/sources.list.d").glob("*.list"))
    sources += list(Path("/etc/apt/sources.list.d").glob("*.sources"))
    for source in sources:
        try:
            for line in source.read_text(errors="replace").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or stripped.lower().startswith(("types:", "suites:", "components:", "signed-by:", "architectures:", "signed-by:", "enabled:")):
                    continue
                for token in stripped.split():
                    if token.startswith(("http://", "https://")):
                        host = urlparse(token).hostname
                        if host:
                            hosts.append(host.lower())
        except OSError:
            continue
    return sorted(set(hosts))


def ubuntu_release():
    values = {}
    release_file = Path("/etc/os-release")
    if release_file.exists():
        for line in release_file.read_text(errors="replace").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key] = value.strip().strip('"')
    return values


def trusted_distribution_host(host):
    return (
        host == "ubuntu.com"
        or host.endswith(".ubuntu.com")
        or host == "debian.org"
        or host.endswith(".debian.org")
    )


def apt_policy_is_official(text):
    hosts = re.findall(r"https?://([A-Za-z0-9.-]+)", text)
    normalized = sorted(set(host.lower() for host in hosts))
    return bool(normalized) and all(trusted_distribution_host(host) for host in normalized), normalized


def find_blender():
    candidates = [shutil.which("blender")]
    candidates += ["/usr/bin/blender", "/usr/local/bin/blender", "/opt/blender/blender"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(Path(candidate).resolve())
    return None


print("AI-Engine Kaggle Blender runtime preflight")
print("Timestamp UTC:", report["started_utc"])
print("Python:", sys.version.replace("\n", " "))
print("OS:", platform.platform())
print("Architecture:", platform.machine())
print("Working directory:", os.getcwd())
print("Selected Kaggle environment:", {
    key: os.environ.get(key)
    for key in ("KAGGLE_KERNEL_RUN_TYPE", "KAGGLE_KERNEL_INTERNET_ENABLED")
    if key in os.environ
})

cpu_models = []
cpuinfo = Path("/proc/cpuinfo")
if cpuinfo.exists():
    for line in cpuinfo.read_text(errors="replace").splitlines():
        if line.lower().startswith("model name") and ":" in line:
            model = line.split(":", 1)[1].strip()
            if model not in cpu_models:
                cpu_models.append(model)
memory = {}
meminfo = Path("/proc/meminfo")
if meminfo.exists():
    for line in meminfo.read_text(errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            if key in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
                memory[key] = value.strip()
working = Path("/kaggle/working")
disk_info = None
if working.is_dir():
    usage = shutil.disk_usage(working)
    disk_info = {"total_bytes": usage.total, "used_bytes": usage.used, "free_bytes": usage.free}
environment = {
    "os_release": Path("/etc/os-release").read_text(errors="replace") if Path("/etc/os-release").exists() else None,
    "architecture": platform.machine(),
    "cpu_logical_count": os.cpu_count(),
    "cpu_models": cpu_models,
    "memory": memory,
    "disk_working": disk_info,
    "gpu_query": None,
    "tpu_device_paths": [str(path) for path in Path("/dev").glob("accel*")],
}
nvidia_smi = shutil.which("nvidia-smi")
if nvidia_smi:
    gpu_stage = run_command("gpu_inventory", [nvidia_smi, "-L"], timeout=10)
    environment["gpu_query"] = {
        "exit_code": gpu_stage["exit_code"],
        "output": gpu_stage.get("output_tail", ""),
    }
else:
    environment["gpu_query"] = {"status": "nvidia-smi not available"}
write_json(OUTPUT / "environment.json", environment)
report["stages"]["environment"] = {"status": "COMPLETED", "details": environment}
print("CPU logical count:", environment["cpu_logical_count"])
print("CPU model:", cpu_models or "not reported")
print("Memory:", memory or "not reported")
print("Working disk:", disk_info or "not available")
print("GPU query:", environment["gpu_query"])
print("TPU device paths:", environment["tpu_device_paths"])

probe = OUTPUT / "temporary-write-read.txt"
expected = "AI-Engine Kaggle preflight write/read verification\n"
try:
    probe.write_text(expected, encoding="utf-8")
    verified = probe.read_text(encoding="utf-8") == expected
    report["stages"]["temporary_write_read"] = {
        "status": "COMPLETED" if verified else "FAILED",
        "path": str(probe),
        "verified_contents": verified,
        "size_bytes": probe.stat().st_size,
    }
except Exception as exc:
    report["stages"]["temporary_write_read"] = {
        "status": "FAILED",
        "error": f"{type(exc).__name__}: {exc}",
    }

blender = find_blender()
report["stages"]["blender_detection"] = {
    "status": "COMPLETED" if blender else "FAILED",
    "path": blender,
}
if not blender:
    apt_get = shutil.which("apt-get")
    apt_cache = shutil.which("apt-cache")
    configured_hosts = official_apt_hosts()
    release = ubuntu_release()
    keyring = Path("/usr/share/keyrings/ubuntu-archive-keyring.gpg")
    source_file = OUTPUT / "ubuntu-official.sources"
    apt_lists = OUTPUT / "apt-state" / "lists"
    apt_lists.mkdir(parents=True, exist_ok=True)
    source_contents = (
        "Types: deb\n"
        "URIs: https://archive.ubuntu.com/ubuntu\n"
        f"Suites: {release.get('VERSION_CODENAME', '')} {release.get('VERSION_CODENAME', '')}-updates\n"
        "Components: main universe\n"
        f"Signed-By: {keyring}\n\n"
        "Types: deb\n"
        "URIs: https://security.ubuntu.com/ubuntu\n"
        f"Suites: {release.get('VERSION_CODENAME', '')}-security\n"
        "Components: main universe\n"
        f"Signed-By: {keyring}\n"
    )
    distro_verified = (
        release.get("ID") == "ubuntu"
        and bool(re.fullmatch(r"[a-z][a-z0-9-]{1,19}", release.get("VERSION_CODENAME", "")))
        and platform.machine() in ("x86_64", "amd64")
        and keyring.is_file()
        and keyring.stat().st_size > 0
    )
    report["stages"]["blender_detection"]["apt_sources"] = {
        "configured_hosts_not_used": configured_hosts,
        "isolated_sources": ["archive.ubuntu.com", "security.ubuntu.com"],
        "distribution": release.get("ID"),
        "codename": release.get("VERSION_CODENAME"),
        "signing_keyring": str(keyring),
        "distribution_and_keyring_verified": distro_verified,
    }
    if apt_get and apt_cache and distro_verified:
        source_file.write_text(source_contents, encoding="utf-8")
        apt_options = [
            "-o", f"Dir::Etc::sourcelist={source_file}",
            "-o", "Dir::Etc::sourceparts=-",
            "-o", f"Dir::State::lists={apt_lists}",
            "-o", "APT::Get::List-Cleanup=0",
        ]
        policy = run_command(
            "apt_blender_policy_initial",
            [apt_cache, *apt_options, "policy", "blender"],
            timeout=30,
        )
        policy_output = policy.get("output_tail", "")
        official, package_hosts = apt_policy_is_official(policy_output)
        if policy["status"] != "COMPLETED" or re.search(r"Candidate:\s+\(none\)", policy_output) or not official:
            update = run_command(
                "apt_update",
                [apt_get, *apt_options, "update"],
                timeout=600,
                extra_env={"DEBIAN_FRONTEND": "noninteractive"},
            )
            if update["status"] == "COMPLETED":
                policy = run_command(
                    "apt_blender_policy_after_update",
                    [apt_cache, *apt_options, "policy", "blender"],
                    timeout=30,
                )
                policy_output = policy.get("output_tail", "")
                official, package_hosts = apt_policy_is_official(policy_output)
        candidate_exists = not bool(re.search(r"Candidate:\s+\(none\)", policy_output))
        report["stages"]["blender_install"] = {
            "package_policy_hosts": package_hosts,
            "official_distribution_source_verified": official,
            "candidate_available": candidate_exists,
            "source_list": str(source_file),
            "configured_third_party_sources_were_not_used": True,
        }
        if official and candidate_exists and disk_info and disk_info["free_bytes"] >= 2 * 1024**3:
            privilege = []
            if os.geteuid() != 0:
                sudo = shutil.which("sudo")
                if sudo:
                    privilege = [sudo, "-n"]
            if os.geteuid() == 0 or privilege:
                install = run_command(
                    "blender_install_command",
                    privilege + [
                        apt_get,
                        *apt_options,
                        "install",
                        "-y",
                        "--no-install-recommends",
                        "blender",
                    ],
                    timeout=900,
                    extra_env={"DEBIAN_FRONTEND": "noninteractive"},
                )
                report["stages"]["blender_install"].update(install)
            else:
                report["stages"]["blender_install"].update({
                    "status": "BLOCKED",
                    "reason": "No non-interactive installation privilege is available.",
                })
        else:
            report["stages"]["blender_install"].update({
                "status": "BLOCKED",
                "reason": "No verified official package candidate or at least 2 GiB free disk space.",
                "free_disk_bytes": disk_info["free_bytes"] if disk_info else None,
            })
    else:
        report["stages"]["blender_install"] = {
            "status": "BLOCKED",
            "reason": "apt tools, a verified Ubuntu release/signing keyring, or the expected architecture are unavailable.",
            "apt_tools_available": bool(apt_get and apt_cache),
            "distribution_and_keyring_verified": distro_verified,
        }
    blender = find_blender()
    report["stages"]["blender_detection"]["path_after_install_attempt"] = blender
    if blender:
        report["stages"]["blender_detection"]["status"] = "COMPLETED"

if blender:
    report["blender_executable"] = blender
    version = run_command("blender_background_version", [blender, "--background", "--version"], timeout=30)
    report["stages"]["blender_version"] = version
    probe_script = OUTPUT / "probe_eevee.py"
    probe_script.write_text(
        "import bpy, json\n"
        "engines = [item.identifier for item in bpy.context.scene.render.bl_rna.properties['engine'].enum_items]\n"
        "eevee = next((name for name in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE') if name in engines), None)\n"
        "print('EEVEE_ENGINE_PROBE=' + json.dumps({'available': eevee is not None, 'selected': eevee, 'engines': engines}))\n"
        "if eevee is None:\n"
        "    raise RuntimeError('No EEVEE engine is exposed by this Blender build')\n",
        encoding="utf-8",
    )
    startup = run_command(
        "blender_background_startup",
        [blender, "--background", "--python", str(probe_script)],
        timeout=60,
    )
    report["stages"]["blender_background_startup"] = startup
    match = re.search(r"EEVEE_ENGINE_PROBE=(\{.*\})", startup.get("output_tail", ""))
    if match:
        try:
            report["stages"]["eevee_availability"] = json.loads(match.group(1))
            report["stages"]["eevee_availability"]["status"] = (
                "COMPLETED" if report["stages"]["eevee_availability"]["available"] else "FAILED"
            )
        except json.JSONDecodeError as exc:
            report["stages"]["eevee_availability"] = {"status": "FAILED", "error": str(exc)}
    else:
        report["stages"]["eevee_availability"] = {
            "status": "FAILED",
            "reason": "EEVEE probe did not emit its result marker; inspect blender_background_startup.log.",
        }

    scene_script = OUTPUT / "scene_test.py"
    scene_script.write_text(
        r'''
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
'''.strip()
        + "\n",
        encoding="utf-8",
    )
    scene_stage = run_command(
        "blender_scene_render_and_simulation",
        [blender, "--background", "--python", str(scene_script), "--", str(OUTPUT)],
        timeout=300,
    )
    report["stages"]["scene_render_and_simulation"] = scene_stage
    scene_result_path = OUTPUT / "scene_test.json"
    if scene_result_path.exists():
        try:
            report["scene_test"] = json.loads(scene_result_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report["scene_test"] = {"status": "FAILED", "error": str(exc)}
else:
    for stage_name in (
        "blender_version",
        "blender_background_startup",
        "eevee_availability",
        "scene_render_and_simulation",
    ):
        report["stages"][stage_name] = {
            "status": "BLOCKED",
            "reason": "Blender was not available after the allowed runtime package-source attempt.",
        }
    report["scene_test"] = {"status": "NOT TESTED"}

for path in sorted(OUTPUT.rglob("*")):
    if path.is_file() and path != REPORT_PATH:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        report["artifacts"].append({
            "name": str(path.relative_to(OUTPUT)),
            "size_bytes": path.stat().st_size,
            "sha256": digest,
        })

render_stage = report["scene_test"].get("render", {}).get("status")
simulation_stage = report["scene_test"].get("simulation", {}).get("status")
report["overall_status"] = (
    "COMPLETED"
    if render_stage == "COMPLETED" and simulation_stage == "COMPLETED"
    else "FAILED"
    if blender
    else "BLOCKED"
)
report["completed_utc"] = datetime.now(timezone.utc).isoformat()
write_json(REPORT_PATH, report)

print("Overall status:", report["overall_status"])
print("EEVEE render:", render_stage)
print("Rigid-body simulation:", simulation_stage)
print("Report:", REPORT_PATH, REPORT_PATH.stat().st_size, "bytes")
print("Artifact inventory:")
for artifact in report["artifacts"]:
    print(json.dumps(artifact, sort_keys=True))
print("Report SHA256:", hashlib.sha256(REPORT_PATH.read_bytes()).hexdigest())
