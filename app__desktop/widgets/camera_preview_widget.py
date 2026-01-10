# app__desktop/widgets/camera_preview_widget.py
"""Widget for displaying a single camera preview."""
import asyncio
from typing import Optional

import cv2
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel

from common.camera_info import CameraInfo
from common.logger import get_logger
from infrastructure_layer.services.camera__service import ICameraService
from app__desktop.app_config import DesktopAppConfig
from app__desktop.widgets.camera_preview_thread import CameraPreviewThread


class CameraPreviewWidget(QLabel):
    """Widget for displaying a single camera preview."""
    
    def __init__(self, camera_info: CameraInfo, app_config: DesktopAppConfig, parent=None):
        """
        Initialize camera preview widget.
        
        Args:
            camera_info: Camera information
            app_config: Application configuration
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.camera_info = camera_info
        self.app_config = app_config
        self.camera_handle: Optional[cv2.VideoCapture] = None
        self.preview_thread: Optional[CameraPreviewThread] = None
        self.logger = get_logger(__name__)
        
        # Set up label for displaying frames
        preview_config = app_config.camera.preview
        self.setMinimumSize(preview_config.width, preview_config.height)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(f"{camera_info.unique_id}\nNot started")
        self.setStyleSheet("border: 1px solid gray; background-color: black; color: white;")
    
    def start_preview(self, camera_service: ICameraService) -> bool:
        """
        Start camera preview.
        
        Args:
            camera_service: Camera service instance
            
        Returns:
            True if preview started successfully, False otherwise
        """
        if self.camera_handle is not None:
            return True
        
        preview_config = self.app_config.camera.preview
        
        async def _open_camera():
            handle = await camera_service.open_camera_async(
                index=self.camera_info.index,
                width=preview_config.width,
                height=preview_config.height,
                buffer_size=preview_config.buffer_size,
                fourcc=preview_config.fourcc,
                auto_exposure=preview_config.auto_exposure
            )
            return handle
        
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            handle = loop.run_until_complete(_open_camera())
            if handle is None:
                return False
            
            self.camera_handle = handle
            self.preview_thread = CameraPreviewThread(self.camera_info.index, handle, self)
            self.preview_thread.frame_ready.connect(self.update_frame)
            self.preview_thread.start()
            return True
        except Exception as e:
            self.logger.error(f"Failed to start preview for {self.camera_info.unique_id}: {e}")
            return False
        finally:
            loop.close()
    
    def stop_preview(self, camera_service: ICameraService):
        """
        Stop camera preview.
        
        Args:
            camera_service: Camera service instance
        """
        if self.preview_thread is not None:
            self.preview_thread.stop()
            self.preview_thread = None
        
        if self.camera_handle is not None:
            async def _close_camera():
                await camera_service.close_camera_async(self.camera_handle)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_close_camera())
            finally:
                loop.close()
                self.camera_handle = None
        
        self.setText(f"{self.camera_info.unique_id}\nStopped")
    
    def update_frame(self, camera_index: int, frame: np.ndarray):
        """
        Update the displayed frame.
        
        Args:
            camera_index: Index of the camera that captured the frame
            frame: Frame data as numpy array (BGR format)
        """
        if camera_index != self.camera_info.index:
            return
        
        # Convert BGR to RGB and ensure contiguous array
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = np.ascontiguousarray(frame_rgb)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        
        # Convert to QImage (copy data to avoid memory issues)
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
        
        # Scale to fit label while maintaining aspect ratio
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.setPixmap(scaled_pixmap)
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture current frame from camera.
        
        Returns:
            Frame as numpy array if successful, None otherwise
        """
        if self.camera_handle is None:
            return None
        
        ret, frame = self.camera_handle.read()
        if ret and frame is not None:
            return frame
        return None

