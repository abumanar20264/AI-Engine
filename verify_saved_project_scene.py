from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ai_engine.project_service import default_projects_directory
from ai_engine.project_store import ProjectStore
from ai_engine.scene_integration import run_saved_project_scene_integration


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build, reopen, and run a bounded rigid-body motion check for a saved project "
            "using Blender 4.0.2; no video render is performed."
        )
    )
    parser.add_argument("project_id", help="UUID of a project already saved through ProjectStore.")
    parser.add_argument("--blender", required=True, help="Blender 4.0.2 executable.")
    parser.add_argument(
        "--projects-dir",
        type=Path,
        default=default_projects_directory(Path(__file__).resolve().parent),
    )
    parser.add_argument("--timeout", type=int, default=600)
    arguments = parser.parse_args()
    try:
        report = run_saved_project_scene_integration(
            ProjectStore(arguments.projects_dir),
            arguments.blender,
            arguments.project_id,
            arguments.timeout,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Integration test setup failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
