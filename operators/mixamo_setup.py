import bpy
import os
from bpy_extras.io_utils import ImportHelper
from ..utils import logger

class EKPV_OT_ImportMixamoFBX(bpy.types.Operator, ImportHelper):
    """Import Mixamo FBX and setup Auto Rig Pro Retargeting"""
    bl_idname = "ekpv.import_mixamo_fbx"
    bl_label = "Import & Setup Mixamo"
    bl_description = "Import Mixamo FBX, scale, and configure ARP retargeting"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".fbx"
    filter_glob: bpy.props.StringProperty(default="*.fbx", options={'HIDDEN'})

    def execute(self, context):
        logger.info(f"Importing Mixamo FBX: {self.filepath}")
        
        # 1. Store list of objects before import
        existing_objects = set(bpy.data.objects.keys())
        
        # 2. Import FBX
        # Settings: ignore leaf bones is usually good for Mixamo
        try:
            bpy.ops.import_scene.fbx(filepath=self.filepath, use_manual_orientation=False, ignore_leaf_bones=True)
        except Exception as e:
            logger.error(f"FBX Import failed: {e}")
            self.report({'ERROR'}, f"Import failed: {e}")
            return {'CANCELLED'}
            
        # 3. Identify Imported Armature
        new_objects = [bpy.data.objects[name] for name in bpy.data.objects.keys() if name not in existing_objects]
        armature = next((obj for obj in new_objects if obj.type == 'ARMATURE'), None)
        
        if not armature:
            logger.error("No armature found in imported FBX")
            self.report({'ERROR'}, "No armature found in FBX")
            return {'CANCELLED'}
            
        logger.info(f"Detected Mixamo armature: {armature.name}")
        
        # 4. Scale Adjustment (0.009)
        armature.scale = (0.009, 0.009, 0.009)
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        logger.debug("Applied scale 0.009")
        
        # 5. ARP Retargeting Setup
        # Requires Auto Rig Pro to be installed
        if not hasattr(bpy.ops, "arp"):
            logger.warning("Auto Rig Pro not detected. Retargeting setup skipped.")
            self.report({'WARNING'}, "Mixamo imported and scaled, but ARP not found.")
            return {'FINISHED'}
            
        try:
            # Set source armature in ARP
            # Note: ARP operators usually expect specific context or properties
            # Based on standard ARP usage:
            # bpy.context.scene.arp_retarget_source = armature.name
            # But let's check if we can call the setup operator
            
            # 1. Set as Source
            armature.select_set(True)
            # Find target (usually the rig in the scene)
            target_rig = self.find_target_rig()
            if target_rig:
                logger.info(f"Found target rig for retargeting: {target_rig.name}")
                
                # Logic to set ARP properties
                # These property names are based on ARP 3.6x+
                context.scene.arp_retarget_source = armature.name
                context.scene.arp_retarget_target = target_rig.name
                
                # 2. Build Bones Map
                bpy.ops.arp.build_bones_map()
                
                # 3. Load Preset
                prefs = context.preferences.addons["EK_PV"].preferences
                preset_path = bpy.path.abspath(prefs.arp_preset_path)
                
                if os.path.exists(preset_path):
                    logger.info(f"Loading ARP Bone Map preset: {preset_path}")
                    bpy.ops.arp.import_config(filepath=preset_path)
                else:
                    logger.warning(f"ARP Preset not found at: {preset_path}")
                    
                self.report({'INFO'}, "Mixamo Setup Complete (Imported, Scaled, ARP Configured)")
            else:
                logger.warning("No target rig found for retargeting setup.")
                self.report({'WARNING'}, "Mixamo imported and scaled, but no target rig found.")
                
        except Exception as e:
            logger.error(f"ARP Setup failed: {e}")
            self.report({'WARNING'}, f"Mixamo imported, but ARP setup failed: {e}")

        return {'FINISHED'}

    def find_target_rig(self):
        """Find the main character rig (target for retargeting)"""
        # Look for typical rig names or Faceit rig
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE':
                if "Faceit" in obj.name or "rig" in obj.name.lower() or "body" in obj.name.lower():
                    # If it's not the one we just imported
                    if obj.scale[0] > 0.1: # Heuristic: target rigs aren't tiny mixamo scaled
                        return obj
        return None

def register():
    bpy.utils.register_class(EKPV_OT_ImportMixamoFBX)

def unregister():
    bpy.utils.unregister_class(EKPV_OT_ImportMixamoFBX)
