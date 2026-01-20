import os
import uuid
from pathlib import Path
from . import logger

def ensure_catalog_exists(library_root: Path, catalog_path: str) -> str:
    """
    Ensure a catalog exists in the blender_assets.cats.txt file at library_root.
    Returns the UUID of the catalog. 
    
    catalog_path example: "POSES/FACE"
    """
    cats_file = library_root / "blender_assets.cats.txt"
    
    # Format of cats.txt:
    # VERSION 1
    # UUID:catalog/path:SimpleName
    
    catalogs = {}
    
    if cats_file.exists():
        try:
            with open(cats_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('VERSION'):
                    continue
                parts = line.split(':')
                if len(parts) >= 2:
                    # UUID:path
                    cid = parts[0]
                    cpath = parts[1]
                    catalogs[cpath] = cid
        except Exception as e:
            logger.error(f"Error reading catalog file: {e}")
    
    # Check if exists
    if catalog_path in catalogs:
        return catalogs[catalog_path]
    
    # Create new
    new_uuid = str(uuid.uuid4())
    catalogs[catalog_path] = new_uuid
    
    # Save file
    try:
        with open(cats_file, 'w', encoding='utf-8') as f:
            f.write("VERSION 1\n\n")
            for path, cid in catalogs.items():
                # simple name is usually last part of path
                simple_name = path.split('/')[-1]
                f.write(f"{cid}:{path}:{simple_name}\n")
        logger.info(f"Created new asset catalog: {catalog_path}")
    except Exception as e:
        logger.error(f"Error writing catalog file: {e}")
        return None
        
    return new_uuid
