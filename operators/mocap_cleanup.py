import bpy
from ..utils import faceit_detection

class EKPV_OT_CleanupActivateControlRig(bpy.types.Operator):
    """Cleanup NLA and activate control rig for editing"""
    bl_idname = "ekpv.cleanup_activate_control_rig"
    bl_label = "Cleanup & Activate Control Rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        result = self.cleanup_and_activate_control_rig()
        
        if result['success']:
            self.report({'INFO'}, result['message'])
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, result['message'])
            return {'CANCELLED'}

    def cleanup_and_activate_control_rig(self):
        """
        Automate NLA cleanup: Remove shape key action from mesh and activate control rig.
        """
        result = {
            'success': False,
            'message': '',
            'control_rig_action': None,
            'mesh_cleaned': False,
            'control_rig_activated': False
        }
        
        # Find character mesh (HG_Body or similar)
        mesh_obj = faceit_detection.find_character_mesh()
        
        if not mesh_obj:
            result['message'] = 'Could not find character mesh'
            return result
        
        # Step 1: Clean up shape key action from mesh
        if mesh_obj.animation_data and mesh_obj.animation_data.action:
            # Set mesh as active object
            bpy.context.view_layer.objects.active = mesh_obj
            
            # Push down action (creates NLA strip)
            bpy.ops.nla.action_pushdown()
            
            # Delete the NLA strip that was just created
            if mesh_obj.animation_data.nla_tracks:
                track = mesh_obj.animation_data.nla_tracks[-1]
                if track.strips:
                    strip = track.strips[-1]
                    track.strips.remove(strip)
                # Remove empty track
                mesh_obj.animation_data.nla_tracks.remove(track)
            
            result['mesh_cleaned'] = True
        
        # Step 2: Find and activate control rig
        control_rig = faceit_detection.find_faceit_control_rig()
        
        if not control_rig:
            result['message'] = 'Could not find Faceit control rig'
            return result
        
        if not control_rig.animation_data or not control_rig.animation_data.action:
            result['message'] = 'No action on control rig. Have you baked shape keys?'
            return result
        
        # Store action name
        result['control_rig_action'] = control_rig.animation_data.action.name
        
        # Set control rig as active
        bpy.context.view_layer.objects.active = control_rig
        control_rig.select_set(True) # Ensure selected
        
        # Push down action
        try:
            bpy.ops.nla.action_pushdown()
        except Exception:
            # Sometimes fails if context is wrong or track already exists?
            pass
            
        # Enter tweak mode (activates the strip - turns green)
        # We need to ensure we are in the NLA editor context or similar for some ops?
        # nla.tweakmode_enter() works on active strip.
        # Push down usually leaves no active action, but creates a track with a strip.
        # We need to select the strip?
        
        if control_rig.animation_data.nla_tracks:
            # Get the last track/strip
            track = control_rig.animation_data.nla_tracks[-1]
            if track.strips:
                strip = track.strips[-1]
                strip.select = True
                track.select = True
                
                # Context override might be needed if not in NLA editor area? 
                # But bpy.ops usually works if context is vaguely correct.
                # Tweak mode requires the NLA track/strip to be selected/active.
                try:
                    bpy.ops.nla.tweakmode_enter()
                    result['control_rig_activated'] = True
                except Exception as e:
                    # If it fails, we might just set use_tweak_mode manually?
                    # But the operator does setup.
                    result['message'] = f"Action pushed down, but tweak mode failed: {e}"
                    return result
        
        result['success'] = True
        result['message'] = f'Control rig action "{result["control_rig_action"]}" activated.'
        
        return result
