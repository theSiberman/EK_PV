import unittest
import os
import shutil
import tempfile
import json
from pathlib import Path
from datetime import datetime

from utils import naming, paths, manifest

class TestNaming(unittest.TestCase):
    def test_session_filename(self):
        date = datetime(2025, 1, 16)
        name = naming.get_session_filename(date, 1)
        self.assertEqual(name, "Session_2025-01-16_001.blend")
        
    def test_pose_asset_name(self):
        name = naming.get_pose_asset_name("Patrick", "Smile Confident")
        self.assertEqual(name, "FACE_PATRICK_Smile_Confident")
        
        name_indexed = naming.get_pose_asset_name("Patrick", "Smile", 1)
        self.assertEqual(name_indexed, "FACE_PATRICK_Smile_01")
        
        # Test sanitization
        name_dirty = naming.get_pose_asset_name("Patrick", "Smile! @#$")
        self.assertEqual(name_dirty, "FACE_PATRICK_Smile")
        
    def test_marker_sanitization(self):
        self.assertEqual(naming.sanitise_marker_name("happy face"), "Happy_Face")
        self.assertEqual(naming.sanitise_marker_name("big SMILE"), "Big_Smile")
        self.assertEqual(naming.sanitise_marker_name("confused   look"), "Confused_Look")

class TestPaths(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root = Path(self.test_dir)
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def test_library_path_default(self):
        # Default: [root]/_Library
        lib = paths.get_library_path(str(self.root))
        self.assertEqual(lib, self.root / "_Library")
        
    def test_library_path_existing(self):
        # Create _Library
        (self.root / "_Library").mkdir()
        lib = paths.get_library_path(str(self.root))
        self.assertEqual(lib, self.root / "_Library")
        
    def test_library_path_named(self):
        # Create _MyProject_Library
        (self.root / "_MyProject_Library").mkdir()
        lib = paths.get_library_path(str(self.root))
        self.assertEqual(lib, self.root / "_MyProject_Library")
        
    def test_subdirs(self):
        # Setup basic lib
        (self.root / "_Library").mkdir()
        
        mocap = paths.get_mocap_dir(str(self.root))
        self.assertEqual(mocap, self.root / "_Library" / "Mocap" / "Face" / "LiveLink")
        
        expr = paths.get_expression_dir(str(self.root), "PATRICK")
        self.assertEqual(expr, self.root / "_Library" / "Expressions" / "PATRICK")

class TestManifest(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root = Path(self.test_dir)
        # Create library structure
        self.lib = self.root / "_Library"
        self.lib.mkdir()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def test_update_manifest(self):
        result = manifest.update_expression_manifest(
            str(self.root),
            "FACE_TEST_Smile",
            "Session_001.blend",
            (10, 10),
            marker_name="smile",
            notes="Notes"
        )
        self.assertTrue(result['success'])
        
        # Check file
        man_path = paths.get_manifest_path(str(self.root), "expression")
        self.assertTrue(man_path.exists())
        
        with open(man_path, 'r') as f:
            data = json.load(f)
            
        self.assertIn("expressions", data)
        self.assertIn("FACE_TEST_Smile", data["expressions"])
        self.assertEqual(data["expressions"]["FACE_TEST_Smile"]["source_file"], "Session_001.blend")
        
        self.assertIn("marker_state", data)
        self.assertIn("smile", data["marker_state"])
        self.assertTrue(data["marker_state"]["smile"]["processed"])

    def test_backup(self):
        # Create initial manifest
        man_path = paths.get_manifest_path(str(self.root), "expression")
        man_path.parent.mkdir(parents=True, exist_ok=True)
        with open(man_path, 'w') as f:
            json.dump({"Old": "Data"}, f)
            
        # Add entry (triggers backup)
        manifest.update_expression_manifest(
            str(self.root), "New", "File", (1,1)
        )
        
        # Check for backup
        backups = list(man_path.parent.glob("*_BACKUP_*.json"))
        self.assertTrue(len(backups) > 0)

if __name__ == '__main__':
    unittest.main()
