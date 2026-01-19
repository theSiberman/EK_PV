import bpy
import os
from datetime import datetime
from ..utils import paths, naming, manifest, faceit_detection, logger

class EKPV_OT_ExportSelectedMarkers(bpy.types.Operator):
    """Export selected timeline markers as expression pose assets"""
    bl_idname = "ekpv.export_selected_markers"
    bl_label = "Export Selected Marker(s)"
    bl_description = "Convert selected timeline markers to expression assets with automatic name sanitisation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        logger.info("Executing Export Selected Markers...")
        result = self.export_selected_markers(context)
        
        if result['success']:
            msg = f"Exported {result['markers_processed']} expressions"
            if result['errors']:
                msg += f" (with {len(result['errors'])} errors)"
            logger.info(msg)
            self.report({'INFO'}, msg)
            return {'FINISHED'}
        else:
            msg = "Export failed"
            if result['errors']:
                msg += f": {result['errors'][0]}"
            logger.error(msg)
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

    def export_selected_markers(self, context):
        result = {
            'success': False,
            'markers_processed': 0,
            'assets_created': [],
            'failed_markers': [],
            'errors': []
        }
        
        # Get control rig
        control_rig = faceit_detection.find_faceit_control_rig()
        if not control_rig or not control_rig.animation_data:
            logger.error("No control rig or animation data found")
            result['errors'].append('No control rig found')
            return result

        # Capture original state
        original_action = control_rig.animation_data.action
        was_tweak_mode = control_rig.animation_data.use_tweak_mode
        
        # Get selected markers
        selected_markers = [m for m in context.scene.timeline_markers if m.select]
        if not selected_markers:
            return result
        
        # Get character name & project root
        character_name = faceit_detection.get_character_name(control_rig)
        try:
            prefs = context.preferences.addons["EK_PV"].preferences
            project_root = bpy.path.abspath(prefs.project_root or "//")
        except:
            project_root = "//"

        # Ensure we are in Pose Mode
        context.view_layer.objects.active = control_rig
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')

        for marker in selected_markers:
            logger.info(f"Processing marker: {marker.name}")
            try:
                # 1. SETUP: Restore Rig to Original State for Sampling
                # We must exit tweak mode to change the action
                if control_rig.animation_data.use_tweak_mode:
                    control_rig.animation_data.use_tweak_mode = False
                
                if original_action:
                    control_rig.animation_data.action = original_action
                    
                # Restore tweak mode if that was the state (ensures NLA strip is evaluated correctly)
                if was_tweak_mode:
                    control_rig.animation_data.use_tweak_mode = True
                
                # 2. SAMPLE: Go to frame
                context.scene.frame_set(marker.frame)
                context.view_layer.update()
                
                # 3. AUTOMATED EXTRACT: Use NLA Bake
                # use_current_action=False creates a NEW action.
                bpy.ops.nla.bake(
                    frame_start=marker.frame,
                    frame_end=marker.frame,
                    only_selected=True,
                    visual_keying=True,
                    clear_constraints=False,
                    use_current_action=False, 
                    bake_types={'POSE'}
                )
                
                # The baked action is now active. Tweak mode is likely forced off by Bake.
                new_action = control_rig.animation_data.action
                
                sanitised_name = naming.sanitise_marker_name(marker.name)
                asset_name = f"FACE_{character_name}_{sanitised_name}"
                new_action.name = asset_name
                
                # 4. ASSET MARK & SAVE
                new_action.asset_mark()
                new_action.asset_data.tags.new("facial", skip_if_exists=True)
                new_action.asset_data.tags.new(character_name, skip_if_exists=True)
                source_file = bpy.path.basename(bpy.data.filepath) or "Unsaved"
                new_action.asset_data.description = f"From marker: {marker.name} in {source_file}"
                
                save_dir = paths.get_expression_dir(project_root, character_name, ensure=True)
                save_path = save_dir / f"{asset_name}.blend"
                
                # Write to library
                bpy.data.libraries.write(str(save_path), {new_action})
                
                # Update Manifest
                manifest.update_expression_manifest(
                    project_root=project_root,
                    asset_name=asset_name,
                    source_file=source_file,
                    frame_range=(marker.frame, marker.frame),
                    marker_name=marker.name,
                    notes=f"From marker: {marker.name}"
                )
                
                result['markers_processed'] += 1
                result['assets_created'].append(asset_name)
                logger.info(f"Successfully exported: {asset_name}")

            except Exception as e:
                logger.error(f"Failed to process marker {marker.name}: {e}")
                result['failed_markers'].append(marker.name)
                result['errors'].append(str(e))
                
        # RESTORE FINAL STATE
        try:
            if control_rig.animation_data.use_tweak_mode:
                control_rig.animation_data.use_tweak_mode = False
                
            if original_action:
                control_rig.animation_data.action = original_action
                
            if was_tweak_mode:
                control_rig.animation_data.use_tweak_mode = True
        except Exception as e:
             logger.error(f"Failed to restore final state: {e}")

        result['success'] = result['markers_processed'] > 0
        return result
        
        result['success'] = result['markers_processed'] > 0
        return result

class EKPV_OT_ExportAllMarkers(bpy.types.Operator):
    """Export all timeline markers as expression pose assets"""
    bl_idname = "ekpv.export_all_markers"
    bl_label = "Export All Markers"
    bl_description = "Batch export all markers (optionally skip already processed)"
    bl_options = {'REGISTER', 'UNDO'}
    
    skip_processed: bpy.props.BoolProperty(
        name="Skip Processed Markers",
        description="Skip markers that have already been exported",
        default=True
    )
    
    def execute(self, context):
        logger.info("Executing Export All Markers...")
        
        # Determine all markers
        all_markers = context.scene.timeline_markers
        logger.debug(f"Total markers found: {len(all_markers)}")
        
        # Deselect all first
        for m in all_markers:
            m.select = False
            
        # Get Project Root
        try:
            prefs = context.preferences.addons["EK_PV"].preferences
        except KeyError:
            prefs = context.preferences.addons[__package__.split('.')[0]].preferences
        project_root = bpy.path.abspath(prefs.project_root or "//")
        
        # Check Manifest for processed state
        man_path = paths.get_manifest_path(project_root, "expression")
        man_data = manifest.load_manifest(man_path)
        marker_state = man_data.get('marker_state', {})
        
        to_select = []
        for m in all_markers:
            is_processed = False
            if m.name in marker_state:
                if marker_state[m.name].get('processed', False):
                    is_processed = True
            
            if self.skip_processed and is_processed:
                continue
            
            to_select.append(m)
            
        logger.info(f"Markers eligible for export: {len(to_select)}")
        
        if not to_select:
            logger.info("No eligible markers to export")
            self.report({'INFO'}, "No eligible markers to export")
            return {'CANCELLED'}
            
        # Select them
        for m in to_select:
            m.select = True
            
        # Call the selected export operator
        return bpy.ops.ekpv.export_selected_markers()
