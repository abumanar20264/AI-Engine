from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ai_engine.project_service import ProjectService, default_projects_directory
from ai_engine.project_store import ProjectStore


class ProjectServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix=".test-project-service-",
            dir=ROOT,
        )
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "projects"
        self.service = ProjectService(ProjectStore(self.root))

    def test_create_edit_save_and_reopen_project(self) -> None:
        project = self.service.new_project("First experiment")
        self.assertEqual(project["scenario"]["video"]["eevee_samples"], 8)
        self.assertFalse(self.root.exists())

        project["name"] = "Edited experiment"
        project["scenario"]["gravity_m_s2"] = [0, 0, -3.7]
        saved = self.service.save_project(project)
        self.assertEqual(saved["name"], "Edited experiment")
        self.assertEqual(
            self.service.load_project(saved["id"])["scenario"]["gravity_m_s2"],
            [0.0, 0.0, -3.7],
        )
        self.assertEqual(self.service.list_projects(), [saved])

    def test_listing_missing_project_directory_returns_empty_list(self) -> None:
        self.assertFalse(self.root.exists())
        self.assertEqual(self.service.list_projects(), [])
        self.assertFalse(self.root.exists())

    def test_create_rejects_invalid_name(self) -> None:
        with self.assertRaisesRegex(ValueError, "name"):
            self.service.new_project(" \n ")

    def test_store_root_helper_uses_repository_projects_directory(self) -> None:
        self.assertEqual(
            default_projects_directory(ROOT),
            ROOT / "projects",
        )


if __name__ == "__main__":
    unittest.main()
