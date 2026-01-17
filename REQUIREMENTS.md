# EK_PV Plugin Development Specification

This document provides technical specifications and implementation requirements for the **EK_PV Plugin**, a custom Blender add-on designed to automate workflow tasks in the AI Blender Pre-Viz System.

## Plugin Overview

**Name:** EK_PV (Easy Killer Pre-Visualisation Tools)
**Type:** Blender Python Add-on
**Target Blender Version:** 5.0+
**Python Version:** 3.11+
**Architecture:** Marker-based workflow with non-destructive editing

**Core Philosophy:** Work directly in the blend file containing mocap data. The saved blend file becomes the persistent mocap recording, maintaining all markers (processed and unprocessed) and providing a complete history of conversions. This enables iterative refinement without losing connection to the original data.

## Core Requirements

### 1. Cleanup & Activate Control Rig

**Feature:** Automate NLA cleanup after shape key baking—remove shape key action from mesh and activate control rig action.

**User Story:** As an animator, I want to automate the tedious NLA cleanup steps after baking so that I can quickly get to the refinement stage.

**Workflow Context:**
After using Faceit's "Bake Shape Keys to Control Rig" function:

* Shape key animation exists on mesh (e.g., `HG_Body`).
* Control rig has baked action (e.g., `c_eyelid_upper_r_action`).
* Both need NLA cleanup before refinement can begin.

**Implementation Requirements:**

* Detect character mesh object (`HG_Body` or similar).
* Detect shape key action on mesh.
* Push down mesh action to NLA track.
* Delete the created NLA strip and track.
* Detect Faceit control rig object.
* Push down control rig action to NLA track.
* Enter tweak mode on control rig strip (activates for editing).
* Verify cleanup completed successfully.
* Display confirmation with control rig action name.

**State Detection:**
The plugin should detect workflow state:

```python
def detect_mocap_state():
    """
    Detect current state of mocap workflow.
    
    Returns:
        str: One of:
            'NO_BAKE' - No control rig action found
            'NEEDS_CLEANUP' - Baked but mesh still has shape key action
            'NEEDS_ACTIVATION' - Cleaned but control rig not in tweak mode
            'READY_TO_SAVE' - Control rig activated, ready for save
    """
    mesh_has_action = check_mesh_shape_key_action()
    control_rig = find_faceit_control_rig()
    
    if not control_rig or not control_rig.animation_data or not control_rig.animation_data.action:
        return 'NO_BAKE'
    
    if mesh_has_action:
        return 'NEEDS_CLEANUP'
    
    # Check if control rig is in tweak mode (activated)
    if control_rig.animation_data.use_tweak_mode:
        return 'READY_TO_SAVE'
    else:
        return 'NEEDS_ACTIVATION'

```

**Technical Details:**

```python
def cleanup_and_activate_control_rig():
    """
    Automate NLA cleanup: Remove shape key action from mesh and activate control rig.
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'control_rig_action': str,
            'mesh_cleaned': bool,
            'control_rig_activated': bool
        }
    """
    result = {
        'success': False,
        'message': '',
        'control_rig_action': None,
        'mesh_cleaned': False,
        'control_rig_activated': False
    }
    
    # Find character mesh (HG_Body or similar)
    mesh_obj = find_character_mesh()
    
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
    control_rig = find_faceit_control_rig()
    
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
    
    # Push down action
    bpy.ops.nla.action_pushdown()
    
    # Enter tweak mode (activates the strip - turns green)
    bpy.ops.nla.tweakmode_enter()
    
    result['control_rig_activated'] = True
    result['success'] = True
    result['message'] = f'Control rig action "{result["control_rig_action"]}" activated and ready for refinement'
    
    return result


def find_character_mesh():
    """Find character mesh object (HG_Body or similar)."""
    # Try common HumGen naming
    for name in ['HG_Body', 'Body', 'CharacterMesh']:
        obj = bpy.data.objects.get(name)
        if obj and obj.type == 'MESH':
            return obj
    
    # Fallback: find any mesh with shape keys
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.data.shape_keys:
            if obj.animation_data and obj.animation_data.action:
                return obj
    
    return None


def find_faceit_control_rig():
    """Find Faceit control rig object."""
    # Look for object with 'FaceitControlRig' in name
    for obj in bpy.data.objects:
        if 'FaceitControlRig' in obj.name or 'control_rig' in obj.name.lower():
            return obj
    
    # Fallback: find armature with facial control bones
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            # Check for typical Faceit control bone names
            if any('c_eyelid' in bone.name or 'c_eye' in bone.name for bone in obj.data.bones):
                return obj
    
    return None

```

