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

**Feature:** Automate cleanup after shape key baking—remove animation data from mesh and shape keys, and select the control rig for refinement.

**Workflow Context:**
After using Faceit's "Bake Shape Keys to Control Rig" function:
* Animation data exists on the mesh object (Transforms).
* Animation data exists on the mesh shape keys.
* Control rig has the baked action.
* Cleanup is required to ensure only the control rig drives the performance.

**Implementation Requirements:**
* Detect character mesh object (`HG_Body`, `Body`, etc.).
* Remove active action from the mesh object.
* Remove active action from the mesh's shape keys animation data.
* Detect Faceit control rig object.
* Set control rig as active and selected.
* Switch control rig to **Pose Mode** for immediate editing.

**State Detection:**
The plugin detects the workflow state to guide the user:
* `NO_BAKE`: No action found on the control rig.
* `NEEDS_CLEANUP`: Control rig has an action, but mesh still has animation data.
* `READY_TO_SAVE`: Mesh is clean, rig is selected and ready for refinement/export.

### 2. Marker-Based Pose/Expression Creation

**Feature:** Convert timeline markers to pose/expression assets with automated visual baking and session-specific tracking.

**Workflow Philosophy:**
* **Session Enforcement:** Users MUST save the mocap recording as a session file before exporting markers.
* **Non-destructive sampling:** Use `bpy.ops.nla.bake` to capture visual poses without manual copy/paste.
* **Marker-based interface:** Place markers at frames of interest.
* **Persistent history:** Manifest tracks markers per session file to allow duplicate marker names across different files.

**Implementation Requirements:**

#### Export Selected Marker(s)
* Validate that the current file is saved and not dirty.
* Detect selected marker(s).
* Sanitise marker name: replace whitespace with underscores, capitalise words.
* Generate a **Unique Asset Name**: `FACE_[CHARACTER]_[Sanitised_Name]`, appending `_##` numerical suffixes if collisions occur in the global library.
* Move timeline to marker frame.
* Perform **Visual NLA Bake** for the selected bones to a new Action.
* Assign the asset to the **Asset Catalog** `POSES/FACE`.
* Save the pose action to `_Library/Expressions/[CHARACTER]/[ASSET_NAME].blend`.
* Update manifest with session-specific marker state.

#### Export All Markers
* Filter timeline markers based on the manifest's processed state for the **current session file**.
* Batch process eligible markers using the same logic as selective export.

#### Marker Name Sanitisation
* Whitespace → `_`
* Special characters removed.
* Words capitalised (e.g., `happy face` → `Happy_Face`).

### 3. Manifest Management

**Feature:** Automatic manifest file updates with nested session tracking and collision prevention.

**Manifest Structure (`Expression_Manifest.json`):**
* `expressions`: Global registry of all exported pose assets.
* `marker_state`: Nested dictionary mapping `source_file` -> `marker_name` -> `processing_details`.
* `metadata`: Versioning and aggregate stats.

**Example Structure:**
```json
{
  "expressions": {
    "FACE_PATRICK_Subtle_Smile": { ... }
  },
  "marker_state": {
    "Session_2026-01-20_001.blend": {
      "subtle smile": {
        "processed": true,
        "asset_name": "FACE_PATRICK_Subtle_Smile",
        "frame": 248,
        "export_date": "2026-01-20"
      }
    }
  }
}
```

### 4. Asset Catalog Management

**Feature:** Automated management of `blender_assets.cats.txt` to ensure organized asset libraries.

**Implementation:**
* Locate `blender_assets.cats.txt` in the library root.
* Ensure the path `POSES/FACE` exists.
* Automatically generate and track UUIDs for catalogs.
* Assign the correct `catalog_id` to exported pose assets during the export process.

## User Interface Design

### Panel Layout (N-Panel > EK_PV)

**Section 1: Motion Capture (Non-Destructive)**
* **Status Display**: Real-time feedback on workflow state.
* **Cleanup & Activate Control Rig**: One-click cleanup.
* **Save Mocap Recording**: "Save As" the current file into the mocap library and switch context to it.

**Section 2: Expression Library (Markers)**
* **Marker Statistics**: Displays counts for selected, total, and remaining markers for the current file.
* **Export Selected Marker(s)**: Actionable only if file is saved.
* **Export All Markers**: With "Skip Already Processed" option.
* **Naming Info**: Details on automatic sanitization and character detection.

## Plugin Architecture

* `operators/`:
    * `mocap_cleanup.py`: NLA/ShapeKey cleanup logic.
    * `mocap_save.py`: Session "Save As" logic.
    * `marker_export.py`: Bake-based asset extraction.
* `utils/`:
    * `catalogs.py`: Asset catalog management (`cats.txt`).
    * `manifest.py`: JSON manifest with nested session tracking.
    * `naming.py`: Marker sanitisation and unique name generation.
    * `paths.py`: Library path resolution.
    * `logger.py`: Console debugging with `[EK_PV]` prefix.
* `ui/`:
    * `panel.py`: Marker-centric UI layout.

## Error Handling
* **Unsaved File**: Blocks marker export until a session file is established.
* **Missing Project Root**: Guides user to Add-on Preferences.
* **Read-only Attributes**: Handled by managing NLA Tweak Mode state during automation.
* **Attribute Errors**: Graceful fallbacks for different Blender versions/Faceit setups.

## Requirements Summary
* **Blender**: 4.1+ (Tested on 5.1 Alpha)
* **Python**: 3.11+
* **Dependencies**: Faceit (for control rig detection), HumanGenerator (optional mesh detection).
