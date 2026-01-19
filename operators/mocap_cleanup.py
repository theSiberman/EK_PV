import bpy
from ..utils import faceit_detection, logger

class EKPV_OT_CleanupActivateControlRig(bpy.types.Operator):
    """Cleanup NLA and activate control rig for editing"""
    bl_idname = "ekpv.cleanup_activate_control_rig"
    bl_label = "Cleanup & Activate Control Rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        logger.info("Starting Cleanup & Activate Control Rig...")
        result = self.cleanup_and_activate_control_rig()
        
        if result['success']:
            logger.info(f"Cleanup success: {result['message']}")
            self.report({'INFO'}, result['message'])
            return {'FINISHED'}
        else:
            logger.warning(f"Cleanup failed: {result['message']}")
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
        logger.debug("Searching for character mesh...")
        mesh_obj = faceit_detection.find_character_mesh()
        
        if not mesh_obj:
            logger.error("Could not find character mesh")
            result['message'] = 'Could not find character mesh'
            return result
        
        logger.debug(f"Found character mesh: {mesh_obj.name}")
        
        # Step 1: Clean up shape key action from mesh
        cleaned_any = False
        
        # 1a. Check Object Level Action (Transforms etc)
        if mesh_obj.animation_data and mesh_obj.animation_data.action:
            action_name = mesh_obj.animation_data.action.name
            logger.info(f"Cleaning up Object Action '{action_name}' from mesh '{mesh_obj.name}'")
            mesh_obj.animation_data.action = None
            cleaned_any = True
            result['mesh_cleaned'] = True
            
        # 1b. Check Shape Key Level Action (Faceit Bake target)
        if mesh_obj.data.shape_keys and mesh_obj.data.shape_keys.animation_data and mesh_obj.data.shape_keys.animation_data.action:
            action_name = mesh_obj.data.shape_keys.animation_data.action.name
            logger.info(f"Cleaning up Shape Key Action '{action_name}' from mesh '{mesh_obj.name}'")
            mesh_obj.data.shape_keys.animation_data.action = None
            cleaned_any = True
            result['mesh_cleaned'] = True
            
        if not cleaned_any:
            logger.debug("No active action on mesh (Object or ShapeKeys) to clean.")
        
        # Step 2: Find and activate control rig
        logger.debug("Searching for Faceit control rig...")
        control_rig = faceit_detection.find_faceit_control_rig()
        
        if not control_rig:
            logger.error("Could not find Faceit control rig")
            result['message'] = 'Could not find Faceit control rig'
            return result
            
        logger.debug(f"Found control rig: {control_rig.name}")
        
        if not control_rig.animation_data or not control_rig.animation_data.action:
            logger.warning("No action on control rig.")
            result['message'] = 'No action on control rig. Have you baked shape keys?'
            return result
        
        # Store action name
        action = control_rig.animation_data.action
        result['control_rig_action'] = action.name
        logger.info(f"Control Rig Action: {result['control_rig_action']}")
        
        # Set control rig as active and selected for refinement
        bpy.context.view_layer.objects.active = control_rig
        control_rig.select_set(True)
        
        # Ensure we are in Pose Mode if it's an armature
        if control_rig.type == 'ARMATURE':
            try:
                bpy.ops.object.mode_set(mode='POSE')
                logger.debug("Switched to Pose Mode")
            except Exception:
                pass
        
        result['control_rig_activated'] = True
        result['success'] = True
        result['message'] = f'Mesh cleaned and rig "{control_rig.name}" selected for refinement.'
        
        return result
