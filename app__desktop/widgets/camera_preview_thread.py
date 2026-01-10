# app__desktop/widgets/camera_preview_thread.py
"""Thread for updating camera preview frames."""
from typing import Optional

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal


class CameraPreviewThread(QThread):
    """Thread for continuously capturing frames from a camera."""
    
    frame_ready = pyqtSignal(str, np.ndarray)  # camera_unique_id, frame
    
    def __init__(self, camera_unique_id: str, camera_handle: cv2.VideoCapture, parent=None):
        """
        Initialize camera preview thread.
        
        Args:
            camera_unique_id: Unique ID of the camera
            camera_handle: OpenCV VideoCapture handle
            parent: Parent QObject (optional)
        """
        super().__init__(parent)
        self.camera_unique_id = camera_unique_id
        self.camera_handle = camera_handle
        self.running = False
    
    def run(self):
        """Run the preview loop continuously."""
        self.running = True
        while self.running:
            if self.camera_handle is None:
                break
            
            ret, frame = self.camera_handle.read()
            if ret and frame is not None:
                self.frame_ready.emit(self.camera_unique_id, frame)
            
            self.msleep(33)  # ~30 FPS
    
    def stop(self):
        """Stop the preview thread."""
        self.running = False
        self.wait()

