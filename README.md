# EK_PV (Easy Killer Pre-Visualisation Tools)

**EK_PV** is a custom Blender add-on designed to automate the AI Blender Pre-Viz workflow. It focuses on non-destructive editing of motion capture data, marker-based expression extraction, and organized asset management.

## Features

### 1. Motion Capture Workflow
*   **Non-Destructive Cleanup:** Automates the cleanup of Faceit shape key bakes.
    *   Removes baked actions from Mesh Object and Shape Keys.
    *   Selects and activates the Control Rig for immediate refinement.
*   **Session Recording:**
    *   Saves the current work state as a persistent session file.
    *   Automatically handles naming conventions (`Session_YYYY-MM-DD_###.blend`).
    *   Saves to project library: `_Library/Mocap/Face/LiveLink/`.
    *   Switches context to the saved file to allow continued work.

### 2. Expression Library (Marker-Based)
*   **Marker Export:** Convert timeline markers into reusable Pose Assets.
    *   **Export Selected:** Process only currently selected timeline markers.
    *   **Export All:** Batch process all markers (optionally skipping already processed ones).
*   **Smart Sanitization:** Automatically converts marker names to asset-friendly formats (e.g., "big smile" → `FACE_CHARACTER_Big_Smile`).
*   **Automated Extraction:** Uses NLA Baking to capture the exact visual pose, handling constraints and drivers automatically.
*   **Asset Management:**
    *   Saves each expression as a separate .blend file in `_Library/Expressions/[Character]/`.
    *   Marks actions as Assets with tags (`facial`, `[character_name]`).

### 3. Manifest Tracking
*   **Automatic Tracking:** Every exported expression is logged in `Expression_Manifest.json`.
*   **Metadata:** Tracks source file, frame number, original marker name, and export date.
*   **State Management:** Remembers which markers have been processed to prevent duplicates.

## Installation

1.  Download the repository or zip the `EK_PV` folder.
2.  In Blender, go to **Edit > Preferences > Add-ons**.
3.  Click **Install...** and select the zip file.
4.  Enable the **EK_PV** add-on.
5.  In the Add-on Preferences, set the **Project Root** directory (usually the parent folder of your `_Library`).

## Usage

### Panel Location
**3D Viewport > Sidebar (N-Panel) > EK_PV Tab**

### Workflow Guide
1.  **Import & Bake:** Import your Faceit recording and bake shape keys to the Control Rig.
2.  **Cleanup:** Click **Cleanup & Activate Control Rig** to prepare the scene for editing.
3.  **Refine & Mark:** Scrub the timeline. When you find a good expression, add a marker (`M`) and name it (e.g., "Surprise").
4.  **Export Expressions:**
    *   Select markers and click **Export Selected Marker(s)**.
    *   Or click **Export All Markers** to batch process.
5.  **Save Session:** Click **Save Mocap Recording** to save your progress to the library.

## Development

### Structure
*   `operators/`: logic for cleanup, saving, and exporting.
*   `utils/`: shared helpers for paths, naming, and manifest JSON handling.
*   `ui/`: panel layout and interface logic.
*   `config/`: preferences and settings.

### Testing
Unit tests for utility functions are located in `tests/`.
Run tests via CLI:
```bash
PYTHONPATH=. python3 tests/test_utils.py
```

## Requirements
*   Blender 4.1+
*   Faceit Add-on (for control rig detection)