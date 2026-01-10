# app__desktop/app_config.py
"""Desktop application configuration."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from common.interfaces import IAppConfig
from common.path_utils import normalize_path


@dataclass
class CameraPreviewConfig:
    """Camera preview configuration."""
    width: int
    height: int
    buffer_size: int
    fourcc: str
    auto_exposure: float


@dataclass
class CameraCaptureConfig:
    """Camera capture configuration."""
    output_folder: str
    filename_format: str


@dataclass
class CameraConfig:
    """Camera configuration."""
    max_scan_index: int
    preview: CameraPreviewConfig
    capture: CameraCaptureConfig


@dataclass
class GridConfig:
    """Grid layout configuration."""
    columns: int


@dataclass
class WindowConfig:
    """Window configuration."""
    title: str
    min_width: int
    min_height: int


@dataclass
class UIConfig:
    """UI configuration."""
    grid: GridConfig
    window: WindowConfig


class DesktopAppConfig(IAppConfig):
    """Desktop application configuration implementation."""
    
    def __init__(
        self,
        camera: dict,
        ui: dict,
    ) -> None:
        """
        Initialize Desktop application configuration.
        
        Args:
            camera: Camera configuration dictionary
            ui: UI configuration dictionary
        """
        # Camera configuration - all fields required
        if "max_scan_index" not in camera:
            raise ValueError("Camera configuration must include 'max_scan_index'")
        if "preview" not in camera:
            raise ValueError("Camera configuration must include 'preview'")
        if "capture" not in camera:
            raise ValueError("Camera configuration must include 'capture'")
        
        camera_preview = camera["preview"]
        camera_capture = camera["capture"]
        
        # Validate preview config fields
        required_preview_fields = ["width", "height", "buffer_size", "fourcc", "auto_exposure"]
        for field in required_preview_fields:
            if field not in camera_preview:
                raise ValueError(f"Camera preview configuration must include '{field}'")
        
        # Validate capture config fields
        required_capture_fields = ["output_folder", "filename_format"]
        for field in required_capture_fields:
            if field not in camera_capture:
                raise ValueError(f"Camera capture configuration must include '{field}'")
        
        self._camera = CameraConfig(
            max_scan_index=camera["max_scan_index"],
            preview=CameraPreviewConfig(**camera_preview),
            capture=CameraCaptureConfig(**camera_capture),
        )
        
        # UI configuration - all fields required
        if "grid" not in ui:
            raise ValueError("UI configuration must include 'grid'")
        if "window" not in ui:
            raise ValueError("UI configuration must include 'window'")
        
        grid_data = ui["grid"]
        window_data = ui["window"]
        
        # Validate grid config fields
        if "columns" not in grid_data:
            raise ValueError("UI grid configuration must include 'columns'")
        
        # Validate window config fields
        required_window_fields = ["title", "min_width", "min_height"]
        for field in required_window_fields:
            if field not in window_data:
                raise ValueError(f"UI window configuration must include '{field}'")
        
        self._ui = UIConfig(
            grid=GridConfig(**grid_data),
            window=WindowConfig(**window_data),
        )
        
        # Set defaults for IAppConfig interface (not used in desktop app)
        self._image_root: str = ""
        self._database = None
        self._algorithm = None
    
    @property
    def camera(self) -> CameraConfig:
        """Get camera configuration."""
        return self._camera
    
    @property
    def ui(self) -> UIConfig:
        """Get UI configuration."""
        return self._ui
    
    # IAppConfig interface properties (not used in desktop app)
    @property
    def image_root(self) -> str:
        """Get the root path for images (not used in desktop app)."""
        return self._image_root
    
    @property
    def database(self):
        """Get the database configuration (not used in desktop app)."""
        return self._database
    
    @property
    def cameras(self):
        """Get camera configurations (not used in desktop app, use self.camera instead)."""
        return {}
    
    def get_camera_config(self, side):
        """Get camera configuration for a specific side (not used in desktop app)."""
        return None
    
    @property
    def algorithm(self):
        """Get algorithm comparison configuration (not used in desktop app)."""
        return self._algorithm
    
    @classmethod
    def load_from_yaml(cls, yaml_path: Path) -> "DesktopAppConfig":
        """
        Load configuration from YAML file.
        
        Args:
            yaml_path: Path to YAML configuration file
            
        Returns:
            DesktopAppConfig instance
        """
        with open(yaml_path, "r") as f:
            cfg = yaml.safe_load(f)
        
        # Validate required fields explicitly
        if "camera" not in cfg:
            raise ValueError("Configuration file must include 'camera' section")
        if "ui" not in cfg:
            raise ValueError("Configuration file must include 'ui' section")
        
        # Normalize output folder path if it's an absolute path
        if "capture" in cfg["camera"] and "output_folder" in cfg["camera"]["capture"]:
            output_folder = cfg["camera"]["capture"]["output_folder"]
            # If it's an absolute path, normalize it
            if output_folder.startswith("/") or output_folder.startswith("\\") or ":" in output_folder:
                cfg["camera"]["capture"]["output_folder"] = normalize_path(output_folder)
        
        return cls(
            camera=cfg["camera"],
            ui=cfg["ui"],
        )

