# app__desktop/services/camera_capture_service.py
"""Service for capturing images from cameras."""
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from common.camera_info import CameraInfo
from common.enums import WalnutSideEnum
from common.logger import get_logger
from infrastructure_layer.services.camera__service import ICameraService
from infrastructure_layer.file_writers.image_file__writer import IImageFileWriter
from app__desktop.app_config import DesktopAppConfig


class CameraCaptureService:
    """Service for capturing images from multiple cameras."""
    
    def __init__(
        self,
        camera_service: ICameraService,
        image_writer: IImageFileWriter,
        app_config: DesktopAppConfig,
    ):
        """
        Initialize camera capture service.
        
        Args:
            camera_service: Camera service instance
            image_writer: Image file writer instance
            app_config: Application configuration
        """
        self.camera_service = camera_service
        self.image_writer = image_writer
        self.app_config = app_config
        self.logger = get_logger(__name__)
    
    async def capture_all_cameras_async(
        self,
        camera_side_mapping: Dict[WalnutSideEnum, str],
        available_cameras: List[CameraInfo],
        preview_widgets: Dict[str, any],  # unique_id -> CameraPreviewWidget (optional)
        walnut_id_free_text: str,
        walnut_id_number: int,
        output_folder: str,
    ) -> Tuple[int, int, List[str]]:
        """
        Capture images from all cameras based on side mapping.
        
        Args:
            camera_side_mapping: Dictionary mapping WalnutSideEnum to camera unique_id
            available_cameras: List of available cameras
            preview_widgets: Dictionary mapping unique_id to CameraPreviewWidget instances
            walnut_id_free_text: Free text part of walnut ID
            walnut_id_number: Auto-increment number part of walnut ID
            output_folder: Output folder path (can be relative or absolute)
            
        Returns:
            Tuple of (captured_count, total_sides, errors)
        """
        # Build full walnut ID: {free_text}__{number}
        full_walnut_id = f"{walnut_id_free_text}__{walnut_id_number:04d}"
        
        # Get output folder path
        # Use provided output_folder, or fall back to config if empty
        if not output_folder:
            output_folder_str = self.app_config.camera.capture.output_folder
        else:
            output_folder_str = output_folder
        
        output_folder_path = Path(output_folder_str)
        if not output_folder_path.is_absolute():
            # Relative to workspace root (app__desktop -> walnut_pair)
            workspace_root = Path(__file__).parent.parent.parent
            output_folder_path = workspace_root / output_folder_str
        
        # Create walnut-specific folder: {full_id}/
        walnut_folder = output_folder_path / full_walnut_id
        walnut_folder.mkdir(parents=True, exist_ok=True)
        
        preview_config = self.app_config.camera.preview
        
        # Build mapping from unique_id to CameraInfo for faster lookup
        unique_id_to_camera: Dict[str, CameraInfo] = {}
        for camera in available_cameras:
            unique_id_to_camera[camera.unique_id] = camera
        
        captured_count = 0
        errors = []
        
        async def capture_from_side(side: WalnutSideEnum, camera_unique_id: str) -> Tuple[bool, str]:
            """Capture a frame from a camera for a specific side."""
            # Find camera info to get index
            camera_info = unique_id_to_camera.get(camera_unique_id)
            if camera_info is None:
                return False, f"Camera {camera_unique_id} not found for side {side.value}"
            
            # Check if camera is already open in preview widget
            widget = preview_widgets.get(camera_unique_id) if preview_widgets else None
            handle = None
            should_close_handle = False
            
            if widget is not None and widget.camera_handle is not None:
                # Camera is already open in preview, use its handle
                handle = widget.camera_handle
                frame = widget.capture_frame()
                if frame is None:
                    frame = await self.camera_service.capture_frame_async(handle)
            else:
                # Open camera temporarily for capture
                handle = await self.camera_service.open_camera_async(
                    index=camera_info.index,
                    width=preview_config.width,
                    height=preview_config.height,
                    buffer_size=preview_config.buffer_size,
                    fourcc=preview_config.fourcc,
                    auto_exposure=preview_config.auto_exposure
                )
                
                if handle is None:
                    return False, f"Failed to open {camera_unique_id} for side {side.value}"
                
                should_close_handle = True
                frame = await self.camera_service.capture_frame_async(handle)
            
            # Close handle if we opened it (not from preview)
            if should_close_handle and handle is not None:
                try:
                    await self.camera_service.close_camera_async(handle)
                except Exception as e:
                    self.logger.warning(f"Error closing camera {camera_unique_id}: {e}")
            
            if frame is None:
                return False, f"Failed to capture frame from {camera_unique_id} for side {side.value}"
            
            # Build filename: {full_id}__{side}.jpg
            filename = f"{full_walnut_id}__{side.value}.jpg"
            file_path = walnut_folder / filename
            
            # Save image
            success = await self.image_writer.save_image_async(frame, str(file_path))
            if success:
                self.logger.info(f"Captured {side.value} ({camera_unique_id}) to {file_path}")
                return True, ""
            else:
                return False, f"Failed to save image for side {side.value}"
        
        # Capture from all mapped sides in parallel
        capture_tasks = [
            capture_from_side(side, camera_unique_id)
            for side, camera_unique_id in camera_side_mapping.items()
        ]
        capture_results = await asyncio.gather(*capture_tasks, return_exceptions=True)
        
        # Process results
        for result in capture_results:
            if isinstance(result, Exception):
                errors.append(f"Capture error: {str(result)}")
                continue
            
            success, error_msg = result
            if success:
                captured_count += 1
            else:
                errors.append(error_msg)
        
        return captured_count, len(camera_side_mapping), errors