**UI Integration:**
Button enabled/disabled based on state:

* `NO_BAKE` state: Button disabled, message "Bake shape keys first"
* `NEEDS_CLEANUP` state: Button enabled
* `NEEDS_ACTIVATION` state: Button enabled
* `READY_TO_SAVE` state: Button disabled, message "Already activated"

### 2. Marker-Based Pose/Expression Creation

**Feature:** Convert timeline markers to pose/expression assets with intelligent naming and source tracking.

**User Story:** As an animator, I want to mark interesting moments in my mocap recording with timeline markers, then selectively export those markers as reusable expression assets while maintaining full traceability back to the source.

**Workflow Philosophy:**

* **Non-destructive editing:** Work directly in the blend file containing mocap data.
* **Marker-based interface:** Place markers at frames of interest rather than managing keyframe selections.
* **Selective export:** Export specific markers or all markers in batch.
* **Persistent history:** Saved blend file maintains record of which markers have been processed.
* **User-friendly naming:** Automatically sanitise marker names (whitespace → underscores, capitalise first letter).

**Implementation Requirements:**

#### Export Selected Marker(s)

* Detect selected marker(s) in timeline.
* Extract character name from control rig.
* Sanitise marker name: replace whitespace with underscores, capitalise first letter.
* Generate pose asset name: `FACE_[CHARACTER]_[Sanitised_Marker_Name]`.
* Extract control rig pose at marker frame.
* Save as pose asset to expressions library.
* Update manifest with source tracking.
* Mark marker as processed (custom marker property).
* Leave other markers intact for future processing.

#### Export All Markers

* Detect all timeline markers in control rig action.
* Filter out already-processed markers (if enabled).
* Batch process all remaining markers.
* Show progress indicator for batch operations.
* Generate summary report: "Exported 8 expressions from 12 markers (4 already processed)".

#### Marker Name Sanitisation

```python
def sanitise_marker_name(marker_name: str) -> str:
    """
    Sanitise marker name for use in asset naming.
    
    Rules:
    - Replace whitespace (spaces, tabs) with underscores
    - Capitalise first letter of each word
    - Remove special characters except underscores
    
    Examples:
    'happy face' → 'Happy_Face'
    'big SMILE' → 'Big_Smile'
    'confused   look' → 'Confused_Look'
    
    Args:
        marker_name: Raw marker name from timeline
        
    Returns:
        str: Sanitised name suitable for file/asset naming
    """
    # Replace whitespace with underscores
    sanitised = re.sub(r'\s+', '_', marker_name.strip())
    
    # Remove special characters except underscores
    sanitised = re.sub(r'[^a-zA-Z0-9_]', '', sanitised)
    
    # Capitalise first letter of each underscore-separated word
    words = sanitised.split('_')
    sanitised = '_'.join(word.capitalize() for word in words if word)
    
    return sanitised

```

#### Marker Processing State Tracking

```python
def mark_marker_as_processed(marker: bpy.types.TimelineMarker, 
                             asset_name: str, 
                             export_date: str):
    """
    Mark timeline marker as processed by storing metadata.
    
    Note: Blender markers don't support custom properties natively,
    so we track this in the manifest file instead.
    
    Args:
        marker: Timeline marker object
        asset_name: Full asset name that was created
        export_date: ISO date string when exported
    """
    # Store in manifest under special 'marker_state' section
    manifest_path = get_expression_manifest_path()
    manifest = load_manifest(manifest_path)
    
    if 'marker_state' not in manifest:
        manifest['marker_state'] = {}
    
    manifest['marker_state'][marker.name] = {
        'processed': True,
        'asset_name': asset_name,
        'frame': marker.frame,
        'export_date': export_date
    }
    
    save_manifest(manifest_path, manifest)


def is_marker_processed(marker: bpy.types.TimelineMarker) -> bool:
    """
    Check if marker has already been processed.
    
    Args:
        marker: Timeline marker to check
        
    Returns:
        bool: True if marker has been exported as asset
    """
    manifest_path = get_expression_manifest_path()
    manifest = load_manifest(manifest_path)
    
    marker_state = manifest.get('marker_state', {})
    marker_info = marker_state.get(marker.name, {})
    
    return marker_info.get('processed', False)

```

