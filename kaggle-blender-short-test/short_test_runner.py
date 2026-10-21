import hashlib
import json
import math
import os
import platform
import posixpath
import re
import shutil
import stat
import struct
import subprocess
import sys
import tarfile
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse


OUTPUT = Path("/kaggle/working/ai-engine-satisfying-physics-short")
OUTPUT.mkdir(parents=True, exist_ok=True)
REPORT_PATH = OUTPUT / "short_test_report.json"
KAGGLE_INPUT = Path("/kaggle/input")
BLENDER_DATASET_REF = "haroonbaaraabumanar/ai-engine-blender-4-0-2-runtime"
KAGGLE_KERNEL_SLUG = "haroonbaaraabumanar/ai-engine-blender-runtime-preflight"
BLENDER_ARCHIVE_NAME = "blender-4.0.2-linux-x64.tar.xz"
BLENDER_ARCHIVE_SHA256 = "5583a5588736da8858c522ef17fff5d73be59c47a6fe91ad29c6f3263e22086a"
BUILD_MANIFEST_NAME = "ai_engine_blender_tree_manifest.json"
BUILD_MANIFEST_SHA256 = "5ae5f52d3338e5b61cbd366a6fb19b51e54fa93309a6ce7bca7b9cde22a5d052"
BLENDER_TREE_NAME = "blender-4.0.2-linux-x64"
BLENDER_RUNTIME_ROOT = Path("/kaggle/working/ai-engine-blender-4-0-2-runtime")
BLENDER_TREE_ROOT = BLENDER_RUNTIME_ROOT / BLENDER_TREE_NAME
KERNEL_V7_BASELINE = {
    "kernel_version": 7,
    "kaggle_run_id": "360664134",
    "elapsed_seconds": 583.558,
    "mp4_size_bytes": 259531,
    "mp4_sha256": "50b83bfaccc43297e1d5c238814170e1a78876784b378c8c72153d51be72c882",
    "codec": "h264",
    "resolution": [720, 1280],
    "fps": 24,
    "frame_count": 120,
    "duration_seconds": 5.0,
    "eevee_physics_png_bytes": 3807,
    "stage_measurements_available": False,
    "source": "PROJECT_WORK_ARCHIVE.md Kernel v7 record; Kaggle UI run route /edit/run/360664134",
}
HISTORICAL_RESTORE_V4 = {
    "source": "kaggle-blender-tree-restore-probe/full-dataset-verification/run-v4-report.json",
    "run_type": "independent full restore/runtime verification; not the production Short run",
    "archive_sha256_seconds": 3.335547,
    "extraction_seconds": 30.651143,
    "inventory_hash_seconds": 4.538482,
    "blender_startup_seconds": 0.380801,
    "embedded_python_check_seconds": 1.438743,
    "eevee_physics_combined_seconds": 8.401786,
    "eevee_png_bytes": 3797,
    "blender_version": "4.0.2",
    "embedded_python_version": "3.10.13",
}
report = {
    "title": "Satisfying Physics Test",
    "timing_schema_version": 1,
    "started_utc": datetime.now(timezone.utc).isoformat(),
    "python": sys.version,
    "platform": platform.platform(),
    "kaggle_kernel_slug": KAGGLE_KERNEL_SLUG,
    "kaggle_kernel_version": os.environ.get("KAGGLE_KERNEL_VERSION"),
    "timing_method": "time.monotonic; stage durations are measured independently and may be nested",
    "environment": {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count_logical": os.cpu_count(),
        "memory_bytes": {},
        "accelerator": "CPU-only",
    },
    "stages": {},
    "artifacts": [],
    "historical_baselines": {
        "kernel_v7": KERNEL_V7_BASELINE,
        "restore_run_v4": HISTORICAL_RESTORE_V4,
    },
}
try:
    for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
        key, separator, value = line.partition(":")
        if separator and key in ("MemTotal", "MemAvailable"):
            report["environment"]["memory_bytes"][key] = int(value.split()[0]) * 1024
except OSError as exc:
    report["environment"]["memory_info_error"] = f"{type(exc).__name__}: {exc}"
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


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_unique_input_file(filename):
    matches = [
        path for path in KAGGLE_INPUT.rglob(filename)
        if path.is_file() and not path.is_symlink()
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one mounted {filename}; found {len(matches)}."
        )
    return matches[0]


def validate_archive_member(member):
    path = PurePosixPath(member.name)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise RuntimeError(f"Unsafe Blender archive member path: {member.name!r}")
    if path.parts[0] != BLENDER_TREE_NAME:
        raise RuntimeError(f"Unexpected Blender archive root: {member.name!r}")
    if not (member.isfile() or member.isdir() or member.issym()):
        raise RuntimeError(f"Unsupported Blender archive member: {member.name!r}")
    if member.issym():
        resolved = PurePosixPath(
            posixpath.normpath(posixpath.join(str(path.parent), member.linkname))
        )
        if PurePosixPath(member.linkname).is_absolute() or resolved.parts[0] != BLENDER_TREE_NAME:
            raise RuntimeError(
                f"Unsafe Blender symlink target: {member.name!r} -> {member.linkname!r}"
            )


def inspect_blender_tree(tree_root, manifest, verify_content=True):
    expected_files = {item["path"]: item for item in manifest["files"]}
    expected_directories = {
        item["path"]: item for item in manifest["directories"]
    }
    expected_symlinks = {
        item["path"]: item["target"] for item in manifest["symlinks"]
    }
    actual_files = {}
    actual_directories = {}
    actual_symlinks = {}
    pending = [tree_root]
    while pending:
        current = pending.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative = path.relative_to(tree_root).as_posix()
                if entry.is_symlink():
                    actual_symlinks[relative] = os.readlink(path)
                elif entry.is_dir(follow_symlinks=False):
                    actual_directories[relative] = stat.S_IMODE(
                        entry.stat(follow_symlinks=False).st_mode
                    )
                    pending.append(path)
                elif entry.is_file(follow_symlinks=False):
                    details = {
                        "bytes": entry.stat(follow_symlinks=False).st_size,
                        "mode": stat.S_IMODE(path.stat(follow_symlinks=False).st_mode),
                    }
                    if verify_content:
                        details["sha256"] = sha256_file(path)
                    actual_files[relative] = details
                else:
                    raise RuntimeError(f"Unsupported restored filesystem entry: {path}")

    missing_files = sorted(set(expected_files) - set(actual_files))
    extra_files = sorted(set(actual_files) - set(expected_files))
    file_mode_mismatches = sorted(
        path for path, details in actual_files.items()
        if path in expected_files
        and details["mode"] != expected_files[path]["mode"]
    )
    hash_mismatches = sorted(
        path for path, details in actual_files.items()
        if path in expected_files
        and (
            details["bytes"] != expected_files[path]["bytes"]
            or (
                verify_content
                and details["sha256"] != expected_files[path]["sha256"]
            )
        )
    )
    missing_directories = sorted(set(expected_directories) - set(actual_directories))
    extra_directories = sorted(set(actual_directories) - set(expected_directories))
    directory_mode_mismatches = sorted(
        path for path, mode in actual_directories.items()
        if path in expected_directories
        and mode != expected_directories[path]["mode"]
    )
    symlink_mismatches = sorted(
        path for path, target in expected_symlinks.items()
        if actual_symlinks.get(path) != target
    )
    extra_symlinks = sorted(set(actual_symlinks) - set(expected_symlinks))
    unresolved_symlinks = sorted(
        path for path in expected_symlinks if not (tree_root / path).exists()
    )
    return {
        "regular_file_count": len(actual_files),
        "regular_file_bytes": sum(item["bytes"] for item in actual_files.values()),
        "content_hashes_verified": verify_content,
        "directory_count": len(actual_directories),
        "symlink_count": len(actual_symlinks),
        "resolved_symlink_count": len(expected_symlinks) - len(unresolved_symlinks),
        "missing_files": missing_files,
        "extra_files": extra_files,
        "hash_mismatches": hash_mismatches,
        "file_mode_mismatches": file_mode_mismatches,
        "missing_directories": missing_directories,
        "extra_directories": extra_directories,
        "directory_mode_mismatches": directory_mode_mismatches,
        "symlink_mismatches": symlink_mismatches,
        "extra_symlinks": extra_symlinks,
        "unresolved_symlinks": unresolved_symlinks,
    }


