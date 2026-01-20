import bpy
from . import mocap_save, marker_export, mocap_cleanup, mixamo_setup

classes = (
    mocap_save.EKPV_OT_SaveMocapAction,
    marker_export.EKPV_OT_ExportSelectedMarkers,
    marker_export.EKPV_OT_ExportAllMarkers,
    mocap_cleanup.EKPV_OT_CleanupActivateControlRig,
    mixamo_setup.EKPV_OT_ImportMixamoFBX,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
