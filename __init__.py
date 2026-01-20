bl_info = {
    "name": "EK_PV (Easy Killer Pre-Visualisation Tools)",
    "author": "Easy Killer",
    "version": (1, 0, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > EK_PV",
    "description": "Tools for automating AI Blender Pre-Viz workflow",
    "category": "Animation",
}

import bpy
from . import operators, ui, utils, config

def register():
    operators.register()
    ui.register()
    config.register()

def unregister():
    config.unregister()
    ui.unregister()
    operators.unregister()

if __name__ == "__main__":
    register()