def restore_blender_runtime():
    started = time.monotonic()
    input_discovery_started = time.monotonic()
    archive = find_unique_input_file(BLENDER_ARCHIVE_NAME)
    manifest_path = find_unique_input_file(BUILD_MANIFEST_NAME)
    input_discovery_seconds = time.monotonic() - input_discovery_started
    archive_hash_started = time.monotonic()
    archive_sha256 = sha256_file(archive)
    archive_hash_seconds = time.monotonic() - archive_hash_started
    if archive_sha256 != BLENDER_ARCHIVE_SHA256:
        raise RuntimeError(
            f"Blender archive SHA-256 mismatch: expected {BLENDER_ARCHIVE_SHA256}, "
            f"got {archive_sha256}."
        )
    manifest_hash_started = time.monotonic()
    manifest_sha256 = sha256_file(manifest_path)
    manifest_hash_seconds = time.monotonic() - manifest_hash_started
    if manifest_sha256 != BUILD_MANIFEST_SHA256:
        raise RuntimeError(
            f"Blender build manifest SHA-256 mismatch: expected "
            f"{BUILD_MANIFEST_SHA256}, got {manifest_sha256}."
        )
    manifest_validation_started = time.monotonic()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest.get("expected", {})
    if expected != {"directories": 699, "file_bytes": 1315515076, "files": 5302, "symlinks": 85}:
        raise RuntimeError(f"Unexpected Blender build manifest inventory: {expected!r}")
    if (
        len(manifest["files"]) != expected["files"]
        or len({item["path"] for item in manifest["files"]}) != expected["files"]
        or sum(item["bytes"] for item in manifest["files"]) != expected["file_bytes"]
        or len(manifest["directories"]) != expected["directories"]
        or len({item["path"] for item in manifest["directories"]}) != expected["directories"]
        or len(manifest["symlinks"]) != expected["symlinks"]
        or len({item["path"] for item in manifest["symlinks"]}) != expected["symlinks"]
    ):
        raise RuntimeError("Blender build manifest entries do not match expected counts.")
    manifest_validation_seconds = time.monotonic() - manifest_validation_started

    restored = False
    extraction_seconds = 0.0
    free_disk_bytes = shutil.disk_usage("/kaggle/working").free
    required_disk_bytes = expected["file_bytes"] + 256 * 1024**2
    if not BLENDER_TREE_ROOT.exists() and free_disk_bytes < required_disk_bytes:
        raise RuntimeError(
            f"Insufficient writable disk space for Blender restore: "
            f"{free_disk_bytes} bytes free, {required_disk_bytes} required."
        )
    staging_root = BLENDER_RUNTIME_ROOT.with_name(
        BLENDER_RUNTIME_ROOT.name + ".staging"
    )
    if BLENDER_TREE_ROOT.exists():
        inventory_started = time.monotonic()
        inventory = inspect_blender_tree(BLENDER_TREE_ROOT, manifest)
        inventory_seconds = time.monotonic() - inventory_started
        if any(
            inventory[key]
            for key in (
                "missing_files", "extra_files", "hash_mismatches",
                "missing_directories", "extra_directories",
                "symlink_mismatches", "extra_symlinks", "unresolved_symlinks",
            )
        ):
            raise RuntimeError(
                "Existing Blender restore is not valid; refusing to overwrite it: "
                + json.dumps(inventory, sort_keys=True)
            )
        permissions_changed = False
        for item in manifest["files"]:
            path = BLENDER_TREE_ROOT / Path(*item["path"].split("/"))
            if stat.S_IMODE(path.stat().st_mode) != item["mode"]:
                os.chmod(path, item["mode"])
                permissions_changed = True
        for item in sorted(
            manifest["directories"],
            key=lambda directory: directory["path"].count("/"),
            reverse=True,
        ):
            path = BLENDER_TREE_ROOT / Path(*item["path"].split("/"))
            if stat.S_IMODE(path.stat().st_mode) != item["mode"]:
                os.chmod(path, item["mode"])
                permissions_changed = True
        if permissions_changed:
            reverify_started = time.monotonic()
            post_permission_inventory = inspect_blender_tree(
                BLENDER_TREE_ROOT, manifest, verify_content=False
            )
            inventory_seconds += time.monotonic() - reverify_started
            if any(
                post_permission_inventory[key]
                for key in (
                    "missing_files", "extra_files", "hash_mismatches",
                    "file_mode_mismatches", "missing_directories",
                    "extra_directories", "directory_mode_mismatches",
                    "symlink_mismatches", "extra_symlinks",
                    "unresolved_symlinks",
                )
            ):
                raise RuntimeError(
                    "Blender tree failed post-permission metadata verification: "
                    + json.dumps(post_permission_inventory, sort_keys=True)
                )
            inventory["file_mode_mismatches"] = (
                post_permission_inventory["file_mode_mismatches"]
            )
            inventory["directory_mode_mismatches"] = (
                post_permission_inventory["directory_mode_mismatches"]
            )
            inventory["post_permission_metadata_verified"] = True
        else:
            inventory["post_permission_metadata_verified"] = False
        restore_mode = "REUSED_VERIFIED"
    else:
        if staging_root.exists():
            raise FileExistsError(
                f"Found incomplete Blender staging path; preserving it for diagnosis: "
                f"{staging_root}"
            )
        staging_root.mkdir(parents=True)
        staged_tree = staging_root / BLENDER_TREE_NAME
        staged_tree.mkdir()
        expected_files = {item["path"]: item for item in manifest["files"]}
        expected_directories = {
            item["path"]: item for item in manifest["directories"]
        }
        expected_symlinks = {
            item["path"]: item["target"] for item in manifest["symlinks"]
        }
        directory_modes = {}
        extraction_started = time.monotonic()
        with tarfile.open(archive, mode="r|xz") as tar:
            for member in tar:
                validate_archive_member(member)
                member_path = PurePosixPath(member.name)
                relative = member_path.relative_to(BLENDER_TREE_NAME)
                if not relative.parts:
                    if not member.isdir():
                        raise RuntimeError("Blender archive root is not a directory.")
                    continue
                relative_name = relative.as_posix()
                destination = staged_tree.joinpath(*relative.parts)
                if member.isdir():
                    expected_directory = expected_directories.get(relative_name)
                    if expected_directory is None:
                        raise RuntimeError(f"Unexpected archive directory: {relative_name}")
                    if (member.mode & 0o777) != expected_directory["mode"]:
                        raise RuntimeError(f"Directory mode differs from manifest: {relative_name}")
                    destination.mkdir(parents=True, exist_ok=True)
                    directory_modes[destination] = expected_directory["mode"]
                elif member.isfile():
                    expected_file = expected_files.get(relative_name)
                    if expected_file is None:
                        raise RuntimeError(f"Unexpected archive file: {relative_name}")
                    if member.size != expected_file["bytes"]:
                        raise RuntimeError(f"File size differs from manifest: {relative_name}")
                    if (member.mode & 0o777) != expected_file["mode"]:
                        raise RuntimeError(f"File mode differs from manifest: {relative_name}")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    source = tar.extractfile(member)
                    if source is None:
                        raise RuntimeError(f"Could not read archive member: {member.name}")
                    digest = hashlib.sha256()
                    with source, destination.open("xb") as target:
                        while True:
                            chunk = source.read(1024 * 1024)
                            if not chunk:
                                break
                            digest.update(chunk)
                            target.write(chunk)
                    if digest.hexdigest() != expected_file["sha256"]:
                        raise RuntimeError(f"File SHA-256 differs from build manifest: {relative_name}")
                    os.chmod(destination, expected_file["mode"])
                else:
                    expected_target = expected_symlinks.get(relative_name)
                    if expected_target is None or member.linkname != expected_target:
                        raise RuntimeError(f"Unexpected archive symlink: {relative_name}")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    os.symlink(member.linkname, destination)
        for path, mode in sorted(
            directory_modes.items(), key=lambda item: len(item[0].parts), reverse=True
        ):
            os.chmod(path, mode)
        extraction_seconds = time.monotonic() - extraction_started
        inventory_started = time.monotonic()
        inventory = inspect_blender_tree(staged_tree, manifest)
        inventory_seconds = time.monotonic() - inventory_started
        if any(
            inventory[key]
            for key in (
                "missing_files", "extra_files", "hash_mismatches",
                "missing_directories", "extra_directories",
                "symlink_mismatches", "extra_symlinks", "unresolved_symlinks",
                "file_mode_mismatches", "directory_mode_mismatches",
            )
        ):
            raise RuntimeError(
                "Restored Blender tree failed inventory verification: "
                + json.dumps(inventory, sort_keys=True)
            )
        BLENDER_RUNTIME_ROOT.mkdir()
        os.replace(staged_tree, BLENDER_TREE_ROOT)
        staging_root.rmdir()
        restored = True
        restore_mode = "RESTORED_FROM_DATASET_ARCHIVE"

    if (
        inventory["regular_file_count"] != expected["files"]
        or inventory["regular_file_bytes"] != expected["file_bytes"]
        or inventory["directory_count"] != expected["directories"]
        or inventory["symlink_count"] != expected["symlinks"]
        or inventory["resolved_symlink_count"] != expected["symlinks"]
    ):
        raise RuntimeError(
            f"Restored Blender tree counts differ from the build manifest: {inventory!r}"
        )

    blender = BLENDER_TREE_ROOT / "blender"
    if not blender.is_file():
        raise FileNotFoundError(f"Blender executable is missing: {blender}")
    expected_blender = next(
        item for item in manifest["files"] if item["path"] == "blender"
    )
    mode = stat.S_IMODE(blender.stat().st_mode)
    if not mode & 0o111:
        mode = expected_blender["mode"] | 0o111
        os.chmod(blender, mode)
    if not os.access(blender, os.X_OK):
        raise PermissionError(f"Blender executable is not executable: {blender}")
    environment = {
        "LD_LIBRARY_PATH": os.pathsep.join(
            filter(
                None,
                [
                    str(BLENDER_TREE_ROOT / "lib"),
                    os.environ.get("LD_LIBRARY_PATH"),
                ],
            )
        )
    }
    return {
        "blender": str(blender),
        "environment": environment,
        "report": {
            "status": "VERIFIED",
            "dataset_ref": BLENDER_DATASET_REF,
            "archive_path": str(archive),
            "archive_bytes": archive.stat().st_size,
            "archive_sha256": archive_sha256,
            "archive_sha256_seconds": round(archive_hash_seconds, 6),
            "manifest_path": str(manifest_path),
            "manifest_sha256": manifest_sha256,
            "manifest_sha256_seconds": round(manifest_hash_seconds, 6),
            "mode": restore_mode,
            "restored_this_run": restored,
            "dataset_payload_type": "single TAR.XZ archive",
            "dataset_contains_unpacked_tree": False,
            "input_discovery_seconds": round(input_discovery_seconds, 6),
            "free_disk_before_restore_bytes": free_disk_bytes,
            "manifest_validation_seconds": round(manifest_validation_seconds, 6),
            "extraction_seconds": round(extraction_seconds, 6),
            "inventory_seconds": round(inventory_seconds, 6),
            "cache_status": "MISS_RESTORED" if restored else "HIT_REUSED",
            "tree_root": str(BLENDER_TREE_ROOT),
            "blender_executable_mode": oct(stat.S_IMODE(blender.stat().st_mode)),
            "blender_executable": os.access(blender, os.X_OK),
            **inventory,
            "total_seconds": round(time.monotonic() - started, 6),
        },
    }


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


