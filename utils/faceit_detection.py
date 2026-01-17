import bpy

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
            if hasattr(obj.data, 'bones'):
                if any('c_eyelid' in bone.name or 'c_eye' in bone.name for bone in obj.data.bones):
                    return obj
    
    return None

def get_character_name(control_rig):
    """
    Extract character name from control rig or scene.
    Defaults to 'GENERIC' or uses part of rig name.
    """
    if not control_rig:
        return "Unknown"
        
    # Heuristics:
    # If rig name is "PATRICK_FaceitControlRig", extract PATRICK
    name = control_rig.name
    if "_" in name:
        parts = name.split("_")
        # Assuming format like Character_Rig or Rig_Character
        # Just taking the first part if it looks like a name?
        if parts[0].isupper():
            return parts[0]
            
    return "GENERIC"

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
    mesh_obj = find_character_mesh()
    control_rig = find_faceit_control_rig()
    
    mesh_has_action = False
    if mesh_obj and mesh_obj.animation_data and mesh_obj.animation_data.action:
        mesh_has_action = True
    
    if not control_rig or not control_rig.animation_data or not control_rig.animation_data.action:
        return 'NO_BAKE'
    
    if mesh_has_action:
        return 'NEEDS_CLEANUP'
    
    # Check if control rig is in tweak mode (activated)
    # Tweak mode usually means use_tweak_mode is True on the animation_data
    if control_rig.animation_data.use_tweak_mode:
        return 'READY_TO_SAVE'
    else:
        return 'NEEDS_ACTIVATION'
