import sys

def log(message: str, level: str = "INFO"):
    """
    Log message to console with [EK_PV] prefix.
    Levels: INFO, WARNING, ERROR, DEBUG
    """
    prefix = "[EK_PV]"
    formatted = f"{prefix} [{level}] {message}"
    print(formatted) # Prints to system console
    
    # Optional: Log to Blender Info Editor (Report) logic is usually handled by operators, 
    # but we can try to find a context if needed. 
    # For now, system console is best for debugging.

def debug(message: str):
    log(message, "DEBUG")

def info(message: str):
    log(message, "INFO")

def warning(message: str):
    log(message, "WARNING")

def error(message: str):
    log(message, "ERROR")
