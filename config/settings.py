import bpy

class EKPV_Preferences(bpy.types.AddonPreferences):
    bl_idname = "EK_PV" # Must match package name if __init__ is in root of zip, or whatever name used in bl_info["name"]? No, package name.
    # Since we are in EK_PV package, bl_idname should be the package name.
    # If the folder is "EK_PV", then "EK_PV".
    
    project_root: bpy.props.StringProperty(
        name="Project Root",
        subtype='DIR_PATH',
        default="//"
    )
    
    mocap_export_path: bpy.props.StringProperty(
        name="Mocap Export Path",
        default="/_Library/Mocap/Facial/"
    )
    
    pose_library_path: bpy.props.StringProperty(
        name="Pose Library Path",
        default="/_Library/Expressions/"
    )
    
    arp_preset_path: bpy.props.StringProperty(
        name="ARP Bone Map Preset",
        subtype='FILE_PATH',
        default="//_Library/Presets/Mixamo_to_HumGen.bmap"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "project_root")
        layout.prop(self, "mocap_export_path")
        layout.prop(self, "pose_library_path")
        layout.prop(self, "arp_preset_path")

def register():
    bpy.utils.register_class(EKPV_Preferences)
    
    # Register Scene Properties
    bpy.types.Scene.ekpv_session_description = bpy.props.StringProperty(
        name="Session Description",
        description="Description for the mocap session",
        default=""
    )
    
    bpy.types.Scene.ekpv_naming_mode = bpy.props.EnumProperty(
        name="Naming Mode",
        items=[
            ('SEQUENTIAL', "Sequential", "Auto-numbering"),
            ('INDIVIDUAL', "Individual", "Prompt for each"),
        ],
        default='SEQUENTIAL'
    )

def unregister():
    del bpy.types.Scene.ekpv_naming_mode
    del bpy.types.Scene.ekpv_session_description
    bpy.utils.unregister_class(EKPV_Preferences)
