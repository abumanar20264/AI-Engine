from __future__ import annotations

import json
import importlib.util
import sys
import tempfile
import unittest
from types import FunctionType
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ai_engine.project_store import ProjectStore, create_project
from ai_engine.scene_generation import (
    SavedProjectSceneGenerator,
    SceneGenerationError,
    scene_report_from_file,
)
from ai_engine.scene_integration import (
    run_saved_project_scene_integration,
    validate_verification_report,
)

KAGGLE_INTEGRATION_SCRIPT = (
    ROOT / "kaggle-blender-short-test" / "run_scene_integration_kaggle.py"
)


class SavedProjectSceneGeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix=".test-scene-generation-",
            dir=ROOT,
        )
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "projects"
        self.store = ProjectStore(self.root)
        self.project = self.store.save(create_project("Saved scene project"))
        self.generator = SavedProjectSceneGenerator(self.store, "blender-4.0.2")

    def test_plan_is_built_from_saved_project(self) -> None:
        plan = self.generator.plan_saved_project(self.project["id"])
        self.assertEqual(plan.project_id, self.project["id"])
        self.assertEqual(plan.objects[0].object_id, "starter")
        self.assertEqual(plan.eevee_samples, 8)

    def test_generation_passes_saved_project_to_blender_and_validates_outputs(self) -> None:
        output = self.root / "generated" / "scene.blend"
        report_path = output.with_suffix(".scene-report.json")

        def run(command: list[str], **kwargs: object) -> CompletedProcess[str]:
            timeout = kwargs.get("timeout")
            self.assertIsInstance(timeout, int)
            if command[-1] == "--version":
                return CompletedProcess(command, 0, "Blender 4.0.2\n", "")
            project_file = Path(command[command.index("--project") + 1])
            self.assertEqual(project_file, self.root / f"{self.project['id']}.json")
            blend_path = Path(command[command.index("--output") + 1])
            scene_report = Path(command[command.index("--report") + 1])
            self.assertEqual(blend_path, output)
            self.assertIn("--factory-startup", command)
            self.assertEqual(command[command.index("--threads") + 1], "1")
            blend_path.write_bytes(b"test blend artifact")
            scene_report.write_text(
                json.dumps(
                    {
                        "status": "SCENE_BUILT",
                        "project_id": self.project["id"],
                        "blender_version": "4.0.2",
                        "engine": "BLENDER_EEVEE",
                        "eevee_samples": 8,
                        "simulation_or_render_executed": False,
                        "device": None,
                    }
                ),
                encoding="utf-8",
            )
            return CompletedProcess(command, 0, "scene built\n", "")

        with patch("ai_engine.scene_generation.subprocess.run", side_effect=run) as mocked:
            result = self.generator.generate(
                self.project["id"],
                "generated\\scene.blend",
            )

        self.assertEqual(mocked.call_count, 2)
        self.assertTrue(result.blend_file.is_file())
        self.assertEqual(result.blend_file, output)
        self.assertEqual(result.report_file, report_path)
        self.assertEqual(result.blender_version, "4.0.2")
        self.assertEqual(result.scene_plan.eevee_samples, 8)
        self.assertEqual(
            scene_report_from_file(report_path)["status"],
            "SCENE_BUILT",
        )

    def test_generation_rejects_wrong_version_and_output_escape(self) -> None:
        with patch(
            "ai_engine.scene_generation.subprocess.run",
            return_value=CompletedProcess(["blender", "--version"], 0, "Blender 4.1.0\n", ""),
        ):
            with self.assertRaisesRegex(SceneGenerationError, "Blender 4.0.2 is required"):
                self.generator.generate(self.project["id"])

        with self.assertRaisesRegex(SceneGenerationError, "inside the configured"):
            self.generator.generate(
                self.project["id"],
                ROOT.parent / "outside.blend",
            )

    def test_generation_reports_missing_blender_without_creating_scene(self) -> None:
        with patch(
            "ai_engine.scene_generation.subprocess.run",
            side_effect=FileNotFoundError("not installed"),
        ):
            with self.assertRaisesRegex(SceneGenerationError, "was not found"):
                self.generator.generate(self.project["id"])
        self.assertFalse((self.root / "generated-scenes").exists())

    def test_integration_reopens_saved_scene_and_validates_measured_motion(self) -> None:
        blend_file = (
            self.root
            / "generated-scenes"
            / self.project["id"]
            / f"{self.project['id']}.blend"
        )

        def run(
            command: list[str],
            *,
            timeout: int,
            **kwargs: object,
        ) -> CompletedProcess[str]:
            self.assertLessEqual(timeout, 600)
            self.assertIn("capture_output", kwargs)
            if command[-1] == "--version":
                return CompletedProcess(command, 0, "Blender 4.0.2\n", "")
            if "--project" in command:
                blend = Path(command[command.index("--output") + 1])
                scene_report = Path(command[command.index("--report") + 1])
                blend.parent.mkdir(parents=True, exist_ok=True)
                blend.write_bytes(b"mocked scene artifact")
                scene_report.write_text(
                    json.dumps(
                        {
                            "status": "SCENE_BUILT",
                            "project_id": self.project["id"],
                            "blender_version": "4.0.2",
                            "engine": "BLENDER_EEVEE",
                            "eevee_samples": 8,
                            "simulation_or_render_executed": False,
                            "device": None,
                        }
                    ),
                    encoding="utf-8",
                )
                return CompletedProcess(command, 0, "built\n", "")

            self.assertIn(str(blend_file), command)
            verification_report = Path(command[command.index("--report") + 1])
            verification_report.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "status": "PASSED",
                        "project_id": self.project["id"],
                        "blender_version": "4.0.2",
                        "blend_file": str(blend_file),
                        "checks": {
                            "blender_version": True,
                            "blend_reopened": True,
                            "eevee_settings": True,
                            "rigid_body_objects": True,
                            "target_static_before_contact": True,
                            "launcher_reached_contact": True,
                            "target_moved_after_contact": True,
                        },
                        "measurements": {
                            "target_motion_toward_chain_m": 0.25,
                        },
                        "errors": [],
                    }
                ),
                encoding="utf-8",
            )
            return CompletedProcess(command, 0, "verified\n", "")

        with patch("ai_engine.scene_generation.subprocess.run", side_effect=run) as mocked:
            report = run_saved_project_scene_integration(
                self.store,
                "blender-4.0.2",
                self.project["id"],
            )

        self.assertEqual(mocked.call_count, 3)
        self.assertEqual(report["status"], "PASSED")
        self.assertTrue(report["checks"]["blend_reopened"])
        self.assertTrue(report["checks"]["physics_verified"])
        self.assertTrue(Path(report["integration_report_file"]).is_file())
        self.assertEqual(
            validate_verification_report(
                report["verification"],
                self.project["id"],
                blend_file,
            )["status"],
            "PASSED",
        )

    def test_integration_records_blender_process_failure(self) -> None:
        def run(
            command: list[str],
            *,
            timeout: int,
            **kwargs: object,
        ) -> CompletedProcess[str]:
            self.assertIsInstance(timeout, int)
            self.assertIn("capture_output", kwargs)
            if command[-1] == "--version":
                return CompletedProcess(command, 0, "Blender 4.0.2\n", "")
            if "--project" in command:
                blend = Path(command[command.index("--output") + 1])
                scene_report = Path(command[command.index("--report") + 1])
                blend.parent.mkdir(parents=True, exist_ok=True)
                blend.write_bytes(b"mocked scene artifact")
                scene_report.write_text(
                    json.dumps(
                        {
                            "status": "SCENE_BUILT",
                            "project_id": self.project["id"],
                            "blender_version": "4.0.2",
                            "engine": "BLENDER_EEVEE",
                            "eevee_samples": 8,
                            "simulation_or_render_executed": False,
                            "device": None,
                        }
                    ),
                    encoding="utf-8",
                )
                return CompletedProcess(command, 0, "built\n", "")
            return CompletedProcess(command, 1, "", "physics verification failed")

        with patch("ai_engine.scene_generation.subprocess.run", side_effect=run):
            report = run_saved_project_scene_integration(
                self.store,
                "blender-4.0.2",
                self.project["id"],
            )

        self.assertEqual(report["status"], "FAILED")
        self.assertEqual(report["verification_process_exit_code"], 1)
        self.assertIn("physics verification failed", report["errors"][0])
        saved = json.loads(Path(report["integration_report_file"]).read_text(encoding="utf-8"))
        self.assertEqual(saved["status"], "FAILED")

    def test_verification_report_must_show_passed_collision_checks(self) -> None:
        report = {
            "schema_version": 1,
            "status": "PASSED",
            "project_id": self.project["id"],
            "blender_version": "4.0.2",
            "blend_file": str(self.root / "scene.blend"),
            "checks": {
                "blender_version": True,
                "blend_reopened": True,
                "eevee_settings": True,
                "rigid_body_objects": True,
                "launcher_reached_contact": True,
                "target_moved_after_contact": False,
            },
            "measurements": {},
            "errors": [],
        }
        with self.assertRaisesRegex(ValueError, "failed schema"):
            validate_verification_report(
                report,
                self.project["id"],
                self.root / "scene.blend",
            )

    def test_kaggle_restorer_import_does_not_execute_production_runner(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "scene_integration_kaggle",
            KAGGLE_INTEGRATION_SCRIPT,
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("Could not load the Kaggle integration runner for testing.")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        load_restorer = getattr(module, "_load_verified_runtime_restorer", None)
        if not callable(load_restorer):
            raise RuntimeError("Kaggle integration runner lacks the restore helper loader.")
        restore_blender_runtime = load_restorer(
            KAGGLE_INTEGRATION_SCRIPT.with_name("short_test_runner.py")
        )
        if not isinstance(restore_blender_runtime, FunctionType):
            raise RuntimeError("Kaggle integration runner returned an invalid restore helper.")
        namespace = restore_blender_runtime.__globals__

        self.assertTrue(callable(namespace["restore_blender_runtime"]))
        self.assertNotIn("main", namespace)
        self.assertNotIn("OUTPUT", namespace)


if __name__ == "__main__":
    unittest.main()
