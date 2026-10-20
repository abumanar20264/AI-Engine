import hashlib
import json
import os
import subprocess
import stat
import time
from pathlib import Path


INPUT_ROOT = Path("/kaggle/input")

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    matches = list(INPUT_ROOT.glob("**/ai-engine-kaggle-tree-probe/manifest.json"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one mounted fixture manifest; found {len(matches)}.")
    root = matches[0].parent
    started = time.monotonic()
    results = {}
    manifest = json.loads(matches[0].read_text(encoding="utf-8"))
    expected_files = manifest["files"] + manifest["many_files"]
    for expected in expected_files:
        relative = expected["path"]
        path = root / relative
        results[relative] = {
            "exists": path.is_file(),
            "sha256": sha256(path) if path.is_file() else None,
            "mode": oct(stat.S_IMODE(path.stat().st_mode)) if path.exists() else None,
            "sha256_matches": path.is_file() and sha256(path) == expected["sha256"],
        }

    link_path = manifest["symlinks"][0]["path"]
    link_target = manifest["symlinks"][0]["target"]
    link = root / link_path
    symlink_result = {
        "exists": link.exists(),
        "is_symlink": link.is_symlink(),
        "target": os.readlink(link) if link.is_symlink() else None,
        "expected_target": link_target,
    }

    executable = root / "bin" / "probe.sh"
    executable_result = {
        "exists": executable.is_file(),
        "mode": oct(stat.S_IMODE(executable.stat().st_mode)) if executable.exists() else None,
        "chmod_to_755": None,
        "direct_execution": None,
    }
    if executable.is_file():
        try:
            original_mode = stat.S_IMODE(executable.stat().st_mode)
            try:
                executable.chmod(0o755)
                executable_result["chmod_to_755"] = "SUCCEEDED"
            except OSError as error:
                executable_result["chmod_to_755"] = f"{type(error).__name__}: {error}"
            completed = subprocess.run(
                [str(executable)],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            executable_result["direct_execution"] = {
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        except OSError as error:
            executable_result["direct_execution"] = {
                "error": f"{type(error).__name__}: {error}"
            }
        finally:
            if executable_result["chmod_to_755"] == "SUCCEEDED":
                executable.chmod(original_mode)

    regular_file_count = sum(
        len(files)
        for _, _, files in os.walk(root, followlinks=False)
    )
    expected_file_count = 1 + len(expected_files)
    hash_matches = sum(result["sha256_matches"] for result in results.values())
    print(
        json.dumps(
            {
                "dataset_mount_root": str(root),
                "elapsed_seconds": round(time.monotonic() - started, 6),
                "regular_file_count": regular_file_count,
                "expected_regular_file_count": expected_file_count,
                "expected_content_file_count": len(expected_files),
                "sha256_matches": hash_matches,
                "sha256_mismatches": len(results) - hash_matches,
                "files": results,
                "symlink": symlink_result,
                "executable": executable_result,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
