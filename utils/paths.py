import os
from pathlib import Path
from typing import Optional

def get_library_path(project_root: str) -> Path:
    """
    Find the library directory in the project root.
    Prioritizes a folder named '_Library'.
    If not found, searches for '_[ProjectName]_Library'.
    Defaults to '[project_root]/_Library'.
    """
    root = Path(project_root)
    default_lib = root / "_Library"
    
    if default_lib.exists():
        return default_lib
        
    # Search for folder matching _*_Library
    try:
        if root.exists():
            for item in root.iterdir():
                if item.is_dir() and item.name.startswith("_") and item.name.endswith("_Library"):
                    return item
    except OSError:
        pass # Permission errors or invalid paths
        
    return default_lib

def get_mocap_dir(project_root: str, ensure: bool = False) -> Path:
    """
    Get the directory for saving mocap sessions.
    Path: [Library]/Mocap/Face/LiveLink/
    """
    lib_path = get_library_path(project_root)
    mocap_dir = lib_path / "Mocap" / "Face" / "LiveLink"
    
    if ensure:
        mocap_dir.mkdir(parents=True, exist_ok=True)
        
    return mocap_dir

def get_expression_dir(project_root: str, character_name: str, ensure: bool = False) -> Path:
    """
    Get the directory for saving expression poses.
    Path: [Library]/Expressions/[CHARACTER_NAME]/
    """
    lib_path = get_library_path(project_root)
    # Character name usually upper in paths? Spec examples show character folder.
    # Spec: .../Expressions/[CHARACTER_NAME]/
    # Example: .../Expressions/PATRICK/
    
    expr_dir = lib_path / "Expressions" / character_name
    
    if ensure:
        expr_dir.mkdir(parents=True, exist_ok=True)
        
    return expr_dir

def get_manifest_path(project_root: str, manifest_type: str = "expression") -> Path:
    """
    Get path to manifest file.
    
    Args:
        project_root: Root path
        manifest_type: 'expression' or 'body'
    
    Returns:
        Path object
    """
    lib_path = get_library_path(project_root)
    
    if manifest_type == "expression":
        # Spec: _[PROJECT]_Library/Mocap/Face/Expression_Manifest.json
        return lib_path / "Mocap" / "Face" / "Expression_Manifest.json"
    elif manifest_type == "body":
        return lib_path / "Mocap" / "Body" / "Pose_Manifest.json"
    
    raise ValueError(f"Unknown manifest type: {manifest_type}")