**Technical Details:**

```python
def export_selected_markers():
    """
    Export selected timeline marker(s) as expression pose assets.
    
    Returns:
        dict: {
            'success': bool,
            'markers_processed': int,
            'assets_created': list[str],
            'failed_markers': list[str],
            'errors': list[str]
        }
    """
    result = {
        'success': False,
        'markers_processed': 0,
        'assets_created': [],
        'failed_markers': [],
        'errors': []
    }
    
    # Get control rig and its action
    control_rig = find_faceit_control_rig()
    if not control_rig or not control_rig.animation_data or not control_rig.animation_data.action:
        result['errors'].append('No control rig action found')
        return result
    
    action = control_rig.animation_data.action
    
    # Get selected markers (or all markers if none selected)
    selected_markers = get_selected_timeline_markers(action)
    
    if not selected_markers:
        result['errors'].append('No markers selected in timeline')
        return result
    
    # Get character name
    character_name = get_character_name(control_rig)
    
    # Process each marker
    for marker in selected_markers:
        try:
            # Sanitise marker name
            sanitised_name = sanitise_marker_name(marker.name)
            
            # Generate asset name
            asset_name = f"FACE_{character_name}_{sanitised_name}"
            
            # Set timeline to marker frame
            bpy.context.scene.frame_set(marker.frame)
            
            # Create pose asset from current frame
            bpy.ops.poselib.create_pose_asset(
                pose_name=asset_name,
                activate_new_action=False
            )
            
            # Get source blend filename
            source_file = bpy.path.basename(bpy.data.filepath)
            
            # Update manifest
            update_expression_manifest(
                asset_name=asset_name,
                source_file=source_file,
                frame_range=(marker.frame, marker.frame),
                marker_name=marker.name,
                notes=f"From marker: {marker.name}"
            )
            
            # Mark marker as processed
            mark_marker_as_processed(
                marker=marker,
                asset_name=asset_name,
                export_date=datetime.now().strftime("%Y-%m-%d")
            )
            
            result['markers_processed'] += 1
            result['assets_created'].append(asset_name)
            
        except Exception as e:
            result['failed_markers'].append(marker.name)
            result['errors'].append(f"Failed to process marker '{marker.name}': {str(e)}")
    
    result['success'] = result['markers_processed'] > 0
    return result


def export_all_markers(skip_processed: bool = True):
    """
    Export all timeline markers as expression pose assets.
    
    Args:
        skip_processed: If True, skip markers already exported
        
    Returns:
        dict: Same structure as export_selected_markers()
    """
    control_rig = find_faceit_control_rig()
    if not control_rig or not control_rig.animation_data or not control_rig.animation_data.action:
        return {'success': False, 'errors': ['No control rig action found']}
    
    action = control_rig.animation_data.action
    markers = action.pose_markers if hasattr(action, 'pose_markers') else []
    
    # Filter markers if needed
    if skip_processed:
        markers = [m for m in markers if not is_marker_processed(m)]
    
    # Process all markers using same logic as export_selected_markers
    # ... (implementation similar to above)

```

**UI Integration:**

```
┌─ Expression Library (Marker-Based) ──┐
│ Selected Markers: [2]                 │
│ Total Markers: [15]                   │
│ Processed: [11]                       │
│ Remaining: [4]                        │
│                                       │
│ Character: [PATRICK] [GENERIC]        │
│                                       │
│ Source Recording:                     │
│ [Session_2025-01-16_001.blend]        │
│                                       │
│ [Export Selected Marker(s)]           │
│ [Export All Markers]                  │
│                                       │
│ Options:                              │
│ [✓] Skip Already Processed            │
│ [✓] Auto-sanitise Marker Names        │
│                                       │
│ Status: Ready                         │
└───────────────────────────────────────┘

```

### 3. Manifest Management

