# application_layer/queries/camera__query.py
"""Query service for camera operations."""
import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional

from common.camera_info import CameraInfo
from infrastructure_layer.services.camera__service import ICameraService


class ICameraQuery(ABC):
    """Interface for camera queries."""

    @abstractmethod
    async def scan_available_cameras_async(self) -> List[CameraInfo]:
        """
        Scan for available cameras with unique identifiers.
        
        Returns:
            List of CameraInfo objects with unique identifiers
        """
        pass

    @abstractmethod
    async def test_camera_async(self, index: int) -> bool:
        """
        Test if a specific camera is available.
        
        Args:
            index: Camera device index
            
        Returns:
            True if camera is available, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_camera_by_unique_id_async(self, unique_id: str) -> Optional[CameraInfo]:
        """
        Get camera information by unique identifier.
        
        Args:
            unique_id: Unique camera identifier
            
        Returns:
            CameraInfo if found, None otherwise
        """
        pass


class CameraQuery(ICameraQuery):
    """Implementation of camera query service."""

    def __init__(self, camera_service: ICameraService, max_scan_index: int = 15) -> None:
        """
        Initialize the query service.
        
        Args:
            camera_service: Camera service for testing cameras
            max_scan_index: Maximum camera index to scan (default: 15)
        """
        self.camera_service: ICameraService = camera_service
        self.max_scan_index: int = max_scan_index

    async def scan_available_cameras_async(self) -> List[CameraInfo]:
        """Scan for available cameras with unique identifiers."""
        return await self.camera_service.scan_available_cameras_async(self.max_scan_index)

    async def test_camera_async(self, index: int) -> bool:
        """Test if a specific camera is available."""
        return await self.camera_service.test_camera_available_async(index)
    
    async def get_camera_by_unique_id_async(self, unique_id: str) -> Optional[CameraInfo]:
        """
        Get camera information by unique identifier (logical ID).
        
        Scans cameras if needed to ensure mapping is up to date.
        """
        # First try to get from mapping
        camera = await self.camera_service.get_camera_by_unique_id_async(unique_id)
        if camera:
            return camera
        
        # If not found, rescan to update mapping
        try:
            cameras = await asyncio.wait_for(
                self.scan_available_cameras_async(),
                timeout=180.0
            )
            # Try again after rescan
            return await self.camera_service.get_camera_by_unique_id_async(unique_id)
        except asyncio.TimeoutError:
            from common.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Timeout scanning cameras to find unique_id '{unique_id}'")
            return None
        except Exception as e:
            from common.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error getting camera by unique_id '{unique_id}': {e}")
            return None

