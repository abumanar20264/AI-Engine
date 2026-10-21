from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ai_engine import (
    ProjectStore,
    ProjectStoreError,
    ProjectValidationError,
    create_project,
    validate_project,
)


class ProjectContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = create_project("Collision study")

    def test_default_project_has_versioned_scenario_and_safe_production_defaults(self) -> None:
        project = self.project
        self.assertEqual(project["schema_version"], 1)
        self.assertEqual(project["status"], "draft")
        self.assertEqual(project["task"]["status"], "not_started")
        self.assertEqual(project["scenario"]["type"], "rigid_body_chain")
        self.assertGreaterEqual(len(project["scenario"]["objects"]), 2)
        self.assertEqual(project["scenario"]["video"]["eevee_samples"], 8)
        self.assertFalse(project["audio"]["enabled"])
        self.assertIsNone(project["outputs"]["video"])

    def test_validation_returns_a_detached_normalized_document(self) -> None:
        validated = validate_project(self.project)
        validated["scenario"]["objects"][0]["position"][0] = 99
        self.assertNotEqual(
            self.project["scenario"]["objects"][0]["position"][0],
            validated["scenario"]["objects"][0]["position"][0],
        )

    def test_rejects_invalid_project_names_and_schema_versions(self) -> None:
        for name in (" ", "x" * 201, "bad\nname"):
            with self.subTest(name=repr(name)):
                candidate = copy.deepcopy(self.project)
                candidate["name"] = name
                with self.assertRaisesRegex(ProjectValidationError, "name"):
                    validate_project(candidate)

        candidate = copy.deepcopy(self.project)
        candidate["schema_version"] = 2
        with self.assertRaisesRegex(ProjectValidationError, "unsupported version"):
            validate_project(candidate)

    def test_rejects_invalid_objects_and_duplicate_object_ids(self) -> None:
        cases = [
            ("mass_kg", 0),
            ("friction", 1.1),
            ("restitution", -0.1),
            ("dimensions", [1, 0, 1]),
            ("position", [0, float("nan"), 0]),
            ("shape", "triangle"),
        ]
        for field, value in cases:
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.project)
                candidate["scenario"]["objects"][0][field] = value
                with self.assertRaises(ProjectValidationError):
                    validate_project(candidate)

        candidate = copy.deepcopy(self.project)
        candidate["scenario"]["objects"][1]["id"] = candidate["scenario"]["objects"][0]["id"]
        with self.assertRaisesRegex(ProjectValidationError, "unique"):
            validate_project(candidate)

        candidate["scenario"]["objects"] = candidate["scenario"]["objects"][:1]
        with self.assertRaisesRegex(ProjectValidationError, "between 2 and 64"):
            validate_project(candidate)

    def test_rejects_invalid_video_camera_and_audio_settings(self) -> None:
        mutations = [
            (("scenario", "video", "width"), True),
            (("scenario", "video", "fps"), 0),
            (("scenario", "video", "eevee_samples"), 3),
            (("scenario", "camera", "lens_mm"), 0),
            (("audio", "enabled"), "false"),
            (("audio", "volume"), 2.1),
        ]
        for keys, value in mutations:
            with self.subTest(keys=keys):
                candidate = copy.deepcopy(self.project)
                target = candidate
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                with self.assertRaises(ProjectValidationError):
                    validate_project(candidate)

        candidate = copy.deepcopy(self.project)
        candidate["audio"]["enabled"] = True
        with self.assertRaisesRegex(ProjectValidationError, "required when audio is enabled"):
            validate_project(candidate)

    def test_task_and_output_states_must_be_consistent(self) -> None:
        candidate = copy.deepcopy(self.project)
        candidate["task"]["status"] = "failed"
        with self.assertRaisesRegex(ProjectValidationError, "required when task status is failed"):
            validate_project(candidate)

        candidate["task"]["error"] = "Blender did not start"
        candidate["status"] = "failed"
        self.assertEqual(validate_project(candidate)["task"]["error"], "Blender did not start")

        candidate["task"]["status"] = "succeeded"
        candidate["task"]["error"] = None
        candidate["status"] = "completed"
        with self.assertRaisesRegex(ProjectValidationError, "outputs.video"):
            validate_project(candidate)

        candidate["outputs"]["video"] = "exports/result.mp4"
        self.assertEqual(validate_project(candidate)["status"], "completed")

    def test_rejects_noncanonical_project_ids_and_unknown_fields(self) -> None:
        candidate = copy.deepcopy(self.project)
        candidate["id"] = "../outside"
        with self.assertRaisesRegex(ProjectValidationError, "canonical lowercase UUID"):
            validate_project(candidate)

        candidate = copy.deepcopy(self.project)
        candidate["unexpected"] = True
        with self.assertRaisesRegex(ProjectValidationError, "unknown field"):
            validate_project(candidate)

        with self.assertRaisesRegex(ProjectValidationError, "keys must be text"):
            validate_project({**self.project, 1: "not a JSON object key"})


class ProjectStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix=".test-project-store-",
            dir=ROOT,
        )
        self.addCleanup(self.temporary.cleanup)
        self.store = ProjectStore(self.temporary.name)

    def test_save_load_and_list_round_trip(self) -> None:
        project = create_project("Round trip")
        saved = self.store.save(project)
        loaded = self.store.load(project["id"])
        self.assertEqual(loaded, saved)
        self.assertEqual(self.store.list_projects(), [saved])
        self.assertTrue((Path(self.temporary.name) / f"{project['id']}.json").is_file())

    def test_save_preserves_creation_time_and_supports_valid_updates(self) -> None:
        project = create_project("Initial name")
        self.store.save(project)
        updated = copy.deepcopy(project)
        updated["name"] = "Updated name"
        updated["status"] = "ready"
        saved = self.store.save(updated)
        self.assertEqual(saved["created_at"], project["created_at"])
        self.assertEqual(self.store.load(project["id"])["name"], "Updated name")
        self.assertEqual(len(list(Path(self.temporary.name).glob("*.json"))), 1)

    def test_rejects_path_traversal_and_missing_projects(self) -> None:
        with self.assertRaisesRegex(ProjectValidationError, "canonical lowercase UUID"):
            self.store.load("../../kaggle.json")
        with self.assertRaisesRegex(ProjectStoreError, "Project not found"):
            self.store.load(str(uuid4()))

    def test_reports_corrupt_or_duplicate_key_json(self) -> None:
        project_id = str(uuid4())
        path = Path(self.temporary.name) / f"{project_id}.json"
        path.write_text('{"id":"' + project_id + '","id":"' + project_id + '"}', encoding="utf-8")
        with self.assertRaisesRegex(ProjectStoreError, "duplicate JSON key"):
            self.store.load(project_id)

    def test_rejects_symbolic_links_in_project_storage(self) -> None:
        project_id = str(uuid4())
        outside = Path(self.temporary.name) / "outside.json"
        outside.write_text("{}", encoding="utf-8")
        link = Path(self.temporary.name) / f"{project_id}.json"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Symbolic links unavailable in this environment: {exc}")
        with self.assertRaisesRegex(ProjectStoreError, "symbolic link"):
            self.store.load(project_id)

    def test_failed_atomic_replace_leaves_no_temporary_file(self) -> None:
        project = create_project("Blocked destination")
        destination = Path(self.temporary.name) / f"{project['id']}.json"
        destination.mkdir()
        with self.assertRaises(ProjectStoreError):
            self.store.save(project)
        self.assertEqual(list(Path(self.temporary.name).glob("*.tmp")), [])
        self.assertTrue(destination.is_dir())

    def test_store_rejects_a_file_as_its_root(self) -> None:
        root_file = Path(self.temporary.name) / "not-a-directory"
        root_file.write_text("x", encoding="utf-8")
        store = ProjectStore(root_file)
        with self.assertRaisesRegex(ProjectStoreError, "not a directory"):
            store.save(create_project("Cannot save"))


if __name__ == "__main__":
    unittest.main()
