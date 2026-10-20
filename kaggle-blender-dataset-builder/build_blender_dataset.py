import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import tarfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


VERSION = "4.0.2"
ARCHIVE_NAME = f"blender-{VERSION}-linux-x64.tar.xz"
BASE_URL = "https://download.blender.org/release/Blender4.0"
ARCHIVE_URL = f"{BASE_URL}/{ARCHIVE_NAME}"
CHECKSUM_URL = f"{BASE_URL}/blender-{VERSION}.sha256"
WORKING = Path("/kaggle/working")
TEMP = Path("/kaggle/temp/ai-engine-blender-dataset-builder")
INSTALL_ROOT = WORKING / ARCHIVE_NAME.removesuffix(".tar.xz")
REPORT_PATH = WORKING / "blender_dataset_build_report.json"
EXPECTED_SHA256 = "5583a5588736da8858c522ef17fff5d73be59c47a6fe91ad29c6f3263e22086a"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url, destination):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AI-Engine-Blender-Dataset-Builder/1.0"},
    )
    with urllib.request.urlopen(request, timeout=90) as response, destination.open("wb") as target:
        shutil.copyfileobj(response, target)


def run_stage(command, timeout):
    started = time.monotonic()
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
        check=False,
        env=os.environ.copy(),
    )
    return {
        "exit_code": result.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "stdout": result.stdout[-3000:],
        "stderr": result.stderr[-3000:],
    }


def summarize_tree(root):
    summary = {
        "file_count": 0,
        "directory_count": 0,
        "symlink_count": 0,
        "regular_file_bytes": 0,
        "symlinks": [],
        "top_level": {},
    }
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        directories.sort()
        for name in list(directories):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                directories.remove(name)
                summary["symlink_count"] += 1
                summary["symlinks"].append(
                    {"path": relative, "target": os.readlink(path)}
                )
            else:
                summary["directory_count"] += 1
                first = relative.split("/", 1)[0]
                entry = summary["top_level"].setdefault(
                    first,
                    {"file_count": 0, "directory_count": 0, "symlink_count": 0, "bytes": 0},
                )
                entry["directory_count"] += 1
        for name in files:
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                summary["symlink_count"] += 1
                summary["symlinks"].append(
                    {"path": relative, "target": os.readlink(path)}
                )
                continue
            size = path.stat().st_size
            summary["file_count"] += 1
            summary["regular_file_bytes"] += size
            first = relative.split("/", 1)[0]
            entry =             summary["top_level"].setdefault(
                first,
                {"file_count": 0, "directory_count": 0, "symlink_count": 0, "bytes": 0},
            )
            entry["file_count"] += 1
            entry["bytes"] += size
    for link in summary["symlinks"]:
        first = link["path"].split("/", 1)[0]
        entry = summary["top_level"].setdefault(
            first,
            {"file_count": 0, "directory_count": 0, "symlink_count": 0, "bytes": 0},
        )
        entry["symlink_count"] += 1
    return summary


def main():
    started_utc = utc_now()
    started = time.monotonic()
    TEMP.mkdir(parents=True, exist_ok=True)
    archive_path = TEMP / ARCHIVE_NAME
    report = {
        "status": "FAILED",
        "version": VERSION,
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "started_utc": started_utc,
        "source": ARCHIVE_URL,
        "checksum_source": CHECKSUM_URL,
        "expected_sha256": EXPECTED_SHA256,
        "output_directory": str(INSTALL_ROOT),
        "stages": {},
    }
    try:
        disk = shutil.disk_usage(WORKING)
        report["working_disk_before_bytes"] = {
            "free": disk.free,
            "total": disk.total,
        }
        if platform.machine().lower() not in ("x86_64", "amd64"):
            raise RuntimeError(f"Unsupported architecture: {platform.machine()}")
        if disk.free < 3 * 1024**3:
            raise RuntimeError(f"At least 3 GiB free space is required; found {disk.free} bytes.")

        download_start = time.monotonic()
        download(ARCHIVE_URL, archive_path)
        report["stages"]["archive_download"] = {
            "status": "COMPLETED",
            "duration_seconds": round(time.monotonic() - download_start, 3),
            "size_bytes": archive_path.stat().st_size,
            "sha256": sha256_file(archive_path),
        }

        checksum_path = TEMP / "blender-4.0.2.sha256"
        checksum_start = time.monotonic()
        download(CHECKSUM_URL, checksum_path)
        checksum_lines = checksum_path.read_text(encoding="ascii").splitlines()
        published = next(
            (
                line.split()[0].lower()
                for line in checksum_lines
                if len(line.split()) >= 2 and Path(line.split()[-1]).name == ARCHIVE_NAME
            ),
            None,
        )
        local_digest = report["stages"]["archive_download"]["sha256"]
        if published != EXPECTED_SHA256:
            raise RuntimeError(f"Official checksum list mismatch: {published!r}")
        if local_digest != published:
            raise RuntimeError(
                f"Archive SHA-256 mismatch: expected {published}, received {local_digest}"
            )
        report["stages"]["checksum_verification"] = {
            "status": "COMPLETED",
            "duration_seconds": round(time.monotonic() - checksum_start, 3),
            "published_sha256": published,
            "local_sha256": local_digest,
        }

        extract_start = time.monotonic()
        if INSTALL_ROOT.exists():
            raise FileExistsError(f"Refusing to overwrite existing output: {INSTALL_ROOT}")
        with tarfile.open(archive_path, mode="r:xz") as archive:
            archive.extractall(path=WORKING, filter="data")
        blender = INSTALL_ROOT / "blender"
        if not blender.is_file():
            raise FileNotFoundError(f"Expected Blender executable missing: {blender}")
        if not (blender.stat().st_mode & stat.S_IXUSR):
            raise PermissionError(f"Blender executable bit missing: {blender}")
        if not (INSTALL_ROOT / "4.0" / "datafiles").is_dir():
            raise FileNotFoundError("Expected Blender 4.0 datafiles folder is missing.")
        report["stages"]["archive_extraction"] = {
            "status": "COMPLETED",
            "duration_seconds": round(time.monotonic() - extract_start, 3),
            "blender_executable": str(blender),
            "executable_mode": oct(blender.stat().st_mode & 0o777),
            "blender_executable_size_bytes": blender.stat().st_size,
            "blender_executable_sha256": sha256_file(blender),
        }
        report["extracted_tree_inventory"] = summarize_tree(INSTALL_ROOT)

        version_check = run_stage([str(blender), "--background", "--version"], 60)
        report["stages"]["blender_version"] = version_check
        if version_check["exit_code"] != 0 or "Blender 4.0.2" not in version_check["stdout"]:
            raise RuntimeError("Extracted Blender did not report the expected 4.0.2 version.")

        disk_after = shutil.disk_usage(WORKING)
        report["working_disk_after_bytes"] = {
            "free": disk_after.free,
            "total": disk_after.total,
        }
        report["status"] = "COMPLETED"
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if archive_path.exists():
            archive_path.unlink()
        if TEMP.exists():
            shutil.rmtree(TEMP)
        report["temporary_archive_removed"] = not archive_path.exists()
        report["temporary_directory_removed"] = not TEMP.exists()
        report["completed_utc"] = utc_now()
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
