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
    width: int = 640
    height: int = 480
    buffer_size: int = 1
    fourcc: str = "MJPG"
    auto_exposure: float = 0.75


@dataclass
class CameraCaptureConfig:
    """Camera capture configuration."""
    output_folder: str = "_test"
    filename_format: str = "{unique_id}_{timestamp}.jpg"


@dataclass
class CameraConfig:
    """Camera configuration."""
    max_scan_index: int = 15
    preview: Optional[CameraPreviewConfig] = None
    capture: Optional[CameraCaptureConfig] = None

    def __post_init__(self):
        if self.preview is None:
            self.preview = CameraPreviewConfig()
        if self.capture is None:
            self.capture = CameraCaptureConfig()


@dataclass
class GridConfig:
    """Grid layout configuration."""
    columns: int = 2


@dataclass
class WindowConfig:
    """Window configuration."""
    title: str = "Walnut Camera Preview"
    min_width: int = 1280
    min_height: int = 720


@dataclass
class UIConfig:
    """UI configuration."""
    grid: Optional[GridConfig] = None
    window: Optional[WindowConfig] = None

    def __post_init__(self):
        if self.grid is None:
            self.grid = GridConfig()
        if self.window is None:
            self.window = WindowConfig()


class DesktopAppConfig(IAppConfig):
    """Desktop application configuration implementation."""
    
    def __init__(
        self,
        camera: dict,
        ui: Optional[dict] = None,
    ) -> None:
        """
        Initialize Desktop application configuration.
        
        Args:
            camera: Camera configuration dictionary
            ui: UI configuration dictionary (optional)
        """
        # Camera configuration
        camera_preview = camera.get("preview", {})
        camera_capture = camera.get("capture", {})
        
        self._camera = CameraConfig(
            max_scan_index=camera.get("max_scan_index", 15),
            preview=CameraPreviewConfig(**camera_preview),
            capture=CameraCaptureConfig(**camera_capture),
        )
        
        # UI configuration
        ui_data = ui or {}
        grid_data = ui_data.get("grid", {})
        window_data = ui_data.get("window", {})
        
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
        
        # Normalize output folder path if present
        if "camera" in cfg and "capture" in cfg["camera"] and "output_folder" in cfg["camera"]["capture"]:
            output_folder = cfg["camera"]["capture"]["output_folder"]
            # If it's an absolute path, normalize it
            if output_folder.startswith("/") or output_folder.startswith("\\") or ":" in output_folder:
                cfg["camera"]["capture"]["output_folder"] = normalize_path(output_folder)
        
        return cls(**cfg)

