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
        Test if camera index is available.
        
        All cameras are treated equally with the same timeout.
        Uses CAP_MSMF backend (Windows Media Foundation) for reliable testing.
        
        Args:
            index: Camera device index
            timeout: Maximum time to wait for camera test (default: 120 seconds / 2 minutes)
        """
        async def test_with_backend(backend) -> bool:
            """Test camera with a specific backend."""
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    cap = await asyncio.wait_for(
                        asyncio.to_thread(cv2.VideoCapture, index, backend),
                        timeout=timeout
                    )
                    if cap and cap.isOpened():
                        await asyncio.wait_for(
                            asyncio.to_thread(cap.release),
                            timeout=120.0
                        )
                        return True
                    elif cap:
                        await asyncio.wait_for(
                            asyncio.to_thread(cap.release),
                            timeout=120.0
                        )
            except (asyncio.TimeoutError, asyncio.CancelledError):
                raise
            except Exception:
                pass
            return False

        msmf_timed_out = False
        try:
            # Try MSMF first (faster on Windows)
            if await test_with_backend(cv2.CAP_MSMF):
                self.logger.debug(f"Camera {index} is available (MSMF)")
                return True
        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError:
            msmf_timed_out = True
            self.logger.debug(f"Camera {index} test timed out with MSMF, trying fallback")
        except Exception as e:
            self.logger.debug(f"Camera {index} test failed with MSMF: {e}")
        
        # Try CAP_ANY as fallback (for non-Windows systems)
        cap_any_timed_out = False
        try:
            if await test_with_backend(cv2.CAP_ANY):
                self.logger.debug(f"Camera {index} is available (CAP_ANY)")
                return True
        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError:
            cap_any_timed_out = True
            self.logger.debug(f"Camera {index} test timed out with CAP_ANY as well")
        except Exception:
            pass
        
        # If both backends timed out, raise TimeoutError so the camera can still be included
        if msmf_timed_out and cap_any_timed_out:
            raise asyncio.TimeoutError(f"Camera {index} timed out with all backends, but may still be available")
        
        return False

    async def open_camera_async(
        self, index: int, width: int, height: int, buffer_size: int = 1, fourcc: str = "MJPG", auto_exposure: float = 0.75
    ) -> Optional[CameraHandle]:
        """
        Open camera with fallback backends.
        
        All cameras are treated equally with the same timeout.
        Tries backends in order with timeouts to prevent hanging.
        Camera settings are configured in a single batch operation for efficiency.
        """
        backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW, cv2.CAP_ANY]
        
        async def try_open_with_backend(backend) -> Optional[CameraHandle]:
            """Try to open camera with a specific backend."""
            try:
                # Try to open camera with timeout - increased significantly for slow cameras
                cap = await asyncio.wait_for(
                    asyncio.to_thread(cv2.VideoCapture, index, backend),
                    timeout=120.0  # 120 second timeout per backend (2 minutes)
                )
                if cap and cap.isOpened():
                    # Configure all camera settings in one batch (more efficient)
                    def configure_camera(cap_obj):
                        """Configure camera settings synchronously."""
                        import warnings
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            cap_obj.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size)
                            cap_obj.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                            cap_obj.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                            cap_obj.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
                            cap_obj.set(cv2.CAP_PROP_AUTO_EXPOSURE, auto_exposure)
                    
                    # Configure settings in one go
                    await asyncio.wait_for(
                        asyncio.to_thread(configure_camera, cap),
                        timeout=120.0
                    )
                    self.logger.info(f"Opened camera {index} with backend {backend}")
                    return cap
                else:
                    if cap:
                        await asyncio.wait_for(
                            asyncio.to_thread(cap.release),
                            timeout=120.0
                        )
            except asyncio.TimeoutError:
                self.logger.debug(f"Timeout opening camera {index} with backend {backend}")
            except Exception as e:
                self.logger.debug(f"Failed to open camera {index} with backend {backend}: {e}")
            return None
        
        # Try backends sequentially (parallel might cause resource conflicts)
        for backend in backends:
            result = await try_open_with_backend(backend)
            if result:
                return result
        
        self.logger.error(f"Failed to open camera {index} with any backend")
        return None

    async def capture_frame_async(self, camera: CameraHandle) -> Optional[np.ndarray]:
        """Capture a single frame from the camera."""
        try:
            # Run read in thread pool since it's blocking
            # Suppress OpenCV warnings during frame capture
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ok, frame = await asyncio.to_thread(camera.read)
                if ok and frame is not None:
                    return frame
            return None
        except Exception as e:
            # Only log if it's not a common OpenCV warning
            if "can't grab frame" not in str(e).lower():
                self.logger.debug(f"Error capturing frame: {e}")
            return None

    async def close_camera_async(self, camera: CameraHandle) -> None:
        """Close and release a camera."""
        try:
            await asyncio.to_thread(camera.release)
            self.logger.info("Camera closed")
        except Exception as e:
            self.logger.error(f"Error closing camera: {e}")

    async def get_camera_info_async(self, index: int) -> Optional[CameraInfo]:
        """
        Get unique identifier and information for a camera at a specific index.
        
        Creates a unique identifier by attempting to capture a frame and using
        frame properties to create a stable hash. This helps identify the same
        physical camera even if the index changes.
        """
        try:
            # Try to open camera briefly to get device information
            cap = None
            device_properties = {}
            
            try:
                cap = await asyncio.wait_for(
                    asyncio.to_thread(cv2.VideoCapture, index, cv2.CAP_MSMF),
                    timeout=120.0
                )
                if cap and cap.isOpened():
                    try:
                        # Try to capture a frame to get camera-specific properties
                        # This helps create a more unique identifier
                        ret, frame = await asyncio.wait_for(
                            asyncio.to_thread(cap.read),
                            timeout=120.0
                        )
                        if ret and frame is not None:
                            # Use frame dimensions and a hash of the first few pixels
                            # to create a unique identifier (not perfect, but better than just index)
                            frame_hash = hashlib.md5(frame[:10, :10].tobytes()).hexdigest()[:8]
                            device_properties['frame_hash'] = frame_hash
                            device_properties['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            device_properties['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    except Exception:
                        # If we can't capture a frame, that's okay - we'll use other properties
                        pass
                    
                    try:
                        backend_name = cap.getBackendName()
                        device_properties['backend'] = backend_name
                    except Exception:
                        pass
                    
                    await asyncio.wait_for(
                        asyncio.to_thread(cap.release),
                        timeout=120.0
                    )
                    
                    # Create unique identifier combining index and device properties
                    # This should be more stable than just using the index
                    props_str = "_".join(f"{k}:{v}" for k, v in sorted(device_properties.items()))
                    unique_hash = hashlib.md5(f"cam_{index}_{props_str}".encode()).hexdigest()[:12]
                    unique_id = f"cam_{unique_hash}"
                    
                    return CameraInfo(
                        unique_id=unique_id,
                        index=index,
                        name=f"Camera {index}"
                    )
            except asyncio.TimeoutError:
                # Camera exists but is slow - create a basic unique ID
                # Use a hash that includes the index to make it somewhat unique
                unique_hash = hashlib.md5(f"cam_slow_{index}".encode()).hexdigest()[:12]
                unique_id = f"cam_{unique_hash}"
                return CameraInfo(
                    unique_id=unique_id,
                    index=index,
                    name=f"Camera {index} (slow)"
                )
            except Exception as e:
                self.logger.debug(f"Error getting info for camera {index}: {e}")
                # Still create a basic unique ID even if we can't open the camera
                unique_hash = hashlib.md5(f"cam_error_{index}".encode()).hexdigest()[:12]
                unique_id = f"cam_{unique_hash}"
                return CameraInfo(
                    unique_id=unique_id,
                    index=index,
                    name=f"Camera {index}"
                )
        except Exception as e:
            self.logger.debug(f"Exception getting camera info for {index}: {e}")
            return None
    
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
        # Scan cameras sequentially and get unique identifiers
        found_cameras: Dict[str, CameraInfo] = {}  # Use dict to deduplicate by unique_id
        
        for camera_index in range(max_index + 1):
            try:
                # Test if camera is available
                result = await self._test_camera_with_error_handling(camera_index)
                if result is True:
                    # Get camera info with unique identifier
                    camera_info = await self.get_camera_info_async(camera_index)
                    if camera_info:
                        # Use unique_id as key to prevent duplicates
                        found_cameras[camera_info.unique_id] = camera_info
                        self.logger.debug(f"Found camera: {camera_info}")
            except asyncio.CancelledError:
                raise
            except asyncio.TimeoutError:
                # Include cameras that timeout - create basic info
                camera_info = await self.get_camera_info_async(camera_index)
                if camera_info:
                    found_cameras[camera_info.unique_id] = camera_info
                self.logger.debug(f"Camera {camera_index} test timed out, but including it")
            except Exception as e:
                # For other exceptions, try to get info anyway
                camera_info = await self.get_camera_info_async(camera_index)
                if camera_info:
                    found_cameras[camera_info.unique_id] = camera_info
                self.logger.debug(f"Camera {camera_index} test had exception: {e}, but including it")
        
        # Return list sorted by index for consistent ordering
        return sorted(list(found_cameras.values()), key=lambda c: c.index)
    
    async def _test_camera_with_error_handling(self, index: int) -> bool:
        """
        Test a single camera with error handling.
        
        All cameras are treated equally with the same timeout.
        Returns True if camera is available, or raises TimeoutError if it times out.
        TimeoutError is caught in scan_available_cameras_async to include the camera anyway.
        """
        try:
            # All cameras use the same timeout - no distinction between fast/slow
            return await self.test_camera_available_async(index, timeout=120.0)
        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError:
            # Re-raise timeout so scan method can include the camera
            raise
        except Exception as e:
            # For other exceptions, also raise so camera can be included
            raise TimeoutError(f"Camera {index} test exception: {e}") from e

