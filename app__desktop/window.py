# app__desktop/window.py
"""Main window for desktop camera preview application."""
import asyncio
from typing import Dict, List

from PyQt6.QtCore import QSize, QTimer
from PyQt6.QtWidgets import (
    QGridLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from common.camera_info import CameraInfo
from common.logger import get_logger
from infrastructure_layer.services.camera__service import ICameraService
from app__desktop.app_config import DesktopAppConfig
from app__desktop.services.camera_capture_service import CameraCaptureService
from app__desktop.widgets.camera_preview_widget import CameraPreviewWidget


class MainWindow(QMainWindow):
    """Main window for the desktop camera preview application."""
    
    def __init__(
        self,
        camera_service: ICameraService,
        camera_capture_service: CameraCaptureService,
        app_config: DesktopAppConfig,
    ):
        """
        Initialize main window.
        
        Args:
            camera_service: Camera service instance
            camera_capture_service: Camera capture service instance
            app_config: Application configuration
        """
        super().__init__()
        self.camera_service = camera_service
        self.camera_capture_service = camera_capture_service
        self.app_config = app_config
        self.available_cameras: List[CameraInfo] = []
        self.preview_widgets: Dict[str, CameraPreviewWidget] = {}
        self.logger = get_logger(__name__)
        
        # Configure window from config
        window_config = app_config.ui.window
        self.setWindowTitle(window_config.title)
        self.setMinimumSize(QSize(window_config.min_width, window_config.min_height))
        
        self._setup_ui()
        
        # Auto-scan cameras on startup
        QTimer.singleShot(500, self.scan_cameras)
    
    def _setup_ui(self):
        """Set up the user interface."""
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
    
    def scan_cameras(self):
        """Scan for available cameras."""
        self.logger.info("Scanning for cameras...")
        
        async def _scan():
            max_index = self.app_config.camera.max_scan_index
            cameras = await self.camera_service.scan_available_cameras_async(max_index=max_index)
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
        
        # Create grid using configured number of columns
        cols = self.app_config.ui.grid.columns
        for idx, camera_info in enumerate(self.available_cameras):
            row = idx // cols
            col = idx % cols
            
            widget = CameraPreviewWidget(camera_info, self.app_config, self)
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
        
        async def _capture_all():
            return await self.camera_capture_service.capture_all_cameras_async(
                cameras=self.available_cameras,
                preview_widgets=self.preview_widgets,
            )
        
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
