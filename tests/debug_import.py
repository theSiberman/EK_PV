import sys
import os
from unittest.mock import MagicMock

# Mock bpy
sys.modules['bpy'] = MagicMock()

# Set package context
# We need to simulate running from the parent directory so 'EK_PV' is the package
sys.path.append(os.path.dirname(os.getcwd()))

try:
    import EK_PV
    import EK_PV.operators.marker_export
    print("Import Successful")
except Exception as e:
    print(f"Import Failed: {e}")
    import traceback
    traceback.print_exc()
