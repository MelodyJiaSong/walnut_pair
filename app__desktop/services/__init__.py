# app__desktop/services/__init__.py
"""Desktop application services."""
from .camera_capture_service import CameraCaptureService
from .camera_side_mapping__service import CameraSideMappingService

__all__ = [
    "CameraCaptureService",
    "CameraSideMappingService",
]

