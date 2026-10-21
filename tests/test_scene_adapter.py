from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ai_engine.project_store import ProjectStore, create_project
from ai_engine.scene_adapter import SceneAdapterError, project_to_scene_plan


class SceneAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = create_project("Scene adapter test")

    def test_project_settings_map_to_scene_plan(self) -> None:
        project = copy.deepcopy(self.project)
        project["scenario"]["video"].update(
            {"width": 1080, "height": 1920, "fps": 30, "frame_count": 240}
        )
        project["scenario"]["video"]["eevee_samples"] = 8
        project["scenario"]["gravity_m_s2"] = [0, 0, -4.5]
        project["scenario"]["camera"]["position"] = [4, -8, 6]
        project["scenario"]["camera"]["target"] = [0.5, 0, 1]
        project["scenario"]["objects"][0]["mass_kg"] = 2.0

        plan = project_to_scene_plan(project)

        self.assertEqual(plan.project_id, project["id"])
        self.assertEqual(plan.scenario_type, "rigid_body_chain")
        self.assertEqual(plan.gravity_m_s2, (0.0, 0.0, -4.5))
        self.assertEqual((plan.resolution_x, plan.resolution_y), (1080, 1920))
        self.assertEqual(plan.fps, 30)
        self.assertEqual(plan.frame_end, 240)
        self.assertEqual(plan.eevee_samples, 8)
        self.assertEqual(plan.camera_position, (4.0, -8.0, 6.0))
        self.assertEqual(plan.objects[0].mass_kg, 2.0)
        self.assertEqual(plan.launch_object_id, "starter")
        self.assertEqual(plan.target_object_id, "target")
        self.assertLess(plan.launch_end_position[0], plan.objects[1].position[0])
        self.assertEqual(plan.launch_release_frame, plan.launch_end_frame + 1)
        self.assertEqual(plan.blender_version, "4.0.2")
        self.assertEqual(plan.render_engine, "BLENDER_EEVEE")
        self.assertIsNone(plan.render_device)

    def test_rejects_unsupported_scenario_and_too_short_motion(self) -> None:
        unsupported = copy.deepcopy(self.project)
        unsupported["scenario"]["type"] = "fluid"
        with self.assertRaisesRegex(SceneAdapterError, "rigid_body_chain"):
            project_to_scene_plan(unsupported)

        too_short = copy.deepcopy(self.project)
        too_short["scenario"]["video"]["frame_count"] = 3
        with self.assertRaisesRegex(SceneAdapterError, "at least 4 frames"):
            project_to_scene_plan(too_short)

    def test_rejects_overlapping_launcher_and_nearest_target(self) -> None:
        overlapping = copy.deepcopy(self.project)
        overlapping["scenario"]["objects"][1]["position"] = [-1.9, 0, 0.5]
        with self.assertRaisesRegex(SceneAdapterError, "overlaps"):
            project_to_scene_plan(overlapping)

    def test_rejects_coincident_object_centers(self) -> None:
        coincident = copy.deepcopy(self.project)
        coincident["scenario"]["objects"][1]["position"] = [-2, 0, 0.5]
        with self.assertRaisesRegex(SceneAdapterError, "different X/Y"):
            project_to_scene_plan(coincident)

    def test_rejects_unreachable_target_and_non_downward_gravity(self) -> None:
        separated = copy.deepcopy(self.project)
        separated["scenario"]["objects"][1]["position"] = [0, 0, 5]
        with self.assertRaisesRegex(SceneAdapterError, "vertical collision band"):
            project_to_scene_plan(separated)

        upward = copy.deepcopy(self.project)
        upward["scenario"]["gravity_m_s2"] = [0, 0, 9.81]
        with self.assertRaisesRegex(SceneAdapterError, "Gravity Z must be negative"):
            project_to_scene_plan(upward)

    def test_rejects_camera_aiming_at_its_own_position(self) -> None:
        invalid_camera = copy.deepcopy(self.project)
        invalid_camera["scenario"]["camera"]["target"] = (
            invalid_camera["scenario"]["camera"]["position"].copy()
        )
        with self.assertRaisesRegex(SceneAdapterError, "must be different"):
            project_to_scene_plan(invalid_camera)

    def test_plan_can_be_created_from_a_project_loaded_from_project_store(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".test-scene-adapter-", dir=ROOT) as folder:
            store = ProjectStore(Path(folder) / "projects")
            saved = store.save(self.project)
            loaded = store.load(saved["id"])

            plan = project_to_scene_plan(loaded)

            self.assertEqual(plan.project_id, saved["id"])
            self.assertEqual(plan.objects[0].object_id, "starter")
            self.assertEqual(plan.eevee_samples, 8)


if __name__ == "__main__":
    unittest.main()