def install_remote_video_tools_if_needed():
    ffmpeg = find_executable("ffmpeg")
    ffprobe = find_executable("ffprobe")
    report["stages"]["initial_tool_detection"] = {
        "status": "COMPLETED",
        "ffmpeg": ffmpeg,
        "ffprobe": ffprobe,
    }
    if ffmpeg and ffprobe:
        report["stages"]["runtime_tool_installation"] = {
            "status": "NOT_NEEDED",
            "reason": "ffmpeg and ffprobe are already available.",
        }
        return ffmpeg, ffprobe

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
        return None, None

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
        [apt_cache, *apt_options, "policy", "ffmpeg"],
        60,
    )
    candidate_lines = re.findall(r"Candidate:\s+(\S+)", policy.get("output_tail", ""))
    if policy["status"] != "COMPLETED" or len(candidate_lines) != 1 or "(none)" in candidate_lines:
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
            return None, None
        policy = run_command(
            "apt_policy_after_update",
            [apt_cache, *apt_options, "policy", "ffmpeg"],
            60,
        )
    policy_text = policy.get("output_tail", "")
    official, hosts = official_policy_hosts(policy_text)
    candidate_lines = re.findall(r"Candidate:\s+(\S+)", policy_text)
    if policy["status"] != "COMPLETED" or not official or len(candidate_lines) != 1 or "(none)" in candidate_lines:
        report["stages"]["runtime_tool_installation"] = {
            "status": "BLOCKED",
            "reason": "No ffmpeg candidate verified from official Ubuntu package hosts.",
            "policy_hosts": hosts,
            "source_list": str(sources),
        }
        return None, None
    install = run_command(
        "runtime_tool_install",
        [apt_get, *apt_options, "install", "-y", "--no-install-recommends", "ffmpeg"],
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
        "packages": ["ffmpeg"],
    }
    if install["status"] != "COMPLETED":
        return None, None
    ffmpeg = find_executable("ffmpeg")
    ffprobe = find_executable("ffprobe")
    if not ffmpeg or not ffprobe:
        report["stages"]["runtime_tool_installation"]["status"] = "FAILED"
        report["stages"]["runtime_tool_installation"]["reason"] = "Expected executable still missing after official package installation."
        return None, None
    return ffmpeg, ffprobe


