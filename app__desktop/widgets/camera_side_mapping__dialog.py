# app__desktop/widgets/camera_side_mapping__dialog.py
"""Dialog for configuring camera-to-side mapping."""
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
)

from common.enums import WalnutSideEnum
from common.camera_info import CameraInfo
from common.logger import get_logger
from app__desktop.services.camera_side_mapping__service import CameraSideMappingService


class CameraSideMappingDialog(QDialog):
    """Dialog for assigning cameras to walnut sides."""
    
    def __init__(
        self,
        available_cameras: List[CameraInfo],
        mapping_service: CameraSideMappingService,
        default_output_folder: str = "",
        parent=None
    ):
        """
        Initialize camera side mapping dialog.
        
        Args:
            available_cameras: List of available cameras
            mapping_service: Service for loading/saving mapping
            default_output_folder: Default output folder from config (used if not set in saved settings)
            parent: Parent widget
        """
        super().__init__(parent)
        self.available_cameras = available_cameras
        self.mapping_service = mapping_service
        self.default_output_folder = default_output_folder
        self.logger = get_logger(__name__)
        
        self.setWindowTitle("Camera to Side Mapping & Settings")
        self.setMinimumWidth(500)
        
        # ComboBoxes for each side
        self.side_combos: Dict[WalnutSideEnum, QComboBox] = {}
        self.output_folder_input: Optional[QLineEdit] = None
        
        self._setup_ui()
        self._load_current_settings()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Configure camera-to-side mapping and output folder.\n"
            "Each side must have a unique camera assigned."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Output folder configuration section
        output_folder_label = QLabel("Output Folder:")
        output_folder_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(output_folder_label)
        
        self.output_folder_input = QLineEdit()
        self.output_folder_input.setPlaceholderText("Enter folder path or click Browse...")
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_output_folder)
        
        output_folder_layout = QHBoxLayout()
        output_folder_layout.addWidget(self.output_folder_input)
        output_folder_layout.addWidget(browse_button)
        
        layout.addLayout(output_folder_layout)
        
        # Separator
        separator = QLabel("")
        separator.setMinimumHeight(10)
        layout.addWidget(separator)
        
        # Camera mapping section
        mapping_label = QLabel("Camera to Side Mapping:")
        mapping_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(mapping_label)
        
        # Form layout for side selection
        form_layout = QFormLayout()
        
        # Create combobox for each side
        for side in WalnutSideEnum:
            combo = QComboBox()
            combo.addItem("(None)", None)
            
            # Add available cameras
            for camera in self.available_cameras:
                combo.addItem(f"{camera.unique_id} (Index {camera.index})", camera.unique_id)
            
            # Capitalize first letter of side name for display
            side_display_name = side.value.capitalize()
            form_layout.addRow(f"{side_display_name}:", combo)
            
            self.side_combos[side] = combo
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _browse_output_folder(self):
        """Open file dialog to browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            self.output_folder_input.text() or ".",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.output_folder_input.setText(folder)
    
    def _load_current_settings(self):
        """Load current mapping and output folder, then populate UI."""
        mapping, output_folder = self.mapping_service.load_settings()
        
        # Load output folder - use saved folder or fall back to default from config
        if self.output_folder_input:
            display_folder = output_folder if output_folder else self.default_output_folder
            self.output_folder_input.setText(display_folder)
        
        # Load mapping
        for side, camera_unique_id in mapping.items():
            combo = self.side_combos.get(side)
            if combo is None:
                continue
            
            # Find index of camera_unique_id in combo
            for i in range(combo.count()):
                if combo.itemData(i) == camera_unique_id:
                    combo.setCurrentIndex(i)
                    break
    
    def _validate_and_accept(self):
        """Validate mapping before accepting."""
        # Check that each camera is assigned to at most one side
        assigned_cameras: Dict[str, WalnutSideEnum] = {}
        
        for side, combo in self.side_combos.items():
            camera_unique_id = combo.currentData()
            if camera_unique_id is None:
                continue
            
            if camera_unique_id in assigned_cameras:
                other_side = assigned_cameras[camera_unique_id]
                QMessageBox.warning(
                    self,
                    "Invalid Mapping",
                    f"Camera {camera_unique_id} is already assigned to {other_side.value.capitalize()}.\n"
                    f"Each camera can only be assigned to one side."
                )
                return
            
            assigned_cameras[camera_unique_id] = side
        
        # Check that all 6 sides are assigned
        unassigned_sides = [
            side for side in WalnutSideEnum
            if self.side_combos[side].currentData() is None
        ]
        
        if unassigned_sides:
            unassigned_names = [side.value.capitalize() for side in unassigned_sides]
            reply = QMessageBox.question(
                self,
                "Incomplete Mapping",
                f"The following sides are not assigned:\n{', '.join(unassigned_names)}\n\n"
                f"Do you want to continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        self.accept()
    
    def get_mapping(self) -> Dict[WalnutSideEnum, str]:
        """
        Get the current mapping from the dialog.
        
        Returns:
            Dictionary mapping WalnutSideEnum to camera unique_id
        """
        mapping: Dict[WalnutSideEnum, str] = {}
        
        for side, combo in self.side_combos.items():
            camera_unique_id = combo.currentData()
            if camera_unique_id is not None:
                mapping[side] = camera_unique_id
        
        return mapping
    
    def get_output_folder(self) -> str:
        """
        Get the output folder from the dialog.
        
        Returns:
            Output folder path string
        """
        if self.output_folder_input:
            return self.output_folder_input.text().strip()
        return ""

