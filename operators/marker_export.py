import bpy
import os
from datetime import datetime
from ..utils import paths, naming, manifest, faceit_detection

class EKPV_OT_ExportSelectedMarkers(bpy.types.Operator):
    """Export selected timeline markers as expression pose assets"""
    bl_idname = "ekpv.export_selected_markers"
    bl_label = "Export Selected Marker(s)"
    bl_description = "Convert selected timeline markers to expression assets with automatic name sanitisation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        result = self.export_selected_markers(context)
        
        if result['success']:
            msg = f"Exported {result['markers_processed']} expressions"
            if result['errors']:
                msg += f" (with {len(result['errors'])} errors)"
            self.report({'INFO'}, msg)
            return {'FINISHED'}
        else:
            msg = "Export failed"
            if result['errors']:
                msg += f": {result['errors'][0]}"
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
        
        # Get control rig and its action
        control_rig = faceit_detection.find_faceit_control_rig()
        if not control_rig or not control_rig.animation_data or not control_rig.animation_data.action:
            result['errors'].append('No control rig action found')
            return result
        
        action = control_rig.animation_data.action
        
        # Get selected markers
        # Blender API: context.scene.timeline_markers, check 'select' property
        selected_markers = [m for m in context.scene.timeline_markers if m.select]
        
        if not selected_markers:
            result['errors'].append('No markers selected in timeline')
            return result
        
        # Get character name
        character_name = faceit_detection.get_character_name(control_rig)
        
        # Get Project Root
        try:
            prefs = context.preferences.addons["EK_PV"].preferences
        except KeyError:
            prefs = context.preferences.addons[__package__.split('.')[0]].preferences
            
        project_root = prefs.project_root
        if not project_root:
            project_root = "//"
        project_root = bpy.path.abspath(project_root)
        
        # Process each marker
        for marker in selected_markers:
            try:
                # Sanitise marker name
                sanitised_name = naming.sanitise_marker_name(marker.name)
                
                # Generate asset name
                asset_name = f"FACE_{character_name}_{sanitised_name}"
                
                # Set timeline to marker frame
                context.scene.frame_set(marker.frame)
                
                # Ensure we are in Pose Mode and Rig selected
                context.view_layer.objects.active = control_rig
                bpy.ops.object.mode_set(mode='POSE')
                bpy.ops.pose.select_all(action='SELECT')
                
                # Create pose asset from current frame
                # Note: create_pose_asset operates on active object's pose
                bpy.ops.poselib.create_pose_asset(
                    pose_name=asset_name,
                    activate_new_action=False # Don't switch the action on the rig
                )
                
                # The asset is created in the current file. We need to save it out?
                # Spec says: "Save as pose asset to expressions library"
                # This implies saving a .blend file for the asset? 
                # Or just marking it in the current file?
                # "Save each pose to [ProjectRoot]/_[PROJECT]_Library/Expressions/[CHARACTER_NAME]/..."
                # Previous implementation saved individual files. New spec implies the same: 
                # "The saved blend file becomes the persistent mocap recording" (for the source)
                # But for the *expression assets*, they need to be in the library.
                
                # So we assume the newly created pose action needs to be written to a library file.
                # Find the action we just created. It's not active on the object because activate_new_action=False.
                # It should be in bpy.data.actions.
                new_pose_action = bpy.data.actions.get(asset_name)
                
                if new_pose_action:
                    # Asset Metadata
                    new_pose_action.asset_mark()
                    new_pose_action.asset_data.tags.new("facial", skip_if_exists=True)
                    new_pose_action.asset_data.tags.new(character_name, skip_if_exists=True)
                    source_file = bpy.path.basename(bpy.data.filepath) or "Unsaved"
                    new_pose_action.asset_data.description = f"From marker: {marker.name} in {source_file}"
                    
                    # Save to individual blend file in library
                    save_dir = paths.get_expression_dir(project_root, character_name, ensure=True)
                    save_path = save_dir / f"{asset_name}.blend"
                    
                    bpy.data.libraries.write(str(save_path), {new_pose_action})
                    
                    # Update manifest
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
                else:
                    result['failed_markers'].append(marker.name)
                    result['errors'].append(f"Could not find created action {asset_name}")
            
            except Exception as e:
                result['failed_markers'].append(marker.name)
                result['errors'].append(f"Failed to process marker '{marker.name}': {str(e)}")
        
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
        # Determine all markers
        all_markers = context.scene.timeline_markers
        
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
        # We need a helper in manifest.py to check if processed, or load whole manifest
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
            
        if not to_select:
            self.report({'INFO'}, "No eligible markers to export")
            return {'CANCELLED'}
            
        # Select them
        for m in to_select:
            m.select = True
            
        # Call the selected export operator
        return bpy.ops.ekpv.export_selected_markers()
