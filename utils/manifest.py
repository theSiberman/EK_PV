import json
import shutil
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple
from . import logger

def create_backup(manifest_path: Path) -> Path:
    """
    Create a timestamped backup of the manifest file.
    Returns the path to the backup.
    """
    if not manifest_path.exists():
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = manifest_path.parent / f"{manifest_path.stem}_BACKUP_{timestamp}.json"
    
    try:
        shutil.copy2(manifest_path, backup_path)
        logger.debug(f"Manifest backup created: {backup_path}")
        return backup_path
    except OSError as e:
        logger.warning(f"Failed to create backup: {e}")
        return None

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load manifest JSON. Returns empty dict if file doesn't exist or is invalid.
    """
    if not manifest_path.exists():
        logger.debug(f"Manifest not found at {manifest_path}, starting fresh.")
        return {}
        
    try:
        if manifest_path.stat().st_size == 0:
            logger.debug(f"Manifest file {manifest_path} is empty, initializing fresh.")
            return {}
            
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Error loading manifest {manifest_path}: {e}")
        return {}

def save_manifest(manifest_path: Path, data: Dict[str, Any]) -> bool:
    """
    Save data to manifest JSON.
    """
    try:
        # Ensure directory exists
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Manifest saved to {manifest_path}")
        return True
    except OSError as e:
        logger.error(f"Error saving manifest {manifest_path}: {e}")
        return False

def update_expression_manifest(
    project_root: str,
    asset_name: str,
    source_file: str,
    frame_range: Tuple[int, int],
    marker_name: str = None,
    notes: str = ""
) -> Dict[str, Any]:
    """
    Update Expression_Manifest.json with new asset entry and marker state.
    
    Args:
        project_root: Root path
        asset_name: Full expression asset name
        source_file: Source mocap filename
        frame_range: Tuple of (start_frame, end_frame)
        marker_name: Original marker name before sanitisation
        notes: Optional user notes
        
    Returns:
        dict with success status and details
    """
    from .paths import get_manifest_path
    from .naming import get_pose_asset_name # Helper if needed, but we pass asset_name
    
    manifest_path = get_manifest_path(project_root, "expression")
    
    # Create backup
    backup_path = create_backup(manifest_path)
    
    # Load existing manifest
    manifest = load_manifest(manifest_path)
    
    # Ensure structure exists
    if 'expressions' not in manifest:
        manifest['expressions'] = {}
    if 'marker_state' not in manifest:
        manifest['marker_state'] = {}
    if 'metadata' not in manifest:
        manifest['metadata'] = {}
        
    # Extract character name from asset name (FACE_CHARNAME_Expression)
    parts = asset_name.split('_')
    character = parts[1] if len(parts) > 1 else "Unknown"
    
    # Add expression entry
    manifest['expressions'][asset_name] = {
        "source_file": source_file,
        "frame": frame_range[0],
        "marker_name": marker_name,
        "export_date": datetime.now().strftime("%Y-%m-%d"),
        "character": character,
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
    success = save_manifest(manifest_path, manifest)
    
    if success:
        logger.info(f"Manifest updated for asset: {asset_name}")
    else:
        logger.error(f"Failed to update manifest for asset: {asset_name}")
    
    return {
        'success': success,
        'manifest_path': str(manifest_path),
        'backup_created': backup_path is not None,
        'entry_added': True,
        'marker_updated': marker_name is not None
    }
