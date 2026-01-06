# common/camera_info.py
"""Camera information and unique identification."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CameraInfo:
    """
    Information about a camera device with unique identification.
    
    Attributes:
        unique_id: Unique identifier for the camera (device name, VID/PID, or hash)
        index: OpenCV camera index (may change, use unique_id for stable identification)
        name: Human-readable camera name (optional)
        vid: USB Vendor ID (optional, for USB cameras)
        pid: USB Product ID (optional, for USB cameras)
    """
    unique_id: str
    index: int
    name: Optional[str] = None
    vid: Optional[int] = None
    pid: Optional[int] = None
    
    def __str__(self) -> str:
        """String representation of camera info."""
        if self.name:
            return f"{self.name} (ID: {self.unique_id}, Index: {self.index})"
        return f"Camera {self.index} (ID: {self.unique_id})"