def verify_blender_runtime(blender, environment):
    version = run_command(
        "blender_version",
        [blender, "--background", "--version"],
        30,
        environment,
    )
    if (
        version["status"] != "COMPLETED"
        or "Blender 4.0.2" not in version.get("output_tail", "")
    ):
        version["status"] = "FAILED"
        version["error"] = "Restored executable did not report Blender 4.0.2."
        return False

    python_test = run_command(
        "blender_embedded_python",
        [
            blender,
            "--background",
            "--python-expr",
            "import bpy, sys; print('BLENDER_PYTHON_OK', "
            "sys.version.split()[0], bpy.app.version_string)",
        ],
        60,
        environment,
    )
    if (
        python_test["status"] != "COMPLETED"
        or "BLENDER_PYTHON_OK 3.10.13 4.0.2"
        not in python_test.get("output_tail", "")
    ):
        python_test["status"] = "FAILED"
        python_test["error"] = (
            "Embedded Blender Python did not report the expected Python/Blender versions."
        )
        return False

    render_path = OUTPUT / "blender_runtime_smoke.png"
    scene_script = OUTPUT / "blender_runtime_smoke.py"
    scene_script.write_text(
        "\n".join(
            [
                "import bpy, json, time",
                "from mathutils import Vector",
                "smoke_started = time.monotonic()",
                "bpy.ops.wm.read_factory_settings(use_empty=True)",
                "scene = bpy.context.scene",
                "engines = [x.identifier for x in scene.render.bl_rna.properties['engine'].enum_items]",
                "engine = next((x for x in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT') if x in engines), None)",
                "if engine is None: raise RuntimeError('EEVEE is unavailable')",
                "bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))",
                "plane = bpy.context.object",
                "bpy.ops.rigidbody.object_add()",
                "plane.rigid_body.type = 'PASSIVE'",
                "cubes = []",
                "for z in (1.1, 2.25, 3.4):",
                "    bpy.ops.mesh.primitive_cube_add(size=0.8, location=(0, 0, z))",
                "    cube = bpy.context.object",
                "    bpy.ops.rigidbody.object_add()",
                "    cube.rigid_body.mass = 1.0",
                "    cube.rigid_body.collision_shape = 'BOX'",
                "    cubes.append(cube)",
                "bpy.ops.object.camera_add(location=(6, -8, 6))",
                "camera = bpy.context.object",
                "camera.rotation_euler = (Vector((0, 0, 1.5)) - camera.location).to_track_quat('-Z', 'Y').to_euler()",
                "scene.camera = camera",
                "bpy.ops.object.light_add(type='AREA', location=(1, -4, 7))",
                "light = bpy.context.object",
                "light.data.energy = 600",
                "light.data.shape = 'DISK'",
                "light.data.size = 5",
                "scene.frame_start, scene.frame_end = 1, 48",
                "if scene.rigidbody_world:",
                "    scene.rigidbody_world.substeps_per_frame = 4",
                "    scene.rigidbody_world.solver_iterations = 10",
                "samples = []",
                "physics_started = time.monotonic()",
                "for frame in range(1, 49):",
                "    scene.frame_set(frame)",
                "    bpy.context.view_layer.update()",
                "    if frame in (1, 48): samples.append({'frame': frame, 'cube_z': [round(float(c.matrix_world.translation.z), 5) for c in cubes]})",
                "physics_seconds = time.monotonic() - physics_started",
                "scene.render.engine = engine",
                "if hasattr(scene, 'eevee') and hasattr(scene.eevee, 'taa_render_samples'): scene.eevee.taa_render_samples = 8",
                "scene.render.resolution_x = 64",
                "scene.render.resolution_y = 64",
                "scene.render.resolution_percentage = 100",
                "scene.render.image_settings.file_format = 'PNG'",
                f"scene.render.filepath = {str(render_path)!r}",
                "scene.frame_set(24)",
                "eevee_render_started = time.monotonic()",
                "bpy.ops.render.render(write_still=True)",
                "eevee_render_seconds = time.monotonic() - eevee_render_started",
                "print(json.dumps({'engine': engine, 'samples': samples, 'physics_seconds': physics_seconds, 'eevee_render_seconds': eevee_render_seconds, 'smoke_total_seconds': time.monotonic() - smoke_started}))",
            ]
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    smoke = run_command(
        "blender_eevee_physics_smoke",
        [blender, "--background", "--python", str(scene_script)],
        180,
        environment,
    )
    payload = None
    for line in smoke.get("output_tail", "").splitlines():
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and "engine" in candidate:
            payload = candidate
            break
    samples = payload.get("samples", []) if payload else []
    first = next((item for item in samples if item.get("frame") == 1), None)
    last = next((item for item in samples if item.get("frame") == 48), None)
    physics_ok = (
        first is not None
        and last is not None
        and len(first.get("cube_z", [])) == 3
        and len(last.get("cube_z", [])) == 3
        and any(
            after < before - 0.05
            for before, after in zip(first["cube_z"], last["cube_z"])
        )
    )
    render_ok = render_path.is_file() and render_path.stat().st_size > 0
    smoke.update(
        {
            "engine": payload.get("engine") if payload else None,
            "physics_samples": samples,
            "physics_seconds": payload.get("physics_seconds") if payload else None,
            "eevee_render_seconds": payload.get("eevee_render_seconds") if payload else None,
            "smoke_total_seconds": payload.get("smoke_total_seconds") if payload else None,
            "physics_verified": physics_ok,
            "render_path": str(render_path),
            "render_bytes": render_path.stat().st_size if render_ok else 0,
            "runtime_checks_verified": (
                smoke["status"] == "COMPLETED"
                and payload is not None
                and payload.get("engine") in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT")
                and physics_ok
                and render_ok
            ),
        }
    )
    if not smoke["runtime_checks_verified"]:
        smoke["status"] = "FAILED"
        smoke["error"] = "EEVEE render or rigid-body smoke verification failed."
    report["stages"]["blender_eevee_physics_smoke"] = smoke
    return smoke["runtime_checks_verified"]


SCENE_SCRIPT = r'''
import bpy
import json
import math
import sys
import traceback
from pathlib import Path
from mathutils import Vector

arguments = sys.argv[sys.argv.index("--") + 1:]
output = Path(arguments[0])
report_path = output / "scene_report.json"
benchmark_samples = int(arguments[1]) if len(arguments) > 1 else None
render_samples = benchmark_samples or 8
scene_report = {
    "title": "Satisfying Physics Test",
    "timing_method": "time.monotonic inside the Blender process",
    "scene_setup_seconds": None,
    "motion_mode": "KEYFRAMED_KINEMATIC_CHAIN",
    "motion_note": "Deterministic visual choreography using animated rigid bodies; dynamic solver impacts are not claimed.",
    "resolution": [720, 1280],
    "fps": 24,
    "frame_start": 1,
    "frame_end": 120,
    "frame_count": 120,
    "render_engine": "BLENDER_EEVEE",
    "eevee_render_samples": render_samples,
    "benchmark_variant": benchmark_samples is not None,
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
    scene_setup_started = __import__("time").monotonic()
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
    if not hasattr(scene, "eevee") or not hasattr(scene.eevee, "taa_render_samples"):
        raise RuntimeError("The selected Blender runtime does not expose EEVEE TAA samples.")
    scene.eevee.taa_render_samples = render_samples
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
    scene_report["physics_settings"] = {
        "gravity": [float(value) for value in scene.gravity],
        "time_scale": world.time_scale,
        "substeps_per_frame": world.substeps_per_frame,
        "solver_iterations": world.solver_iterations,
        "cache_frame_start": world.point_cache.frame_start,
        "cache_frame_end": world.point_cache.frame_end,
    }

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

    scene_report["scene_setup_seconds"] = round(
        __import__("time").monotonic() - scene_setup_started, 6
    )
    output_basename = (
        f"satisfying_physics_test_samples_{render_samples:02d}"
        if benchmark_samples is not None
        else "satisfying_physics_test"
    )
    scene.render.filepath = str(output / output_basename)
    scene_report["render"]["samples"] = render_samples
    scene_report["render"]["output_basename"] = str(output / output_basename)
    scene_report["render"]["expected_video_pattern"] = f"{output_basename}*.mp4"
    scene.frame_set(1)
    save_report()
    render_started = __import__("time").monotonic()
    try:
        bpy.ops.render.render(animation=True)
        scene_report["render"] = {
            "status": "COMPLETED",
            "output_basename": str(output / output_basename),
            "expected_video_pattern": f"{output_basename}*.mp4",
            "duration_seconds": round(__import__("time").monotonic() - render_started, 3),
            "render_includes_mp4_write_finalize": True,
            "mp4_write_finalize_seconds": None,
            "resolution": [scene.render.resolution_x, scene.render.resolution_y],
            "fps": scene.render.fps,
            "frame_count": scene.frame_end - scene.frame_start + 1,
            "samples": render_samples,
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


def run_eevee_sample_benchmark(blender, environment, scene_script, ffmpeg, ffprobe):
    benchmark_started = time.monotonic()
    benchmark_root = OUTPUT / "eevee-sample-benchmark"
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_root = benchmark_root / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    benchmark = {
        "status": "RUNNING",
        "run_id": run_id,
        "sample_counts": [8, 4, 2],
        "kernel_v8_baseline": {
            "runner_elapsed_seconds": 501.796,
            "render_and_mp4_write_seconds": 412.36,
            "resolution": [720, 1280],
            "fps": 24,
            "frame_count": 120,
            "eevee_samples": 8,
            "source": "performance-run-v8-summary.json",
        },
        "blender_version_check_seconds": report["stages"]
        .get("blender_version", {})
        .get("duration_seconds"),
        "scene_script_sha256": sha256_file(scene_script),
        "fixed_settings": {
            "render_engine": "BLENDER_EEVEE",
            "resolution": [720, 1280],
            "resolution_percentage": 100,
            "fps": 24,
            "frame_start": 1,
            "frame_end": 120,
            "frame_count": 120,
            "gtao_enabled": True,
            "gtao_distance": 3,
            "gtao_factor": 1.25,
            "physics_and_motion": "unchanged deterministic keyframed rigid-body choreography",
            "output_codec": "H.264 in MP4",
        },
        "results": [],
        "visual_review": {
            "status": "PENDING_MANUAL_REVIEW",
            "comparison_image": None,
            "frame_indices_zero_based": [0, 59, 119],
            "sample_order_top_to_bottom": [8, 4, 2],
            "assessment_fields": ["noise", "fine_details", "shadows", "edges"],
        },
    }

    for samples in benchmark["sample_counts"]:
        sample_started = time.monotonic()
        sample_dir = run_root / f"samples-{samples:02d}"
        sample_dir.mkdir()
        scene_report_path = sample_dir / "scene_report.json"
        blender_stage = run_command(
            f"benchmark_eevee_samples_{samples:02d}",
            [
                blender,
                "--background",
                "--python",
                str(scene_script),
                "--",
                str(sample_dir),
                str(samples),
            ],
            timeout=1500,
            extra_env=environment,
        )
        result = {
            "samples": samples,
            "status": "FAILED",
            "output_directory": str(sample_dir.relative_to(OUTPUT)),
            "blender_process": blender_stage,
            "scene_setup_seconds": None,
            "render_and_mp4_write_seconds": None,
            "mp4_write_finalize_only_seconds": None,
        }
        if scene_report_path.is_file():
            try:
                scene_data = json.loads(scene_report_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                result["scene_report_error"] = f"{type(exc).__name__}: {exc}"
                scene_data = None
            result["scene_report"] = scene_data
        else:
            scene_data = None
            result["scene_report_error"] = "Blender did not create scene_report.json."

        expected_video_stem = f"satisfying_physics_test_samples_{samples:02d}"
        candidate_videos = sorted(sample_dir.glob(f"{expected_video_stem}*.mp4"))
        video_path = candidate_videos[0] if len(candidate_videos) == 1 else None
        render_record = scene_data.get("render", {}) if scene_data else {}
        result["scene_setup_seconds"] = (
            scene_data.get("scene_setup_seconds") if scene_data else None
        )
        result["render_and_mp4_write_seconds"] = render_record.get("duration_seconds")
        result["video_path"] = (
            str(video_path.relative_to(OUTPUT)) if video_path is not None else None
        )
        if (
            blender_stage["status"] != "COMPLETED"
            or render_record.get("status") != "COMPLETED"
            or scene_data is None
            or scene_data.get("eevee_render_samples") != samples
            or render_record.get("samples") != samples
            or scene_data.get("resolution") != [720, 1280]
            or scene_data.get("fps") != 24
            or scene_data.get("frame_count") != 120
            or scene_data.get("motion", {}).get("status") != "COMPLETED"
            or video_path is None
            or not video_path.is_file()
            or video_path.stat().st_size == 0
        ):
            result["error"] = (
                "Render, fixed settings, scene motion, or unique MP4 validation failed."
            )
            result["candidate_videos"] = [
                str(path.relative_to(OUTPUT)) for path in candidate_videos
            ]
            result["elapsed_seconds"] = round(time.monotonic() - sample_started, 6)
            benchmark["results"].append(result)
            continue

        probe = run_command(
            f"benchmark_ffprobe_samples_{samples:02d}",
            [
                ffprobe,
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries",
                "stream=codec_name,profile,width,height,r_frame_rate,avg_frame_rate,nb_frames,duration:format=duration,size",
                "-of", "json",
                str(video_path),
            ],
            120,
        )
        probe_data = None
        if probe["status"] == "COMPLETED":
            try:
                raw = probe["output_tail"]
                probe_data = json.loads(raw[raw.find("{"):])
            except (ValueError, json.JSONDecodeError):
                probe_data = None
        streams = probe_data.get("streams", []) if probe_data else []
        stream = streams[0] if streams else {}
        duration = float(
            stream.get("duration")
            or probe_data.get("format", {}).get("duration", 0)
        )
        frame_rate = stream.get("avg_frame_rate")
        metadata_valid = (
            stream.get("codec_name") == "h264"
            and (stream.get("width"), stream.get("height")) == (720, 1280)
            and frame_rate in ("24/1", "24/1.000")
            and stream.get("nb_frames") == "120"
            and 4.95 <= duration <= 5.05
        )
        result["ffprobe"] = {
            "status": "COMPLETED" if metadata_valid else "FAILED",
            "duration_seconds": probe.get("duration_seconds"),
            "metadata": probe_data,
            "checks_passed": metadata_valid,
        }

        decode = run_command(
            f"benchmark_ffmpeg_decode_samples_{samples:02d}",
            [ffmpeg, "-v", "error", "-i", str(video_path), "-f", "null", "-"],
            300,
        )
        result["full_decode"] = {
            "status": decode["status"],
            "duration_seconds": decode.get("duration_seconds"),
            "log": decode.get("log"),
        }

        contact_path = sample_dir / "frames-001-060-120.png"
        contact = run_command(
            f"benchmark_contact_samples_{samples:02d}",
            [
                ffmpeg, "-y", "-i", str(video_path),
                "-vf",
                "select='eq(n,0)+eq(n,59)+eq(n,119)',scale=720:1280:flags=lanczos,tile=3x1",
                "-frames:v", "1", str(contact_path),
            ],
            180,
        )
        result["contact_sheet"] = {
            "status": (
                "COMPLETED"
                if contact["status"] == "COMPLETED"
                and contact_path.is_file()
                and contact_path.stat().st_size > 0
                else "FAILED"
            ),
            "path": str(contact_path.relative_to(OUTPUT)),
            "duration_seconds": contact.get("duration_seconds"),
        }

        motion_started = time.monotonic()
        motion_command = [
            ffmpeg, "-v", "error", "-i", str(video_path),
            "-vf", "select='eq(n,0)+eq(n,59)+eq(n,119)',scale=64:114",
            "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ]
        try:
            motion_run = subprocess.run(
                motion_command,
                capture_output=True,
                timeout=120,
                check=False,
            )
            frame_size = 64 * 114 * 3
            raw = motion_run.stdout
            frame_count = len(raw) // frame_size
            differences = []
            for index in range(max(0, frame_count - 1)):
                left = raw[index * frame_size:(index + 1) * frame_size]
                right = raw[(index + 1) * frame_size:(index + 2) * frame_size]
                differences.append(
                    sum(abs(a - b) for a, b in zip(left, right)) / frame_size
                )
            motion_status = (
                "COMPLETED"
                if motion_run.returncode == 0
                and frame_count == 3
                and differences
                and max(differences) > 3.0
                else "FAILED"
            )
            result["visible_motion"] = {
                "status": motion_status,
                "frames_decoded": frame_count,
                "mean_absolute_rgb_difference": differences,
                "threshold": 3.0,
                "duration_seconds": round(time.monotonic() - motion_started, 6),
                "stderr_tail": motion_run.stderr.decode(errors="replace")[-2000:],
            }
        except (OSError, subprocess.TimeoutExpired) as exc:
            result["visible_motion"] = {
                "status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}",
                "duration_seconds": round(time.monotonic() - motion_started, 6),
            }

        hash_started = time.monotonic()
        result["video"] = {
            "size_bytes": video_path.stat().st_size,
            "sha256": sha256_file(video_path),
            "hash_duration_seconds": round(time.monotonic() - hash_started, 6),
        }
        result["status"] = (
            "COMPLETED"
            if result["ffprobe"]["status"] == "COMPLETED"
            and result["full_decode"]["status"] == "COMPLETED"
            and result["contact_sheet"]["status"] == "COMPLETED"
            and result["visible_motion"]["status"] == "COMPLETED"
            else "FAILED"
        )
        result["elapsed_seconds"] = round(time.monotonic() - sample_started, 6)
        benchmark["results"].append(result)

    complete_contacts = [
        OUTPUT / item["contact_sheet"]["path"]
        for item in benchmark["results"]
        if item.get("contact_sheet", {}).get("status") == "COMPLETED"
    ]
    comparison_path = run_root / "samples-08-04-02-comparison.png"
    if len(complete_contacts) == len(benchmark["sample_counts"]):
        comparison = run_command(
            "benchmark_sample_contact_sheet_compare",
            [
                ffmpeg, "-y",
                "-i", str(complete_contacts[0]),
                "-i", str(complete_contacts[1]),
                "-i", str(complete_contacts[2]),
                "-filter_complex", "[0:v][1:v][2:v]vstack=inputs=3[v]",
                "-map", "[v]",
                str(comparison_path),
            ],
            180,
        )
        benchmark["visual_review"]["comparison_image"] = {
            "path": str(comparison_path.relative_to(OUTPUT)),
            "status": (
                "READY_FOR_MANUAL_REVIEW"
                if comparison["status"] == "COMPLETED"
                and comparison_path.is_file()
                and comparison_path.stat().st_size > 0
                else "FAILED"
            ),
            "size_bytes": comparison_path.stat().st_size if comparison_path.is_file() else 0,
            "sha256": sha256_file(comparison_path) if comparison_path.is_file() else None,
        }
    else:
        benchmark["visual_review"]["comparison_image"] = {
            "status": "FAILED",
            "reason": "At least one per-sample contact sheet was not generated.",
        }

    reference = next(
        (item for item in benchmark["results"] if item["samples"] == 8),
        None,
    )
    reference_scene = reference.get("scene_report") if reference else None
    for item in benchmark["results"]:
        scene_data = item.get("scene_report")
        item["scene_equivalent_to_8_samples"] = bool(
            reference_scene
            and scene_data
            and scene_data.get("motion_mode") == reference_scene.get("motion_mode")
            and scene_data.get("motion_samples") == reference_scene.get("motion_samples")
            and scene_data.get("physics_settings") == reference_scene.get("physics_settings")
            and scene_data.get("motion") == reference_scene.get("motion")
        )
        if item.get("status") == "COMPLETED" and not item["scene_equivalent_to_8_samples"]:
            item["status"] = "FAILED"
            item["error"] = "Scene motion/physics differs from the 8-sample reference."
    reference_render_seconds = (
        reference.get("render_and_mp4_write_seconds")
        if reference and reference.get("status") == "COMPLETED"
        else None
    )
    for item in benchmark["results"]:
        current = item.get("render_and_mp4_write_seconds")
        item["time_change_vs_8_sample_percent"] = (
            round((reference_render_seconds - current) / reference_render_seconds * 100, 3)
            if reference_render_seconds and current is not None
            else None
        )
        item["total_time_change_vs_8_sample_percent"] = (
            round(
                (reference["elapsed_seconds"] - item["elapsed_seconds"])
                / reference["elapsed_seconds"] * 100,
                3,
            )
            if reference
            and reference.get("elapsed_seconds")
            and item.get("elapsed_seconds") is not None
            else None
        )
    benchmark["status"] = (
        "COMPLETED"
        if len(benchmark["results"]) == 3
        and all(item["status"] == "COMPLETED" for item in benchmark["results"])
        and benchmark["visual_review"]["comparison_image"]["status"]
        == "READY_FOR_MANUAL_REVIEW"
        else "FAILED"
    )
    benchmark["elapsed_seconds"] = round(time.monotonic() - benchmark_started, 6)
    benchmark["restore_audit"] = {
        "first_call": report["stages"].get("blender_dataset_restore"),
        "second_call": report["stages"].get("blender_restore_reuse_check"),
        "optimization_applied": False,
        "note": "Archive, manifest, and tree verification were not reduced or bypassed in this benchmark.",
    }
    report["eevee_sample_benchmark"] = benchmark
    report["overall_status"] = benchmark["status"]
    report["completed_utc"] = datetime.now(timezone.utc).isoformat()
    report["elapsed_seconds"] = round(time.monotonic() - total_started, 3)
    for path in sorted(OUTPUT.rglob("*")):
        if path.is_file():
            report["artifacts"].append({
                "name": str(path.relative_to(OUTPUT)),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })
    write_json(run_root / "eevee-sample-benchmark-report.json", report)
    write_json(REPORT_PATH, report)
    print("EEVEE sample benchmark status:", benchmark["status"])
    print("Benchmark report:", run_root / "eevee-sample-benchmark-report.json")
    print("Benchmark elapsed seconds:", benchmark["elapsed_seconds"])
    for item in benchmark["results"]:
        print(
            "Samples:",
            item["samples"],
            "status:",
            item["status"],
            "render+MP4 seconds:",
            item.get("render_and_mp4_write_seconds"),
            "video bytes:",
            item.get("video", {}).get("size_bytes"),
        )
    return 0 if benchmark["status"] == "COMPLETED" else 1


def main():
    print("AI-Engine first vertical Short export")
    print("Timestamp UTC:", report["started_utc"])
    print("Python:", sys.version.replace("\n", " "))
    print("Runtime:", platform.platform(), platform.machine())
    print("Kaggle run type:", os.environ.get("KAGGLE_KERNEL_RUN_TYPE", "not reported"))
    print("Accelerator inventory: GPU query", "available" if shutil.which("nvidia-smi") else "no nvidia-smi")
    print("TPU devices:", [str(path) for path in Path("/dev").glob("accel*")])
    restore_audit_setting = os.environ.get("AI_ENGINE_RESTORE_AUDIT_ONLY", "0")
    if restore_audit_setting not in ("0", "1"):
        raise ValueError(
            "AI_ENGINE_RESTORE_AUDIT_ONLY must be '0' (normal production path) or '1'."
        )
    try:
        runtime = restore_blender_runtime()
    except (
        OSError,
        RuntimeError,
        ValueError,
        UnicodeError,
        tarfile.TarError,
        KeyError,
        StopIteration,
    ) as exc:
        report["stages"]["blender_dataset_restore"] = {
            "status": "FAILED",
            "error": f"{type(exc).__name__}: {exc}",
        }
        report["overall_status"] = "FAILED"
        report["completed_utc"] = datetime.now(timezone.utc).isoformat()
        report["elapsed_seconds"] = round(time.monotonic() - total_started, 3)
        write_json(REPORT_PATH, report)
        print("Overall status: FAILED; Blender Dataset restoration/verification failed.")
        print(report["stages"]["blender_dataset_restore"]["error"])
        return 2

    report["stages"]["blender_dataset_restore"] = runtime["report"]
    report["blender_executable"] = runtime["blender"]
    if restore_audit_setting == "1":
        try:
            cache_hit = restore_blender_runtime()
            if (
                cache_hit["report"]["mode"] != "REUSED_VERIFIED"
                or cache_hit["blender"] != runtime["blender"]
            ):
                raise RuntimeError(
                    "The second restore audit call did not verify the restored cache."
                )
            report["stages"]["blender_restore_cache_hit"] = cache_hit["report"]
            baseline = {
                "cache_miss": {
                    "input_discovery_seconds": 0.350755,
                    "archive_sha256_seconds": 2.535602,
                    "manifest_sha256_seconds": 0.123913,
                    "manifest_validation_seconds": 0.016180,
                    "extraction_seconds": 38.527290,
                    "inventory_seconds": 6.569376,
                    "total_seconds": 48.125665,
                },
                "cache_hit": {
                    "input_discovery_seconds": 0.002783,
                    "archive_sha256_seconds": 1.270861,
                    "manifest_sha256_seconds": 0.006583,
                    "manifest_validation_seconds": 0.014273,
                    "extraction_seconds": 0.0,
                    "inventory_seconds": 13.057455,
                    "total_seconds": 14.485559,
                },
                "source": "Kaggle v10 run 360710783, benchmark 20261021T083149Z",
            }
            current_restore_timings = {
                "cache_miss": runtime["report"],
                "cache_hit": cache_hit["report"],
            }
            timing_fields = tuple(baseline["cache_miss"])
            report["restore_cache_comparison"] = {
                "baseline": baseline,
                "current": current_restore_timings,
                "delta_seconds_current_minus_v10": {
                    cache_state: {
                        field: round(
                            current_restore_timings[cache_state][field]
                            - baseline[cache_state][field],
                            6,
                        )
                        for field in timing_fields
                    }
                    for cache_state in ("cache_miss", "cache_hit")
                },
                "cache_hit_duplicate_full_hash_scan_removed": True,
                "normal_run_second_restore_call_removed": True,
            }
            audit_status = (
                runtime["report"]["cache_status"] == "MISS_RESTORED"
                and cache_hit["report"]["cache_status"] == "HIT_REUSED"
                and runtime["report"]["status"] == "VERIFIED"
                and cache_hit["report"]["status"] == "VERIFIED"
            )
            report["restore_cache_comparison"]["status"] = (
                "COMPLETED" if audit_status else "FAILED"
            )
            report["overall_status"] = (
                "COMPLETED" if audit_status else "FAILED"
            )
        except (
            OSError,
            RuntimeError,
            ValueError,
            UnicodeError,
            tarfile.TarError,
            KeyError,
            StopIteration,
        ) as exc:
            report["restore_cache_comparison"] = {
                "status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}",
            }
            report["overall_status"] = "FAILED"
        report["completed_utc"] = datetime.now(timezone.utc).isoformat()
        report["elapsed_seconds"] = round(time.monotonic() - total_started, 3)
        write_json(REPORT_PATH, report)
        print("Restore cache audit status:", report["overall_status"])
        print("Restore audit report:", REPORT_PATH)
        return 0 if report["overall_status"] == "COMPLETED" else 2

    blender = runtime["blender"]
    blender_environment = runtime["environment"]
    if not verify_blender_runtime(blender, blender_environment):
        report["overall_status"] = "FAILED"
        report["completed_utc"] = datetime.now(timezone.utc).isoformat()
        report["elapsed_seconds"] = round(time.monotonic() - total_started, 3)
        write_json(REPORT_PATH, report)
        print("Overall status: FAILED; Blender runtime smoke checks did not pass.")
        return 2

    video_tools_started = time.monotonic()
    ffmpeg, ffprobe = install_remote_video_tools_if_needed()
    report["stages"]["video_tools_prepare"] = {
        "status": "COMPLETED" if ffmpeg and ffprobe else "FAILED",
        "duration_seconds": round(time.monotonic() - video_tools_started, 6),
        "ffmpeg_available": bool(ffmpeg),
        "ffprobe_available": bool(ffprobe),
    }
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

    scene_script = OUTPUT / "short_scene.py"
    scene_script.write_text(SCENE_SCRIPT, encoding="utf-8")
    report["scene_source"] = scene_script.name
    benchmark_setting = os.environ.get("AI_ENGINE_EEVEE_SAMPLE_BENCHMARK", "0")
    if benchmark_setting not in ("0", "1"):
        raise ValueError(
            "AI_ENGINE_EEVEE_SAMPLE_BENCHMARK must be '0' (production default) or '1'."
        )
    if benchmark_setting == "1":
        print("Benchmark mode enabled; production default remains 8 EEVEE samples.")
        return run_eevee_sample_benchmark(
            blender,
            blender_environment,
            scene_script,
            ffmpeg,
            ffprobe,
        )
    existing_video_states = {
        path.resolve(): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in OUTPUT.glob("satisfying_physics_test*.mp4")
        if path.is_file()
    }
    blender_stage = run_command(
        "blender_short_render",
        [blender, "--background", "--python", str(scene_script), "--", str(OUTPUT)],
        timeout=1500,
        extra_env=blender_environment,
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
                "ffprobe_duration_seconds": probe.get("duration_seconds"),
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

    video_hash_started = time.monotonic()
    report["video"] = {
        "path": str(video) if video is not None else None,
        "size_bytes": video.stat().st_size if video is not None else 0,
        "sha256": sha256_file(video) if video is not None else None,
        "hash_duration_seconds": None,
    }
    report["video"]["hash_duration_seconds"] = round(
        time.monotonic() - video_hash_started, 6
    )
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
    report["comparison"] = {
        "baseline_kernel_version": KERNEL_V7_BASELINE["kernel_version"],
        "baseline_kaggle_run_id": KERNEL_V7_BASELINE["kaggle_run_id"],
        "baseline_elapsed_seconds": KERNEL_V7_BASELINE["elapsed_seconds"],
        "current_elapsed_seconds": report["elapsed_seconds"],
        "elapsed_seconds_delta_baseline_minus_current": round(
            KERNEL_V7_BASELINE["elapsed_seconds"] - report["elapsed_seconds"], 3
        ),
        "elapsed_percent_change": round(
            (
                (KERNEL_V7_BASELINE["elapsed_seconds"] - report["elapsed_seconds"])
                / KERNEL_V7_BASELINE["elapsed_seconds"]
            ) * 100,
            3,
        ),
        "baseline_mp4_bytes": KERNEL_V7_BASELINE["mp4_size_bytes"],
        "current_mp4_bytes": report["video"]["size_bytes"],
        "baseline_mp4_sha256": KERNEL_V7_BASELINE["mp4_sha256"],
        "current_mp4_sha256": report["video"]["sha256"],
        "baseline_video": {
            key: KERNEL_V7_BASELINE[key]
            for key in ("codec", "resolution", "fps", "frame_count", "duration_seconds")
        },
        "current_video": report.get("video_metadata"),
        "baseline_stage_times": "N/A; no per-stage timings were retrieved for Kernel v7",
        "current_cache_status": report["stages"]
        .get("blender_dataset_restore", {})
        .get("cache_status"),
        "comparability_notes": [
            "Kernel v7 was the production CPU-only run; this measured run uses the unchanged scene and 720x1280, 24 FPS, 120-frame settings.",
            "Kernel v7 internal elapsed time is 583.558 seconds; its Kaggle UI separately displayed a 604.6-second run. Do not mix those timing sources.",
            "Kernel v7 per-stage report retrieval was rate-limited (HTTP 429), so unmatched stages are N/A.",
            "The run-v4 restore measurements are from a distinct restore/runtime verification and are not a Kernel v7 stage baseline.",
        ],
    }
    restore_stages = report["stages"].get("blender_dataset_restore", {})
    scene_timing = report.get("scene", {})
    report["timing_summary_seconds"] = {
        "input_discovery": restore_stages.get("input_discovery_seconds"),
        "archive_sha256": restore_stages.get("archive_sha256_seconds"),
        "manifest_sha256": restore_stages.get("manifest_sha256_seconds"),
        "manifest_validation": restore_stages.get("manifest_validation_seconds"),
        "archive_extraction": restore_stages.get("extraction_seconds"),
        "restored_tree_validation_and_hashes": restore_stages.get("inventory_seconds"),
        "restore_function_total": restore_stages.get("total_seconds"),
        "restore_cache_status": restore_stages.get("cache_status"),
        "blender_version_subprocess_including_startup": report["stages"]
        .get("blender_version", {})
        .get("duration_seconds"),
        "embedded_python_subprocess_including_startup": report["stages"]
        .get("blender_embedded_python", {})
        .get("duration_seconds"),
        "eevee_and_physics_smoke_subprocess": report["stages"]
        .get("blender_eevee_physics_smoke", {})
        .get("duration_seconds"),
        "eevee_smoke_render": report["stages"]
        .get("blender_eevee_physics_smoke", {})
        .get("eevee_render_seconds"),
        "physics_smoke_simulation": report["stages"]
        .get("blender_eevee_physics_smoke", {})
        .get("physics_seconds"),
        "video_tools_prepare": report["stages"]
        .get("video_tools_prepare", {})
        .get("duration_seconds"),
        "short_scene_setup": scene_timing.get("scene_setup_seconds"),
        "short_render_and_mp4_write_finalize": scene_timing.get("render", {}).get(
            "duration_seconds"
        ),
        "mp4_write_finalize_only": None,
        "ffprobe": report["stages"].get("video_probe", {}).get(
            "ffprobe_duration_seconds"
        ),
        "full_video_decode": report["stages"].get("full_video_decode", {}).get(
            "duration_seconds"
        ),
        "contact_sheet_extraction": report["stages"].get("contact_sheet", {}).get(
            "duration_seconds"
        ),
        "visible_motion_validation": report["stages"]
        .get("visible_motion_check", {})
        .get("duration_seconds"),
        "mp4_sha256": report["video"].get("hash_duration_seconds"),
        "task_total": report["elapsed_seconds"],
        "non_additivity_note": "Subprocess totals include nested stage times; MP4 encoding/finalization occurs inside Blender render and is not independently separable from rendering.",
    }
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
