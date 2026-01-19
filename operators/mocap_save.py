import bpy
import os
from datetime import datetime
from ..utils import paths, naming, logger

class EKPV_OT_SaveMocapAction(bpy.types.Operator):
    """Save current blend file as mocap recording (non-destructive workflow)"""
    bl_idname = "ekpv.save_mocap_action"
    bl_label = "Save Mocap Recording"
    bl_description = "Save blend file as mocap recording in _Library/Mocap/Face/LiveLink/"
    bl_options = {'REGISTER'}

    def execute(self, context):
        logger.info("Starting Mocap Recording Save...")
        
        # Get Preferences
        try:
            prefs = context.preferences.addons["EK_PV"].preferences
        except KeyError:
            prefs = context.preferences.addons[__package__.split('.')[0]].preferences

        project_root = prefs.project_root
        if not project_root or project_root == "//":
            if bpy.data.filepath:
                project_root = os.path.dirname(bpy.data.filepath)
            else:
                logger.error("Project root not set and file not saved.")
                self.report({'ERROR'}, "Save file or set Project Root in preferences")
                return {'CANCELLED'}
        else:
            project_root = bpy.path.abspath(project_root)

        # 1. Determine Filename and Path
        date_obj = datetime.now()
        date_str = date_obj.strftime("%Y-%m-%d")
        
        mocap_dir = paths.get_mocap_dir(project_root, ensure=True)
        logger.debug(f"Scanning mocap directory: {mocap_dir}")
        
        # Scan for existing sessions to determine next number
        max_num = 0
        pattern = f"Session_{date_str}_*.blend"
        
        try:
            for f in mocap_dir.glob(pattern):
                try:
                    parts = f.stem.split('_')
                    num = int(parts[-1])
                    if num > max_num:
                        max_num = num
                except (ValueError, IndexError):
                    continue
        except OSError as e:
            logger.error(f"Error scanning directory: {e}")
            self.report({'ERROR'}, f"Error scanning directory: {e}")
            return {'CANCELLED'}

        session_num = max_num + 1
        filename = naming.get_session_filename(date_obj, session_num)
        save_path = mocap_dir / filename
        logger.info(f"Generated new filename: {filename}")

        # 2. Asset Marking
        obj = context.object
        if obj and obj.animation_data and obj.animation_data.action:
            action = obj.animation_data.action
            logger.debug(f"Marking action as asset: {action.name}")
            action.asset_mark()
            
            # Add Tags
            tags = ["mocap", "facial", date_str]
            character_name = obj.name # Or use helper
            tags.append(character_name)
            
            for tag in tags:
                action.asset_data.tags.new(tag, skip_if_exists=True)
                
            desc = context.scene.ekpv_session_description
            if desc:
                action.asset_data.description = f"{character_name} - {desc}"
        
        # 3. Save As (Switch to new file)
        try:
            logger.info(f"Saving to new session file: {save_path}")
            # copy=False means "Save As" (current file becomes this new file)
            bpy.ops.wm.save_as_mainfile(filepath=str(save_path), copy=False)
            self.report({'INFO'}, f"Saved & Opened Mocap Session: {filename}")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            self.report({'ERROR'}, f"Failed to save file: {e}")
            return {'CANCELLED'}

        logger.info("Mocap Save Complete. Now working in session file.")
        return {'FINISHED'}
