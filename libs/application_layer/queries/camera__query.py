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
        Get camera information by unique identifier.
        
        This method scans all cameras to find the matching unique_id.
        Note: This can be slow if there are many cameras, but it ensures
        we get the current index for the camera.
        """
        try:
            # Scan all cameras and find the one with matching unique_id
            # Use asyncio.wait_for to prevent hanging if scan takes too long
            cameras = await asyncio.wait_for(
                self.scan_available_cameras_async(),
                timeout=180.0  # 3 minutes timeout for scanning (allows for slow cameras)
            )
            for camera in cameras:
                if camera.unique_id == unique_id:
                    return camera
            return None
        except asyncio.TimeoutError:
            # If scan times out, log error but don't crash
            from common.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Timeout scanning cameras to find unique_id '{unique_id}'")
            return None
        except Exception as e:
            from common.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error getting camera by unique_id '{unique_id}': {e}")
            return None

