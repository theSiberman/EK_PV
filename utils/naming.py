import re
from datetime import datetime

def get_session_filename(date_obj: datetime, session_number: int) -> str:
    """
    Generate filename: Session_[DATE]_[###].blend
    Example: Session_2025-01-16_001.blend
    """
    date_str = date_obj.strftime("%Y-%m-%d")
    return f"Session_{date_str}_{session_number:03d}.blend"

def get_pose_asset_name(character_name: str, expression_name: str, index: int = None) -> str:
    """
    Generate pose asset name.
    Format: FACE_[CHARACTER]_[Expression]
    Or if index provided: FACE_[CHARACTER]_[Expression]_[##]
    
    Args:
        character_name: Name of the character (will be uppercased)
        expression_name: Descriptive name of the expression
        index: Optional integer for sequential numbering (1-based)
        
    Returns:
        Formatted string
    """
    char_part = character_name.upper()
    # Sanitize expression name: remove non-alphanumeric/underscore, ensure no leading/trailing spaces
    # We allow spaces in input but replace them or remove them? 
    # Spec examples don't show spaces in the final name (e.g. FACE_PATRICK_Smile_Confident)
    # I'll replace spaces with underscores and remove other special chars
    
    clean_expr = expression_name.strip().replace(" ", "_")
    clean_expr = re.sub(r'[^a-zA-Z0-9_]', '', clean_expr)
    clean_expr = clean_expr.strip("_")
    
    name = f"FACE_{char_part}_{clean_expr}"
    
    if index is not None:
        name = f"{name}_{index:02d}"
        
    return name

def sanitise_marker_name(marker_name: str) -> str:
    """
    Sanitise marker name for use in asset naming.
    
    Rules:
    - Replace whitespace (spaces, tabs) with underscores
    - Capitalise first letter of each word
    - Remove special characters except underscores
    
    Examples:
    'happy face' -> 'Happy_Face'
    'big SMILE' -> 'Big_Smile'
    'confused   look' -> 'Confused_Look'
    """
    # Replace whitespace with underscores
    sanitised = re.sub(r'\s+', '_', marker_name.strip())
    
    # Remove special characters except underscores
    sanitised = re.sub(r'[^a-zA-Z0-9_]', '', sanitised)
    
    # Capitalise first letter of each underscore-separated word
    words = sanitised.split('_')
    sanitised = '_'.join(word.capitalize() for word in words if word)
    
    return sanitised

def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be safe for filenames.
    """
    # Keep alphanumeric, dot, underscore, hyphen
    clean = re.sub(r'[^a-zA-Z0-9._-]', '', name)
    return clean
