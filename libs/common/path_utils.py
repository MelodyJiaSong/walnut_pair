# common/path_utils.py
"""
Path utilities for cross-platform path handling.
Detects environment (WSL vs Windows) and normalizes paths accordingly.
"""
import os
import platform
from pathlib import Path
from typing import Optional


def is_wsl() -> bool:
    """
    Detect if running in WSL (Windows Subsystem for Linux).
    
    Returns:
        True if running in WSL, False otherwise.
    """
    # Check for WSL-specific environment variables
    if os.environ.get("WSL_DISTRO_NAME"):
        return True
    
    # Check for WSL in uname
    try:
        uname = platform.uname()
        if "microsoft" in uname.release.lower() or "wsl" in uname.release.lower():
            return True
    except Exception:
        pass
    
    # Check if running on Linux but with Windows paths accessible
    if platform.system() == "Linux":
        # Check if /mnt/c exists (WSL mounts Windows drives)
        if Path("/mnt/c").exists():
            return True
    
    return False


def is_windows() -> bool:
    """
    Detect if running on Windows (native, not WSL).
    
    Returns:
        True if running on native Windows, False otherwise.
    """
    return platform.system() == "Windows" and not is_wsl()


def normalize_path(path: str, base_path: Optional[str] = None) -> str:
    """
    Normalize a path based on the current environment.
    
    Converts paths between WSL and Windows formats:
    - WSL: /home/dalu/... -> /home/dalu/...
    - Windows: /home/dalu/... -> c:/... (removes /home/dalu prefix)
    
    The mapping assumes:
    - WSL root: /home/dalu
    - Windows root: c:/
    
    So /home/dalu/workspace/... becomes c:/workspace/... on Windows.
    
    Args:
        path: The path to normalize (can be absolute or relative)
        base_path: Optional base path for relative path resolution
        
    Returns:
        Normalized path string for the current environment.
    """
    path_str = str(path).strip()
    
    # Check if it's a WSL path (/home/dalu/...) on Windows
    if is_windows() and path_str.startswith("/home/dalu/"):
        # Convert /home/dalu/workspace/... to c:/workspace/...
        # Remove /home/dalu prefix and convert to Windows path
        relative_part = path_str.replace("/home/dalu/", "")
        # Build Windows path using Path for proper handling
        normalized = Path("c:/") / relative_part
        # Return as Windows path string
        return str(normalized)
    
    # Check if it's a Windows path (c:/...) on WSL
    if is_wsl() and (path_str.startswith("c:/") or path_str.startswith("C:/") or path_str.startswith("c:\\") or path_str.startswith("C:\\")):
        # Convert c:/workspace/... to /home/dalu/workspace/...
        # Remove c:/ prefix and add /home/dalu prefix
        relative_part = path_str.replace("c:/", "").replace("C:/", "").replace("c:\\", "").replace("C:\\", "").replace("\\", "/")
        normalized = Path("/home/dalu") / relative_part
        return str(normalized)
    
    # For other paths, use Path to resolve
    path_obj = Path(path)
    
    # If path is already absolute and matches current environment, return as-is
    if path_obj.is_absolute():
        return str(path_obj.resolve())
    
    # Relative path - resolve against base_path or current working directory
    if base_path:
        base = Path(base_path)
        resolved = (base / path_obj).resolve()
    else:
        resolved = path_obj.resolve()
    
    return str(resolved)


def get_workspace_root() -> Path:
    """
    Get the workspace root path based on the current environment.
    
    Returns:
        Path object pointing to the workspace root.
    """
    if is_wsl():
        return Path("/home/dalu/workspace")
    elif is_windows():
        return Path("c:/workspace")
    else:
        # Fallback to current working directory
        return Path.cwd()

