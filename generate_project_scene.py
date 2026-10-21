from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ai_engine.project_store import ProjectStore
from ai_engine.scene_generation import SavedProjectSceneGenerator
from ai_engine.project_service import default_projects_directory


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a Blender scene from a project saved through the local UI."
    )
    parser.add_argument("project_id", help="Canonical UUID shown in the project editor.")
    parser.add_argument(
        "--blender",
        required=True,
        help="Path to a Blender 4.0.2 executable, or its executable name on PATH.",
    )
    parser.add_argument(
        "--projects-dir",
        type=Path,
        default=default_projects_directory(Path(__file__).resolve().parent),
    )
    parser.add_argument("--output", type=Path, help="Optional .blend path inside projects-dir.")
    parser.add_argument("--timeout", type=int, default=600, help="Scene-build timeout in seconds.")
    arguments = parser.parse_args()

    try:
        generator = SavedProjectSceneGenerator(
            ProjectStore(arguments.projects_dir),
            arguments.blender,
            timeout_seconds=arguments.timeout,
        )
        result = generator.generate(arguments.project_id, arguments.output)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Scene generation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Scene created: {result.blend_file}")
    print(f"Scene report: {result.report_file}")
    print(
        f"Blender {result.blender_version} | EEVEE | "
        f"{result.scene_plan.resolution_x}x{result.scene_plan.resolution_y} "
        f"@ {result.scene_plan.fps} FPS | {result.scene_plan.eevee_samples} samples"
    )
    print("Physics simulation and rendering were not run; render device is unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
