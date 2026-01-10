# app__desktop/services/camera_capture_service.py
"""Service for capturing images from cameras."""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from common.camera_info import CameraInfo
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
        cameras: List[CameraInfo],
        preview_widgets: dict[str, any],  # unique_id -> CameraPreviewWidget (optional)
    ) -> Tuple[int, int, List[str]]:
        """
        Capture images from all cameras simultaneously.
        
        Args:
            cameras: List of available cameras
            preview_widgets: Dictionary mapping unique_id to CameraPreviewWidget instances
            
        Returns:
            Tuple of (captured_count, total_cameras, errors)
        """
        # Get output folder path
        output_folder_str = self.app_config.camera.capture.output_folder
        output_folder = Path(output_folder_str)
        if not output_folder.is_absolute():
            # Relative to workspace root (app__desktop -> walnut_pair)
            workspace_root = Path(__file__).parent.parent.parent
            output_folder = workspace_root / output_folder_str
        
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for this capture session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        preview_config = self.app_config.camera.preview
        capture_config = self.app_config.camera.capture
        
        captured_count = 0
        errors = []
        
        async def capture_from_camera(camera_info: CameraInfo) -> Tuple[bool, str]:
            """Capture a frame from a single camera."""
            # Check if camera is already open in preview widget
            widget = preview_widgets.get(camera_info.unique_id) if preview_widgets else None
            handle = None
            should_close_handle = False
            
            if widget is not None and widget.camera_handle is not None:
                # Camera is already open in preview, use its handle
                handle = widget.camera_handle
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
                    return False, f"Failed to open {camera_info.unique_id}"
                
                should_close_handle = True
                frame = await self.camera_service.capture_frame_async(handle)
            
            # Close handle if we opened it (not from preview)
            if should_close_handle and handle is not None:
                try:
                    await self.camera_service.close_camera_async(handle)
                except Exception as e:
                    self.logger.warning(f"Error closing camera {camera_info.unique_id}: {e}")
            
            if frame is None:
                return False, f"Failed to capture frame from {camera_info.unique_id}"
            
            # Build filename
            filename = capture_config.filename_format.format(
                unique_id=camera_info.unique_id,
                timestamp=timestamp
            )
            file_path = output_folder / filename
            
            # Save image
            success = await self.image_writer.save_image_async(frame, str(file_path))
            if success:
                self.logger.info(f"Captured {camera_info.unique_id} to {file_path}")
                return True, ""
            else:
                return False, f"Failed to save image from {camera_info.unique_id}"
        
        # Capture from all cameras in parallel
        capture_tasks = [capture_from_camera(camera_info) for camera_info in cameras]
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
        
        return captured_count, len(cameras), errors

