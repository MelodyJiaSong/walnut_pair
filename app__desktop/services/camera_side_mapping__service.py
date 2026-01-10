# app__desktop/services/camera_side_mapping__service.py
"""Service for managing camera-to-side mapping configuration."""
import json
from pathlib import Path
from typing import Dict, Optional

from common.enums import WalnutSideEnum
from common.logger import get_logger
from common.camera_info import CameraInfo


class CameraSideMappingService:
    """Service for persisting and loading camera-to-side mapping."""
    
    def __init__(self, mapping_file_path: Optional[Path] = None):
        """
        Initialize camera side mapping service.
        
        Args:
            mapping_file_path: Path to the mapping file. If None, uses default location.
        """
        if mapping_file_path is None:
            # Default location: workspace root / .camera_side_mapping.json
            workspace_root = Path(__file__).parent.parent.parent
            mapping_file_path = workspace_root / ".camera_side_mapping.json"
        
        self.mapping_file_path = mapping_file_path
        self.logger = get_logger(__name__)
    
    def load_mapping(self) -> Dict[WalnutSideEnum, str]:
        """
        Load camera-to-side mapping from file.
        
        Returns:
            Dictionary mapping WalnutSideEnum to camera unique_id
        """
        if not self.mapping_file_path.exists():
            self.logger.info(f"Mapping file does not exist: {self.mapping_file_path}")
            return {}
        
        try:
            with open(self.mapping_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Convert string keys to WalnutSideEnum
            mapping: Dict[WalnutSideEnum, str] = {}
            for side_str, camera_unique_id in data.items():
                try:
                    side_enum = WalnutSideEnum(side_str.lower())
                    mapping[side_enum] = camera_unique_id
                except ValueError:
                    self.logger.warning(f"Invalid side '{side_str}' in mapping file, skipping")
            
            self.logger.info(f"Loaded mapping from {self.mapping_file_path}: {len(mapping)} entries")
            return mapping
        except Exception as e:
            self.logger.error(f"Error loading mapping file: {e}")
            return {}
    
    def save_mapping(self, mapping: Dict[WalnutSideEnum, str]) -> bool:
        """
        Save camera-to-side mapping to file.
        
        Args:
            mapping: Dictionary mapping WalnutSideEnum to camera unique_id
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Convert WalnutSideEnum keys to strings
            data = {side.value: camera_unique_id for side, camera_unique_id in mapping.items()}
            
            # Ensure directory exists
            self.mapping_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.mapping_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved mapping to {self.mapping_file_path}: {len(mapping)} entries")
            return True
        except Exception as e:
            self.logger.error(f"Error saving mapping file: {e}")
            return False
    
    def get_camera_for_side(
        self,
        side: WalnutSideEnum,
        available_cameras: list[CameraInfo],
        mapping: Optional[Dict[WalnutSideEnum, str]] = None
    ) -> Optional[CameraInfo]:
        """
        Get the camera assigned to a specific side.
        
        Args:
            side: The walnut side
            available_cameras: List of currently available cameras
            mapping: Optional mapping dictionary. If None, loads from file.
            
        Returns:
            CameraInfo if found, None otherwise
        """
        if mapping is None:
            mapping = self.load_mapping()
        
        camera_unique_id = mapping.get(side)
        if camera_unique_id is None:
            return None
        
        # Find camera by unique_id
        for camera in available_cameras:
            if camera.unique_id == camera_unique_id:
                return camera
        
        return None

