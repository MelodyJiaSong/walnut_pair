# app__desktop/window.py
"""Main window for desktop camera preview application."""
import asyncio
from typing import Dict, List

from PyQt6.QtCore import QSize, QTimer
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from common.camera_info import CameraInfo
from common.enums import WalnutSideEnum
from common.logger import get_logger
from infrastructure_layer.services.camera__service import ICameraService
from app__desktop.app_config import DesktopAppConfig
from app__desktop.services.camera_capture_service import CameraCaptureService
from app__desktop.services.camera_side_mapping__service import CameraSideMappingService
from app__desktop.widgets.camera_preview_widget import CameraPreviewWidget
from app__desktop.widgets.camera_side_mapping__dialog import CameraSideMappingDialog


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
        
        # Camera-side mapping service
        self.mapping_service = CameraSideMappingService()
        self.camera_side_mapping: Dict[WalnutSideEnum, str] = {}
        self.output_folder: str = ""
        
        # Walnut ID fields
        self.walnut_id_free_text: str = ""
        self.walnut_id_number: int = 1
        
        # Configure window from config
        window_config = app_config.ui.window
        self.setWindowTitle(window_config.title)
        self.setMinimumSize(QSize(window_config.min_width, window_config.min_height))
        
        self._setup_ui()
        
        # Load camera-side mapping and output folder on startup
        self.camera_side_mapping, self.output_folder = self.mapping_service.load_settings()
        # If no output folder is configured, use default from config
        if not self.output_folder:
            self.output_folder = self.app_config.camera.capture.output_folder
        
        # Auto-scan cameras on startup
        QTimer.singleShot(500, self.scan_cameras)
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Walnut ID input section
        walnut_id_layout = QHBoxLayout()
        walnut_id_label = QLabel("Walnut ID:")
        self.walnut_id_free_text_input = QLineEdit()
        self.walnut_id_free_text_input.setPlaceholderText("Free text (e.g., type)")
        self.walnut_id_free_text_input.textChanged.connect(self._on_walnut_id_free_text_changed)
        
        self.walnut_id_number_input = QLineEdit()
        self.walnut_id_number_input.setPlaceholderText("Number")
        self.walnut_id_number_input.setText("1")
        self.walnut_id_number_input.textChanged.connect(self._on_walnut_id_number_changed)
        
        walnut_id_separator = QLabel("__")
        walnut_id_layout.addWidget(walnut_id_label)
        walnut_id_layout.addWidget(self.walnut_id_free_text_input)
        walnut_id_layout.addWidget(walnut_id_separator)
        walnut_id_layout.addWidget(self.walnut_id_number_input)
        walnut_id_layout.addStretch()
        
        main_layout.addLayout(walnut_id_layout)
        
        # Button bar
        button_layout = QHBoxLayout()
        
        scan_button = QPushButton("Scan Cameras")
        scan_button.clicked.connect(self.scan_cameras)
        
        config_mapping_button = QPushButton("Configure Camera Mapping")
        config_mapping_button.clicked.connect(self.configure_camera_mapping)
        
        start_all_button = QPushButton("Start All Previews")
        start_all_button.clicked.connect(self.start_all_previews)
        
        stop_all_button = QPushButton("Stop All Previews")
        stop_all_button.clicked.connect(self.stop_all_previews)
        
        capture_all_button = QPushButton("Capture All Cameras")
        capture_all_button.clicked.connect(self.capture_all_cameras)
        
        button_layout.addWidget(scan_button)
        button_layout.addWidget(config_mapping_button)
        button_layout.addWidget(start_all_button)
        button_layout.addWidget(stop_all_button)
        button_layout.addWidget(capture_all_button)
        
        main_layout.addLayout(button_layout)
        
        # Create grid layout for camera previews
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        
        main_layout.addLayout(self.grid_layout)
    
    def _on_walnut_id_free_text_changed(self, text: str):
        """Handle walnut ID free text field change."""
        self.walnut_id_free_text = text.strip()
    
    def _on_walnut_id_number_changed(self, text: str):
        """Handle walnut ID number field change."""
        try:
            self.walnut_id_number = int(text.strip()) if text.strip() else 1
        except ValueError:
            self.walnut_id_number = 1
            self.walnut_id_number_input.setText("1")
    
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
            else:
                # Reload mapping and output folder, then check if all mapped cameras are still available
                self.camera_side_mapping, saved_output_folder = self.mapping_service.load_settings()
                if saved_output_folder:
                    self.output_folder = saved_output_folder
                elif not self.output_folder:
                    # Use default from config if no saved folder and no current folder
                    self.output_folder = self.app_config.camera.capture.output_folder
                
                missing_cameras = []
                for side, unique_id in self.camera_side_mapping.items():
                    if not any(cam.unique_id == unique_id for cam in self.available_cameras):
                        missing_cameras.append(f"{side.value.capitalize()}: {unique_id}")
                
                if missing_cameras:
                    QMessageBox.warning(
                        self,
                        "Mapped Cameras Not Found",
                        f"The following mapped cameras are no longer available:\n" +
                        "\n".join(missing_cameras) +
                        "\n\nPlease reconfigure camera mapping."
                    )
        except Exception as e:
            self.logger.error(f"Error scanning cameras: {e}")
            QMessageBox.critical(self, "Error", f"Failed to scan cameras: {e}")
        finally:
            loop.close()
    
    def configure_camera_mapping(self):
        """Open dialog to configure camera-to-side mapping."""
        if not self.available_cameras:
            QMessageBox.warning(self, "No Cameras", "Please scan for cameras first.")
            return
        
        dialog = CameraSideMappingDialog(
            available_cameras=self.available_cameras,
            mapping_service=self.mapping_service,
            default_output_folder=self.app_config.camera.capture.output_folder,
            parent=self
        )
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            new_mapping = dialog.get_mapping()
            new_output_folder = dialog.get_output_folder()
            self.camera_side_mapping = new_mapping
            self.output_folder = new_output_folder
            
            # Save mapping and output folder to file
            if self.mapping_service.save_settings(new_mapping, new_output_folder):
                QMessageBox.information(self, "Success", "Settings saved successfully.")
            else:
                QMessageBox.warning(self, "Warning", "Failed to save settings to file.")
    
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
        """Capture images from all cameras based on side mapping."""
        if not self.available_cameras:
            QMessageBox.warning(self, "No Cameras", "Please scan for cameras first.")
            return
        
        if not self.camera_side_mapping:
            QMessageBox.warning(
                self,
                "No Mapping",
                "Please configure camera-to-side mapping first.\n"
                "Click 'Configure Camera Mapping' to set up the mapping."
            )
            return
        
        if not self.walnut_id_free_text.strip():
            QMessageBox.warning(
                self,
                "Missing Walnut ID",
                "Please enter a free text for the walnut ID."
            )
            return
        
        if self.walnut_id_number < 1:
            QMessageBox.warning(
                self,
                "Invalid Walnut ID",
                "Walnut ID number must be at least 1."
            )
            return
        
        self.logger.info(f"Capturing from all cameras for walnut {self.walnut_id_free_text}__{self.walnut_id_number:04d}...")
        
        async def _capture_all():
            return await self.camera_capture_service.capture_all_cameras_async(
                camera_side_mapping=self.camera_side_mapping,
                available_cameras=self.available_cameras,
                preview_widgets=self.preview_widgets,
                walnut_id_free_text=self.walnut_id_free_text.strip(),
                walnut_id_number=self.walnut_id_number,
                output_folder=self.output_folder,
            )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            captured_count, total_sides, errors = loop.run_until_complete(_capture_all())
            
            message = f"Captured {captured_count} of {total_sides} sides."
            if errors:
                message += f"\nErrors:\n" + "\n".join(errors[:5])  # Show first 5 errors
                if len(errors) > 5:
                    message += f"\n... and {len(errors) - 5} more errors"
            
            if captured_count == total_sides:
                QMessageBox.information(self, "Capture Complete", message)
                # Auto-increment walnut ID number after successful capture
                self.walnut_id_number += 1
                self.walnut_id_number_input.setText(str(self.walnut_id_number))
            elif captured_count > 0:
                QMessageBox.warning(self, "Partial Capture", message)
            else:
                QMessageBox.critical(self, "Capture Failed", message)
        except Exception as e:
            self.logger.error(f"Error capturing cameras: {e}")
            QMessageBox.critical(self, "Error", f"Failed to capture cameras: {e}")
        finally:
            loop.close()
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.stop_all_previews()
        event.accept()
