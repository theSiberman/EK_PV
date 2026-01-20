import unittest
import sys
import os

# Mock bpy
try:
    import bpy
except ImportError:
    from unittest.mock import MagicMock
    bpy = MagicMock()
    sys.modules['bpy'] = bpy

class TestImports(unittest.TestCase):
    def test_import_operators(self):
        try:
            from operators import marker_export
            from operators import mocap_cleanup
            from operators import mocap_save
        except ImportError as e:
            self.fail(f"Failed to import operators: {e}")
            
if __name__ == '__main__':
    unittest.main()
