# app__desktop/widgets/camera_preview_thread.py
"""Thread for updating camera preview frames."""
from typing import Optional

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal


class CameraPreviewThread(QThread):
    """Thread for continuously capturing frames from a camera."""
    
    frame_ready = pyqtSignal(int, np.ndarray)  # camera_index, frame
    
    def __init__(self, camera_index: int, camera_handle: cv2.VideoCapture, parent=None):
        """
        Initialize camera preview thread.
        
        Args:
            camera_index: Index of the camera
            camera_handle: OpenCV VideoCapture handle
            parent: Parent QObject (optional)
        """
        super().__init__(parent)
        self.camera_index = camera_index
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
                self.frame_ready.emit(self.camera_index, frame)
            
            self.msleep(33)  # ~30 FPS
    
    def stop(self):
        """Stop the preview thread."""
        self.running = False
        self.wait()

