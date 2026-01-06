# infrastructure_layer/services/camera_preview__service.py
"""Service for managing camera preview streams."""
import asyncio
import base64
from typing import Dict, Optional, Set
from abc import ABC, abstractmethod

import cv2
import numpy as np

from common.logger import get_logger
from infrastructure_layer.services.camera__service import ICameraService, CameraHandle

logger = get_logger(__name__)


class ICameraPreviewService(ABC):
    """Interface for camera preview stream management."""

    @abstractmethod
    async def start_preview_async(self, camera_index: int, width: int = 640, height: int = 480) -> bool:
        """Start preview stream for a camera."""
        pass

    @abstractmethod
    async def stop_preview_async(self, camera_index: int) -> None:
        """Stop preview stream for a camera."""
        pass

    @abstractmethod
    async def get_frame_async(self, camera_index: int) -> Optional[bytes]:
        """Get current frame as JPEG bytes for a camera."""
        pass

    @abstractmethod
    def is_preview_active(self, camera_index: int) -> bool:
        """Check if preview is active for a camera."""
        pass

    @abstractmethod
    def get_active_cameras(self) -> Set[int]:
        """Get set of camera indices with active previews."""
        pass


class CameraPreviewService(ICameraPreviewService):
    """Implementation of camera preview service."""

    def __init__(self, camera_service: ICameraService) -> None:
        """
        Initialize camera preview service.
        
        Args:
            camera_service: Camera service for opening/closing cameras
        """
        self.camera_service: ICameraService = camera_service
        self.logger = get_logger(__name__)
        
        # Track active camera streams: camera_index -> CameraHandle
        self._active_cameras: Dict[int, CameraHandle] = {}
        
        # Track frame capture tasks: camera_index -> asyncio.Task
        self._capture_tasks: Dict[int, asyncio.Task] = {}
        
        # Store latest frames: camera_index -> np.ndarray
        self._latest_frames: Dict[int, np.ndarray] = {}

    async def start_preview_async(self, camera_index: int, width: int = 640, height: int = 480) -> bool:
        """Start preview stream for a camera."""
        if camera_index in self._active_cameras:
            self.logger.warning(f"Camera {camera_index} preview already active")
            return True

        try:
            # Open camera with timeout to prevent hanging
            # All cameras use the same timeout
            camera = await asyncio.wait_for(
                self.camera_service.open_camera_async(
                    index=camera_index,
                    width=width,
                    height=height,
                    buffer_size=1,  # Low latency for preview
                    fourcc="MJPG",
                    auto_exposure=0.75,
                ),
                timeout=120.0  # 120 second timeout for opening camera
            )
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout opening camera {camera_index}")
            return False
        except Exception as e:
            self.logger.error(f"Error opening camera {camera_index}: {e}")
            return False

        if not camera:
            self.logger.error(f"Failed to open camera {camera_index}")
            return False

        self._active_cameras[camera_index] = camera
        
        # Start frame capture task
        task = asyncio.create_task(self._capture_loop_async(camera_index, camera))
        self._capture_tasks[camera_index] = task
        
        self.logger.info(f"Started preview for camera {camera_index}")
        return True

    async def stop_preview_async(self, camera_index: int) -> None:
        """Stop preview stream for a camera."""
        if camera_index not in self._active_cameras:
            return

        # Cancel capture task
        if camera_index in self._capture_tasks:
            task = self._capture_tasks[camera_index]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._capture_tasks[camera_index]

        # Close camera
        camera = self._active_cameras[camera_index]
        await self.camera_service.close_camera_async(camera)
        del self._active_cameras[camera_index]

        # Remove latest frame
        if camera_index in self._latest_frames:
            del self._latest_frames[camera_index]

        self.logger.info(f"Stopped preview for camera {camera_index}")

    async def _capture_loop_async(self, camera_index: int, camera: CameraHandle) -> None:
        """Continuously capture frames from camera."""
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        try:
            while True:
                try:
                    frame = await self.camera_service.capture_frame_async(camera)
                    if frame is not None:
                        self._latest_frames[camera_index] = frame
                        consecutive_errors = 0  # Reset error counter on success
                    else:
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            self.logger.warning(
                                f"Camera {camera_index} failed to capture {consecutive_errors} consecutive frames, stopping preview"
                            )
                            break
                    await asyncio.sleep(0.033)  # ~30 FPS
                except Exception as e:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        self.logger.error(
                            f"Camera {camera_index} capture error: {e}, stopping preview after {consecutive_errors} errors"
                        )
                        break
                    await asyncio.sleep(0.033)  # Continue trying
        except asyncio.CancelledError:
            self.logger.info(f"Capture loop cancelled for camera {camera_index}")
        except Exception as e:
            self.logger.error(f"Error in capture loop for camera {camera_index}: {e}")
        finally:
            # Clean up if loop exits due to errors
            if consecutive_errors >= max_consecutive_errors:
                # Remove from active cameras
                if camera_index in self._active_cameras:
                    del self._active_cameras[camera_index]
                if camera_index in self._capture_tasks:
                    del self._capture_tasks[camera_index]
                if camera_index in self._latest_frames:
                    del self._latest_frames[camera_index]
                # Close camera
                try:
                    await self.camera_service.close_camera_async(camera)
                except Exception:
                    pass

    async def get_frame_async(self, camera_index: int) -> Optional[bytes]:
        """Get current frame as JPEG bytes for a camera."""
        if camera_index not in self._latest_frames:
            return None

        frame = self._latest_frames[camera_index]
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Encode as JPEG
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
        success, buffer = cv2.imencode('.jpg', frame_rgb, encode_param)
        
        if success:
            return buffer.tobytes()
        return None

    def is_preview_active(self, camera_index: int) -> bool:
        """Check if preview is active for a camera."""
        return camera_index in self._active_cameras

    def get_active_cameras(self) -> Set[int]:
        """Get set of camera indices with active previews."""
        return set(self._active_cameras.keys())