**Feature:** Automatic manifest file updates when creating pose/expression assets, with marker state tracking.

**User Story:** As an animator, I want the plugin to automatically track the source mocap for every expression I save, including which markers have been processed, so that I can always trace poses back to their original recordings and avoid duplicate exports.

**Implementation Requirements:**

* Load existing manifest JSON files.
* Validate JSON structure before modification.
* Add new entries when pose/expression assets are created.
* Track marker processing state to prevent duplicate exports.
* Preserve existing entries (never overwrite unless explicitly confirmed).
* Create backup before modification.

**Enhanced Manifest Structure:**

**Expression Manifest** (`_Library/Mocap/Face/Expression_Manifest.json`):

```json
{
  "expressions": {
    "FACE_PATRICK_Happy_Face": {
      "source_file": "Session_2025-01-16_001.blend",
      "frame": 120,
      "marker_name": "happy face",
      "export_date": "2025-01-16",
      "character": "Patrick",
      "notes": "From marker: happy face"
    },
    "FACE_PATRICK_Subtle_Smile": {
      "source_file": "Session_2025-01-16_001.blend",
      "frame": 248,
      "marker_name": "subtle smile",
      "export_date": "2025-01-16",
      "character": "Patrick",
      "notes": "From marker: subtle smile"
    }
  },
  "marker_state": {
    "happy face": {
      "processed": true,
      "asset_name": "FACE_PATRICK_Happy_Face",
      "frame": 120,
      "export_date": "2025-01-16"
    },
    "subtle smile": {
      "processed": true,
      "asset_name": "FACE_PATRICK_Subtle_Smile",
      "frame": 248,
      "export_date": "2025-01-16"
    },
    "big laugh": {
      "processed": false,
      "frame": 312,
      "export_date": null
    }
  },
  "metadata": {
    "version": "1.0",
    "last_updated": "2025-01-16T14:32:00",
    "total_expressions": 2,
    "total_markers": 3,
    "processed_markers": 2
  }
}

```

**Technical Details:**

```python
def update_expression_manifest(asset_name: str, 
                               source_file: str, 
                               frame_range: tuple,
                               marker_name: str = None,
                               notes: str = ""):
    """
    Update Expression_Manifest.json with new asset entry and marker state.
    
    Args:
        asset_name: Full expression asset name (e.g., 'FACE_PATRICK_Happy_Face')
        source_file: Source mocap filename (blend file)
        frame_range: Tuple of (start_frame, end_frame) or (frame, frame) for single frame
        marker_name: Original marker name before sanitisation
        notes: Optional user notes about the expression
        
    Returns:
        dict: {
            'success': bool,
            'manifest_path': str,
            'backup_created': bool,
            'entry_added': bool,
            'marker_updated': bool
        }
    """
    manifest_path = get_expression_manifest_path()
    
    # Create backup
    backup_result = create_manifest_backup(manifest_path)
    
    # Load existing manifest
    manifest = load_manifest(manifest_path)
    
    # Ensure structure exists
    if 'expressions' not in manifest:
        manifest['expressions'] = {}
    if 'marker_state' not in manifest:
        manifest['marker_state'] = {}
    if 'metadata' not in manifest:
        manifest['metadata'] = {}
    
    # Add expression entry
    manifest['expressions'][asset_name] = {
        "source_file": source_file,
        "frame": frame_range[0],  # Use start frame for single-frame exports
        "marker_name": marker_name,
        "export_date": datetime.now().strftime("%Y-%m-%d"),
        "character": extract_character_from_asset_name(asset_name),
        "notes": notes
    }
    
    # Update marker state if marker name provided
    if marker_name:
        manifest['marker_state'][marker_name] = {
            "processed": True,
            "asset_name": asset_name,
            "frame": frame_range[0],
            "export_date": datetime.now().strftime("%Y-%m-%d")
        }
    
    # Update metadata
    manifest['metadata']['version'] = "1.0"
    manifest['metadata']['last_updated'] = datetime.now().isoformat()
    manifest['metadata']['total_expressions'] = len(manifest['expressions'])
    manifest['metadata']['total_markers'] = len(manifest['marker_state'])
    manifest['metadata']['processed_markers'] = sum(
        1 for m in manifest['marker_state'].values() if m.get('processed', False)
    )
    
    # Save updated manifest
    save_manifest(manifest_path, manifest)
    
    return {
        'success': True,
        'manifest_path': manifest_path,
        'backup_created': backup_result['success'],
        'entry_added': True,
        'marker_updated': marker_name is not None
    }

```

