import bpy
from ..utils import faceit_detection, paths, manifest

class EKPV_PT_MainPanel(bpy.types.Panel):
    """EK_PV Main Panel"""
    bl_label = "EK_PV Tools"
    bl_idname = "EKPV_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "EK_PV"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # --- Section 1: Motion Capture ---
        box = layout.box()
        box.label(text="Motion Capture (Non-Destructive)", icon='ACTION')
        
        # Detect State
        state = faceit_detection.detect_mocap_state()
        
        # Status Row
        row = box.row()
        row.label(text=f"Status: {state}")
        
        # Character & Action
        control_rig = faceit_detection.find_faceit_control_rig()
        char_name = faceit_detection.get_character_name(control_rig) if control_rig else "None"
        box.label(text=f"Character: {char_name}")
        
        action_name = "None"
        if control_rig and control_rig.animation_data and control_rig.animation_data.action:
            action_name = control_rig.animation_data.action.name
        box.label(text=f"Action: {action_name}", icon='ANIM_DATA')
        
        box.separator()
        
        # Cleanup Button
        cleanup_row = box.row()
        cleanup_row.operator("ekpv.cleanup_activate_control_rig")
        # Enable based on state
        if state == 'NO_BAKE':
            cleanup_row.enabled = False
        # elif state == 'READY_TO_SAVE':
        #     cleanup_row.enabled = False # Allow retry if needed
        
        box.separator()
        
        col = box.column(align=True)
        col.prop(scene, "ekpv_session_description")
        col.label(text="Current File:")
        col.label(text=bpy.path.basename(bpy.data.filepath) or "Unsaved")
        
        col.separator()
        col.operator("ekpv.save_mocap_action", icon='EXPORT')
        
        box.label(text="Work directly in this file.", icon='INFO')
        
        # --- Section 2: Expression Library ---
        box = layout.box()
        box.label(text="Expression Library (Markers)", icon='ASSET_MANAGER')
        
        # Marker Stats
        markers = scene.timeline_markers
        selected_markers = [m for m in markers if m.select]
        
        # We need to know processed count. 
        # This requires reading manifest which might be slow for draw loop?
        # Maybe just cache it or assume user hits refresh?
        # For now, minimal read or just display counts.
        
        col = box.column(align=True)
        col.label(text=f"Selected Markers: {len(selected_markers)}")
        col.label(text=f"Total Markers: {len(markers)}")
        
        box.separator()
        box.label(text=f"Character: {char_name}")
        
        box.separator()
        box.operator("ekpv.export_selected_markers")
        
        row = box.row()
        op = row.operator("ekpv.export_all_markers")
        op.skip_processed = scene.ekpv_skip_processed
        
        box.separator()
        box.prop(scene, "ekpv_skip_processed", text="Skip Already Processed")
        # Note: skip_processed is prop of operator, but we can bind it to scene prop for persistence if defined
        
        # Status/Refresh
        # box.operator("ekpv.refresh_marker_state") # Not implemented yet

def register():
    bpy.utils.register_class(EKPV_PT_MainPanel)
    
    # Register temporary scene props for UI
    bpy.types.Scene.ekpv_skip_processed = bpy.props.BoolProperty(
        name="Skip Processed",
        default=True
    )

def unregister():
    del bpy.types.Scene.ekpv_skip_processed
    bpy.utils.unregister_class(EKPV_PT_MainPanel)