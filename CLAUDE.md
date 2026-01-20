# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EK_PV** is a Blender add-on (Python 3.11+, Blender 5.0+) that automates motion capture workflows for AI-driven pre-visualization. It provides three main features:

1. **Cleanup & Activate Control Rig** — Non-destructive cleanup of Faceit shape key bakes, removing animation data from mesh while preserving control rig
2. **Marker-Based Expression Export** — Convert timeline markers to reusable pose assets using NLA baking for visual accuracy
3. **Manifest Tracking** — Automatic JSON-based tracking of exported expressions with session-specific marker state to prevent duplicate exports

The plugin enforces a session-based workflow: mocap recordings are saved as persistent `.blend` files that maintain all markers (processed and unprocessed) for iterative refinement.

## Build & Test Commands

**Run Tests:**
```bash
PYTHONPATH=. python3 tests/test_utils.py
```

**Run Specific Test Suite:**
```bash
PYTHONPATH=. python3 -m unittest tests.test_utils.TestNaming -v
```

**Run Single Test:**
```bash
PYTHONPATH=. python3 -m unittest tests.test_utils.TestManifest.test_update_manifest -v
```

## Installation & Development

1. Clone this repository
2. In Blender, go to **Edit > Preferences > Add-ons > Install...**
3. Select the repository folder as a zip or use a symlink
4. In Add-on Preferences, set **Project Root** (parent directory of `_Library`)
5. Reload the add-on via F9 console: `bpy.ops.preferences.addon_refresh()` if making changes

## Code Architecture

### Module Structure

**`operators/`** — Blender operators (actions triggered by UI buttons)
- `mocap_cleanup.py` — `EKPV_OT_CleanupActivateControlRig`: Removes NLA/shape key animation from mesh, sets control rig active/selected, enters pose mode
- `mocap_save.py` — `EKPV_OT_SaveMocapAction`: "Save As" current file to `_Library/Mocap/Face/LiveLink/` with session filename format
- `marker_export.py` — Two operators for exporting markers:
  - `EKPV_OT_ExportSelectedMarkers`: Exports currently selected timeline markers
  - `EKPV_OT_ExportAllMarkers`: Batch exports all markers, with option to skip already-processed ones

**`utils/`** — Shared utilities (not Blender-specific; fully testable)
- `manifest.py` — Loads/saves `Expression_Manifest.json` with nested session tracking and collision detection
- `naming.py` — Marker sanitization (`"happy face"` → `"Happy_Face"`) and unique asset name generation (`FACE_[CHARACTER]_[Name]_##`)
- `paths.py` — Library path resolution (finds `_Library` or named variants like `_MyProject_Library`)
- `catalogs.py` — Asset catalog (`blender_assets.cats.txt`) management for `POSES/FACE` organization
- `logger.py` — Console logging with `[EK_PV]` prefix for debugging
- `faceit_detection.py` — Detects character mesh (HG_Body, Body, etc.) and Faceit control rig

**`ui/`** — User interface
- `panel.py` — N-Panel (sidebar) UI layout with three sections: Cleanup status, Marker stats, Export controls

**`config/`** — Settings & preferences
- `settings.py` — Blender property group for add-on preferences (Project Root, default character name, etc.)

### Key Data Flow: Expression Export

1. **User clicks "Export Selected Marker(s)"** → `marker_export.py` operator
2. **Validate**: Current file must be saved (has a filename)
3. **Sanitize**: Extract marker name, convert to `Happy_Face` format
4. **Generate unique name**: Create `FACE_CHARACTER_Happy_Face`, check for collisions in manifest
5. **NLA Bake**: Use `bpy.ops.nla.bake` to visually capture the pose without manual copy/paste
6. **Create asset**: New Action assigned to Asset Catalog `POSES/FACE`
7. **Save**: Export to `_Library/Expressions/[CHARACTER]/[ASSET_NAME].blend`
8. **Update manifest**: Log in `Expression_Manifest.json` with session-specific marker state to prevent re-export

### Manifest Structure

The JSON manifest tracks two things:
- **`expressions`** — Global registry of all exported asset names with metadata (source file, frame, export date)
- **`marker_state`** — Nested by session file, then by marker name, tracking `processed` status and collision-handling details

This prevents duplicate exports across different session files while allowing the same marker name to be used in different files.

### Key Architectural Principles

- **Session Enforcement**: Users must save the mocap file before exporting markers (prevents orphaned expressions)
- **Non-destructive Cleanup**: Only removes animation from mesh; control rig animation preserved
- **Visual NLA Baking**: Captures exact visual pose including constraints and drivers (not a manual keyframe copy)
- **Persistent History**: Manifest stays in the working file; markers can be refined and re-exported iteratively
- **Path Flexibility**: Detects library path (`_Library`, `_MyProject_Library`, etc.) to support multiple project structures

## Common Development Tasks

### Add a New Operator

1. Create new class in `operators/[feature].py` inheriting from `bpy.types.Operator`
2. Define `bl_idname` (e.g., `"ekpv.my_operator"`) and `bl_label`
3. Implement `execute()` method (return `{'FINISHED'}` or `{'CANCELLED'}`)
4. Add class to `operators/__init__.py` `classes` tuple and `register()`/`unregister()`
5. Add UI button in `ui/panel.py` using `layout.operator("ekpv.my_operator")`

### Modify Manifest Tracking

- Core logic: `utils/manifest.py` `update_expression_manifest()` — takes asset name, session file, marker name, frame, and optional notes
- Always call `create_backup()` before modifying to preserve history
- Update tests in `tests/test_utils.py` for any schema changes

### Detect Objects in Scene

- Use `faceit_detection.find_character_mesh()` to find the mesh (checks common names: HG_Body, Body, etc.)
- Use `faceit_detection.find_control_rig()` to find Faceit control rig
- Extend these functions if supporting new character rigs

### Handle Blender Version Differences

- Wrap version-specific calls with try/except (operators in 5.0+ may differ from future versions)
- Log warnings for graceful fallbacks; don't crash on missing attributes
- Target Blender 5.0+ per `REQUIREMENTS.md`

## Important File References

- **REQUIREMENTS.md** — Full technical specification with workflow philosophy and error handling strategy
- **README.md** — User-facing documentation with installation and usage instructions
- **`bl_info`** in `__init__.py` — Add-on metadata (version, category, Blender version requirement)

## Testing Strategy

Tests use Python's `unittest` framework without Blender context (utilities are pure Python):
- **TestNaming** — Marker sanitization and asset naming logic
- **TestPaths** — Library path detection with fallback rules
- **TestManifest** — JSON serialization, backup creation, nested session tracking

When adding new utility functions, add corresponding tests. Operators cannot be easily unit-tested outside Blender but can delegate logic to testable utility functions.
