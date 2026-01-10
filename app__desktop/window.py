# app__desktop/window.py
"""Main window for desktop camera preview application."""
import asyncio
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np
from PyQt6.QtCore import QSize, Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from common.camera_info import CameraInfo
from infrastructure_layer.services.camera__service import CameraService, ICameraService
from infrastructure_layer.file_writers.image_file__writer import ImageFileWriter, IImageFileWriter
from common.logger import get_logger


class CameraPreviewThread(QThread):
    """Thread for updating camera preview frames."""
    
    frame_ready = pyqtSignal(int, np.ndarray)  # camera_index, frame
    
    def __init__(self, camera_index: int, camera_handle, parent=None):
        super().__init__(parent)
        self.camera_index = camera_index
        self.camera_handle = camera_handle
        self.running = False
    
    def run(self):
        """Run the preview loop."""
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


class CameraPreviewWidget(QLabel):
    """Widget for displaying a single camera preview."""
    
    def __init__(self, camera_info: CameraInfo, parent=None):
        super().__init__(parent)
        self.camera_info = camera_info
        self.camera_handle: Optional[cv2.VideoCapture] = None
        self.preview_thread: Optional[CameraPreviewThread] = None
        
        # Set up label for displaying frames
        self.setMinimumSize(640, 480)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(f"{camera_info.unique_id}\nNot started")
        self.setStyleSheet("border: 1px solid gray; background-color: black; color: white;")
    
    def start_preview(self, camera_service: ICameraService) -> bool:
        """Start camera preview."""
        if self.camera_handle is not None:
            return True
        
        async def _open_camera():
            handle = await camera_service.open_camera_async(
                index=self.camera_info.index,
                width=640,
                height=480,
                buffer_size=1,
                fourcc="MJPG",
                auto_exposure=0.75
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
            logger = get_logger(__name__)
            logger.error(f"Failed to start preview for {self.camera_info.unique_id}: {e}")
            return False
        finally:
            loop.close()
    
    def stop_preview(self, camera_service: ICameraService):
        """Stop camera preview."""
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
        """Update the displayed frame."""
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
        """Capture current frame from camera."""
        if self.camera_handle is None:
            return None
        
        ret, frame = self.camera_handle.read()
        if ret and frame is not None:
            return frame
        return None


class MainWindow(QMainWindow):
    """Main window for the desktop camera preview application."""
    
    def __init__(self):
        super().__init__()
        self.camera_service: ICameraService = CameraService()
        self.image_writer: IImageFileWriter = ImageFileWriter()
        self.available_cameras: List[CameraInfo] = []
        self.preview_widgets: Dict[str, CameraPreviewWidget] = {}
        self.logger = get_logger(__name__)
        
        self.setWindowTitle("Walnut Camera Preview")
        self.setMinimumSize(QSize(1280, 720))
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create button bar
        button_layout = QVBoxLayout()
        
        # Buttons
        scan_button = QPushButton("Scan Cameras")
        scan_button.clicked.connect(self.scan_cameras)
        
        start_all_button = QPushButton("Start All Previews")
        start_all_button.clicked.connect(self.start_all_previews)
        
        stop_all_button = QPushButton("Stop All Previews")
        stop_all_button.clicked.connect(self.stop_all_previews)
        
        capture_all_button = QPushButton("Capture All Cameras")
        capture_all_button.clicked.connect(self.capture_all_cameras)
        
        button_layout.addWidget(scan_button)
        button_layout.addWidget(start_all_button)
        button_layout.addWidget(stop_all_button)
        button_layout.addWidget(capture_all_button)
        
        # Create grid layout for camera previews
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        
        main_layout.addLayout(button_layout)
        main_layout.addLayout(self.grid_layout)
        
        # Auto-scan cameras on startup
        QTimer.singleShot(500, self.scan_cameras)
    
    def scan_cameras(self):
        """Scan for available cameras."""
        self.logger.info("Scanning for cameras...")
        
        async def _scan():
            cameras = await self.camera_service.scan_available_cameras_async(max_index=15)
            return cameras
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            self.available_cameras = loop.run_until_complete(_scan())
            self.logger.info(f"Found {len(self.available_cameras)} cameras")
            self.update_preview_grid()
            
            if len(self.available_cameras) == 0:
                QMessageBox.warning(self, "No Cameras", "No cameras found. Please check your connections.")
        except Exception as e:
            self.logger.error(f"Error scanning cameras: {e}")
            QMessageBox.critical(self, "Error", f"Failed to scan cameras: {e}")
        finally:
            loop.close()
    
    def update_preview_grid(self):
        """Update the preview grid with available cameras."""
        # Clear existing widgets
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        self.preview_widgets.clear()
        
        # Create grid (2 columns)
        cols = 2
        for idx, camera_info in enumerate(self.available_cameras):
            row = idx // cols
            col = idx % cols
            
            widget = CameraPreviewWidget(camera_info, self)
            self.preview_widgets[camera_info.unique_id] = widget
            self.grid_layout.addWidget(widget, row, col)
    
    def start_all_previews(self):
        """Start preview for all cameras."""
        if not self.available_cameras:
            QMessageBox.warning(self, "No Cameras", "Please scan for cameras first.")
            return
        
        self.logger.info("Starting all camera previews...")
        for camera_info in self.available_cameras:
            widget = self.preview_widgets.get(camera_info.unique_id)
            if widget:
                success = widget.start_preview(self.camera_service)
                if not success:
                    self.logger.warning(f"Failed to start preview for {camera_info.unique_id}")
    
    def stop_all_previews(self):
        """Stop preview for all cameras."""
        self.logger.info("Stopping all camera previews...")
        for widget in self.preview_widgets.values():
            widget.stop_preview(self.camera_service)
    
    def capture_all_cameras(self):
        """Capture images from all cameras."""
        if not self.available_cameras:
            QMessageBox.warning(self, "No Cameras", "Please scan for cameras first.")
            return
        
        self.logger.info("Capturing from all cameras...")
        
        # Create _test folder
        workspace_root = Path(__file__).parent.parent
        test_folder = workspace_root / "_test"
        test_folder.mkdir(parents=True, exist_ok=True)
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        async def _capture_all():
            captured_count = 0
            errors = []
            
            for camera_info in self.available_cameras:
                widget = self.preview_widgets.get(camera_info.unique_id)
                if widget is None:
                    continue
                
                # If camera is already open in preview, capture from it
                frame = None
                if widget.camera_handle is not None:
                    frame = widget.capture_frame()
                else:
                    # Otherwise, open camera temporarily
                    handle = await self.camera_service.open_camera_async(
                        index=camera_info.index,
                        width=640,
                        height=480,
                        buffer_size=1,
                        fourcc="MJPG",
                        auto_exposure=0.75
                    )
                    if handle:
                        frame = await self.camera_service.capture_frame_async(handle)
                        await self.camera_service.close_camera_async(handle)
                
                if frame is not None:
                    # Save image
                    filename = f"{camera_info.unique_id}_{timestamp}.jpg"
                    file_path = test_folder / filename
                    
                    success = await self.image_writer.save_image_async(frame, str(file_path))
                    if success:
                        captured_count += 1
                        self.logger.info(f"Captured {camera_info.unique_id} to {file_path}")
                    else:
                        errors.append(f"Failed to save {camera_info.unique_id}")
                else:
                    errors.append(f"Failed to capture {camera_info.unique_id}")
            
            return captured_count, len(self.available_cameras), errors
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            captured_count, total_cameras, errors = loop.run_until_complete(_capture_all())
            
            message = f"Captured {captured_count} of {total_cameras} cameras."
            if errors:
                message += f"\nErrors: {', '.join(errors)}"
            
            if captured_count > 0:
                QMessageBox.information(self, "Capture Complete", message)
            else:
                QMessageBox.warning(self, "Capture Failed", message)
        except Exception as e:
            self.logger.error(f"Error capturing cameras: {e}")
            QMessageBox.critical(self, "Error", f"Failed to capture cameras: {e}")
        finally:
            loop.close()
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.stop_all_previews()
        event.accept()