## User Interface Design

### Panel Layout

**Location:** 3D Viewport → Sidebar (N-Panel) → EK_PV Tab

**Sections:**

#### Section 1: Motion Capture

```
┌─ Motion Capture (Non-Destructive) ───┐
│ Status: [NEEDS_CLEANUP]               │
│ Character: [PATRICK]                  │
│ Action: [c_eyelid_upper_r_action]     │
│                                       │
│ [Cleanup & Activate Control Rig]      │
│                                       │
│ Session Description:                  │
│ [Happy expressions]                   │
│                                       │
│ Current File:                         │
│ [Session_2025-01-16_001.blend]        │
│                                       │
│ [Save Mocap Recording]                │
│  Save blend file to mocap library     │
│                                       │
│ Note: Work directly in this file.     │
│ Markers and history persist on save.  │
└───────────────────────────────────────┘

```

#### Section 2: Expression Library

(Marker-Based)

```
┌─ Expression Library (Markers) ───────┐
│ Selected Markers: [2]                 │
│ Total Markers: [15]                   │
│ Processed: [11]                       │
│ Remaining: [4]                        │
│                                       │
│ Character: [PATRICK] [GENERIC]        │
│                                       │
│ Source Recording:                     │
│ [Session_2025-01-16_001.blend]        │
│                                       │
│ [Export Selected Marker(s)]           │
│ [Export All Markers]                  │
│                                       │
│ Options:                              │
│ [✓] Skip Already Processed            │
│ [✓] Auto-sanitise Marker Names        │
│     (space → _, capitalise)           │
│                                       │
│ [Refresh Marker State]                │
│                                       │
│ Status: 2 markers ready for export    │
└───────────────────────────────────────┘

```

## Plugin Architecture

### Module Structure

```
EK_PV/
├── __init__.py              # Plugin registration and metadata
├── operators/
│   ├── __init__.py
│   ├── mocap_cleanup.py     # NLA cleanup and control rig activation
│   ├── mocap_save.py        # Save blend file as mocap recording (non-destructive)
│   ├── marker_export.py     # Export selected/all markers as pose assets
│   ├── marker_utils.py      # Marker detection, selection, and sanitisation
│   ├── validate_setup.py    # Validate project paths and manifests
│   └── manifest_edit.py     # Manual manifest editor operator
├── ui/
│   ├── __init__.py
│   └── panel.py             # Main UI panel with marker-based workflow
├── utils/
│   ├── __init__.py
│   ├── naming.py            # Naming convention utilities including marker sanitisation
│   ├── paths.py             # Path resolution and validation
│   ├── validation.py        # Setup validation utilities
│   ├── manifest.py          # Manifest read/write with marker state tracking
│   ├── faceit_detection.py  # Detect Faceit actions, rigs, and workflow state
│   ├── nla_operations.py    # NLA Editor cleanup operations
│   └── asset_marking.py     # Asset Browser integration utilities
└── config/
    ├── __init__.py
    └── settings.py          # Plugin settings and preferences

```

### Operator Classes

