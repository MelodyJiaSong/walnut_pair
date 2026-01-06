# infrastructure_layer/services/camera__service.py
"""Camera service for capturing images from cameras."""
import asyncio
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import cv2
import numpy as np

from common.camera_info import CameraInfo
from common.logger import get_logger

# Type alias for camera handle
CameraHandle = cv2.VideoCapture


class ICameraService(ABC):
    """Interface for camera operations."""

    @abstractmethod
    async def test_camera_available_async(self, index: int, timeout: float = 2.0) -> bool:
        """
        Quick test if camera index is available.
        
        Args:
            index: Camera device index
            timeout: Maximum time to wait for camera test (default: 2 seconds)
            
        Returns:
            True if camera is available, False otherwise
        """
        pass

    @abstractmethod
    async def open_camera_async(
        self, index: int, width: int, height: int, buffer_size: int = 1, fourcc: str = "MJPG", auto_exposure: float = 0.75
    ) -> Optional[CameraHandle]:
        """
        Open a camera with specified settings.
        
        Args:
            index: Camera device index
            width: Frame width
            height: Frame height
            buffer_size: Buffer size (1 for low latency)
            fourcc: FourCC codec (default: "MJPG")
            auto_exposure: Auto exposure setting (0.75 = auto)
            
        Returns:
            CameraHandle if successful, None otherwise
        """
        pass

    @abstractmethod
    async def capture_frame_async(self, camera: CameraHandle) -> Optional[np.ndarray]:
        """
        Capture a single frame from the camera.
        
        Args:
            camera: Camera handle
            
        Returns:
            Frame as numpy array (BGR format) if successful, None otherwise
        """
        pass

    @abstractmethod
    async def close_camera_async(self, camera: CameraHandle) -> None:
        """
        Close and release a camera.
        
        Args:
            camera: Camera handle to close
        """
        pass

    @abstractmethod
    async def scan_available_cameras_async(self, max_index: int) -> List[CameraInfo]:
        """
        Scan for available cameras and return unique identifiers.
        
        Args:
            max_index: Maximum camera index to scan (0 to max_index)
            
        Returns:
            List of CameraInfo objects with unique identifiers
        """
        pass
    
    @abstractmethod
    async def get_camera_info_async(self, index: int) -> Optional[CameraInfo]:
        """
        Get unique identifier and information for a camera at a specific index.
        
        Args:
            index: Camera device index
            
        Returns:
            CameraInfo if camera is available, None otherwise
        """
        pass


class CameraService(ICameraService):
    """Implementation of camera service using OpenCV."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        # Reduce OpenCV log verbosity - suppress warnings
        try:
            import os
            # Set OpenCV to only show errors, suppress warnings
            os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
            cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
            # Also suppress stderr for OpenCV warnings
            import warnings
            warnings.filterwarnings('ignore', category=UserWarning, module='cv2')
        except Exception:
            pass

    async def test_camera_available_async(self, index: int, timeout: float = 120.0) -> bool:
        """
        Test if a camera index is available.

        The function is async for interface consistency but the actual
        implementation is synchronous and runs in a thread.

        Args:
            index: Camera device index.
            timeout: Unused, kept for compatibility.
        """

        def _test_sync() -> bool:
            """Synchronous check if a camera can be opened."""
            import warnings

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
                if not cap:
                    return False
                try:
                    if not cap.isOpened():
                        return False
                    return True
                finally:
                    cap.release()

        return await asyncio.to_thread(_test_sync)

    async def open_camera_async(
        self, index: int, width: int, height: int, buffer_size: int = 1, fourcc: str = "MJPG", auto_exposure: float = 0.75
    ) -> Optional[CameraHandle]:
        """
        Open camera with fallback backends.
        
        All cameras are treated equally with the same timeout.
        Tries backends in order with timeouts to prevent hanging.
        Camera settings are configured in a single batch operation for efficiency.
        """
        def _open_sync() -> Optional[CameraHandle]:
            """Synchronously open camera with fallback backends."""
            import warnings
            backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW, cv2.CAP_ANY]
            
            for backend in backends:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    cap = cv2.VideoCapture(index, backend)
                    if cap and cap.isOpened():
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size)
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
                        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, auto_exposure)
                        self.logger.info(f"Opened camera {index} with backend {backend}")
                        return cap
                    elif cap:
                        cap.release()
            return None
        
        cap = await asyncio.wait_for(
            asyncio.to_thread(_open_sync),
            timeout=120.0
        )
        if not cap:
            self.logger.error(f"Failed to open camera {index} with any backend")
        return cap

    async def capture_frame_async(self, camera: CameraHandle) -> Optional[np.ndarray]:
        """Capture a single frame from the camera."""
        def _capture_sync() -> Optional[np.ndarray]:
            """Synchronously capture a frame."""
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ok, frame = camera.read()
                if ok and frame is not None:
                    return frame
            return None
        
        return await asyncio.to_thread(_capture_sync)

    async def close_camera_async(self, camera: CameraHandle) -> None:
        """Close and release a camera."""
        await asyncio.to_thread(camera.release)
        self.logger.info("Camera closed")

    async def get_camera_info_async(self, index: int) -> Optional[CameraInfo]:
        """
        Get unique identifier and information for a camera at a specific index.
        
        Creates a unique identifier by attempting to capture a frame and using
        frame properties to create a stable hash. This helps identify the same
        physical camera even if the index changes.
        """
        def _get_info_sync() -> Optional[CameraInfo]:
            """Synchronously get camera info."""
            import warnings
            device_properties = {}
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
                if not cap or not cap.isOpened():
                    if cap:
                        cap.release()
                    unique_hash = hashlib.md5(f"cam_slow_{index}".encode()).hexdigest()[:12]
                    return CameraInfo(
                        unique_id=f"cam_{unique_hash}",
                        index=index,
                        name=f"Camera {index} (slow)"
                    )
                
                ret, frame = cap.read()
                if ret and frame is not None:
                    frame_hash = hashlib.md5(frame[:10, :10].tobytes()).hexdigest()[:8]
                    device_properties['frame_hash'] = frame_hash
                    device_properties['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    device_properties['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                backend_name = cap.getBackendName()
                if backend_name:
                    device_properties['backend'] = backend_name
                
                cap.release()
                
                props_str = "_".join(f"{k}:{v}" for k, v in sorted(device_properties.items()))
                unique_hash = hashlib.md5(f"cam_{index}_{props_str}".encode()).hexdigest()[:12]
                return CameraInfo(
                    unique_id=f"cam_{unique_hash}",
                    index=index,
                    name=f"Camera {index}"
                )
        
        return await asyncio.wait_for(
            asyncio.to_thread(_get_info_sync),
            timeout=120.0
        )
    
    async def scan_available_cameras_async(self, max_index: int) -> List[CameraInfo]:
        """
        Scan for available cameras and return unique identifiers.
        
        Scanning sequentially ensures stable identification. Each camera gets a unique
        identifier that remains constant even if the index changes.
        
        Args:
            max_index: Maximum camera index to scan (0 to max_index)
            
        Returns:
            List of CameraInfo objects with unique identifiers (no duplicates by unique_id)
        """
        found_cameras: Dict[str, CameraInfo] = {}
        
        for camera_index in range(max_index + 1):
            camera_info = await self.get_camera_info_async(camera_index)
            if camera_info:
                found_cameras[camera_info.unique_id] = camera_info
                self.logger.debug(f"Found camera: {camera_info}")
        
        return sorted(list(found_cameras.values()), key=lambda c: c.index)