```python
class EKPV_OT_CleanupActivateControlRig(bpy.types.Operator):
    """Cleanup NLA and activate control rig for editing"""
    bl_idname = "ekpv.cleanup_activate_control_rig"
    bl_label = "Cleanup & Activate Control Rig"
    
class EKPV_OT_SaveMocapRecording(bpy.types.Operator):
    """Save current blend file as mocap recording (non-destructive workflow)"""
    bl_idname = "ekpv.save_mocap_recording"
    bl_label = "Save Mocap Recording"
    bl_description = "Save blend file as mocap recording in _Library/Mocap/Face/LiveLink/"
    
class EKPV_OT_ExportSelectedMarkers(bpy.types.Operator):
    """Export selected timeline markers as expression pose assets"""
    bl_idname = "ekpv.export_selected_markers"
    bl_label = "Export Selected Marker(s)"
    bl_description = "Convert selected timeline markers to expression assets with automatic name sanitisation"
    
class EKPV_OT_ExportAllMarkers(bpy.types.Operator):
    """Export all timeline markers as expression pose assets"""
    bl_idname = "ekpv.export_all_markers"
    bl_label = "Export All Markers"
    bl_description = "Batch export all markers (optionally skip already processed)"
    
    skip_processed: bpy.props.BoolProperty(
        name="Skip Processed Markers",
        description="Skip markers that have already been exported",
        default=True
    )
    
class EKPV_OT_ValidatePaths(bpy.types.Operator):
    """Validate project paths and manifest files"""
    bl_idname = "ekpv.validate_paths"
    bl_label = "Validate Paths"
    
class EKPV_OT_EditManifest(bpy.types.Operator):
    """Open manifest editor dialog"""
    bl_idname = "ekpv.edit_manifest"
    bl_label = "Edit Manifest"
    
class EKPV_OT_RefreshMarkerState(bpy.types.Operator):
    """Refresh marker processing state from manifest"""
    bl_idname = "ekpv.refresh_marker_state"
    bl_label = "Refresh Marker State"
    bl_description = "Reload marker processing state from manifest file"

```

## Integration Points

### Blender Asset System

* Utilise `bpy.ops.asset.mark()` for pose marking.
* Configure asset tags programmatically.
* Integrate with Asset Browser UI.
* Respect Blender's asset library conventions.

### File System

* Cross-platform path handling (Windows/macOS/Linux).
* Graceful permission error handling.
* Directory creation with validation.
* File naming sanitisation.

## Configuration and Settings

### Plugin Preferences

```python
class EKPV_Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    project_root: bpy.props.StringProperty(
        name="Project Root",
        subtype='DIR_PATH'
    )
    
    mocap_export_path: bpy.props.StringProperty(
        name="Mocap Export Path",
        default="/Mocap/Facial/"
    )
    
    pose_library_path: bpy.props.StringProperty(
        name="Pose Library Path",
        default="/Assets/Library/Poses/Expressions/"
    )

```

### Settings Persistence

* Store settings in JSON file at project root: `[ProjectRoot]/_Config/ekpv_settings.json`
* Auto-load settings when project is opened.
* Fallback to plugin preferences if project settings unavailable.

## Error Handling

### Required Error Messages

* **Missing Project Root:** "Project root path not set. Please configure in Settings section."
* **Invalid Path:** "Path '[path]' is not accessible. Please verify permissions and path correctness."
* **No Active Recording:** "No active Faceit OSC recording detected. Please record or import mocap data first."
* **Missing Character:** "Cannot determine character name. Please ensure character rig is selected."
* **Write Permission Denied:** "Cannot write to '[path]'. Please check directory permissions."
* **Asset Library Exists:** "Asset library '[name]' already exists. Overwrite? [Yes] [No] [Rename]"

## Testing Requirements

### Unit Tests

* Naming convention generation (all variations).
* Path resolution and validation.
* Manifest read/write operations.
* Settings save/load functionality.

### Integration Tests

* Mocap action save with asset marking.
* Asset Browser catalog assignment.
* Expression asset creation and manifest update.
* Asset library configuration.
* Action append from saved .blend files.
* Manifest backup and recovery.

### User Acceptance Criteria

* All operations complete in under 2 seconds.
* Clear feedback messages for all operations.
* No data loss during export operations.
* Graceful handling of edge cases (missing data, invalid paths).

## Future Enhancements

### Phase 2 Features

* Batch pose export from multiple keyframes.
* Expression library validation tools.
* Character rig verification utilities.
* Automatic backup before mocap export.

### Phase 3 Features

* AI-driven expression naming suggestions.
* Mocap recording metadata editor.
* Pose asset preview thumbnails.
* Integration with PostgreSQL database.

### Phase 1 Features (Priority)

* **Mocap Action Import:** One-click append of saved mocap actions into current file.
* Browse and select .blend files from `_Library/Mocap/Face/LiveLink/`.
* Display action metadata (date, frame range, description, tags).
* Preview action data in Asset Browser.
* Append action and apply to selected character rig.
* Option to retarget to different character than original recording.
* Integration with Blender's native action system.