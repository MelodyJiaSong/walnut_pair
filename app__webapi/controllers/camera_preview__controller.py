# app__webapi/controllers/camera_preview__controller.py
"""Camera preview API controller."""
import asyncio
from typing import Dict, List, Set

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from common.camera_info import CameraInfo
from application_layer.queries.camera__query import ICameraQuery
from infrastructure_layer.services.camera_preview__service import ICameraPreviewService
from infrastructure_layer.services.camera__service import ICameraService, CameraHandle
from infrastructure_layer.file_writers.image_file__writer import IImageFileWriter
from app__webapi.dependencies import get_camera_query, get_camera_preview_service, get_camera_service, get_image_file_writer
from app__webapi.routes import (
    CAMERA_PREVIEW_BASE,
    CAMERA_PREVIEW_LIST,
    CAMERA_PREVIEW_START,
    CAMERA_PREVIEW_STOP,
    CAMERA_PREVIEW_STREAM,
    CAMERA_PREVIEW_CAPTURE,
)


class CameraInfoResponse(BaseModel):
    """Response model for camera information."""
    unique_id: str
    index: int
    name: str | None = None
    vid: int | None = None
    pid: int | None = None
    
    @classmethod
    def from_camera_info(cls, camera_info: CameraInfo) -> "CameraInfoResponse":
        """Create response from CameraInfo."""
        return cls(
            unique_id=camera_info.unique_id,
            index=camera_info.index,
            name=camera_info.name,
            vid=camera_info.vid,
            pid=camera_info.pid,
        )


class StartPreviewRequest(BaseModel):
    """Request model for starting camera preview."""
    camera_unique_id: str  # Use unique_id instead of index
    width: int = 640
    height: int = 480


class StopPreviewRequest(BaseModel):
    """Request model for stopping camera preview."""
    camera_unique_id: str  # Use unique_id instead of index

router = APIRouter(tags=["camera-preview"])


@router.get(
    CAMERA_PREVIEW_LIST,
    response_model=List[CameraInfoResponse],
    summary="List available cameras",
    description="Returns a list of available cameras with unique identifiers.",
)
async def list_available_cameras_async(
    camera_query: ICameraQuery = Depends(get_camera_query),
) -> List[CameraInfoResponse]:
    """Get list of available cameras with unique identifiers."""
    cameras = await camera_query.scan_available_cameras_async()
    return [CameraInfoResponse.from_camera_info(cam) for cam in cameras]


@router.post(
    CAMERA_PREVIEW_START,
    summary="Start camera preview",
    description="Start preview stream for a camera using unique identifier.",
)
async def start_camera_preview_async(
    request: StartPreviewRequest,
    camera_query: ICameraQuery = Depends(get_camera_query),
    preview_service: ICameraPreviewService = Depends(get_camera_preview_service),
) -> dict:
    """Start preview stream for a camera using unique identifier."""
    try:
        # Get camera info by unique_id to get the current index
        # This may take time if cameras are slow, but we have timeout protection
        camera_info = await asyncio.wait_for(
            camera_query.get_camera_by_unique_id_async(request.camera_unique_id),
            timeout=180.0  # 3 minutes timeout for lookup
        )
        if not camera_info:
            raise HTTPException(
                status_code=404,
                detail=f"Camera with unique_id '{request.camera_unique_id}' not found. It may not be available or still scanning."
            )
        
        # Use the index to start preview (preview service still uses indices internally)
        success = await preview_service.start_preview_async(
            camera_info.index, request.width, request.height
        )
        return {"success": success, "camera_unique_id": request.camera_unique_id, "camera_index": camera_info.index}
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Timeout looking up camera with unique_id '{request.camera_unique_id}'. Cameras may be slow to respond."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting camera preview: {str(e)}"
        )


@router.post(
    CAMERA_PREVIEW_STOP,
    summary="Stop camera preview",
    description="Stop preview stream for a camera using unique identifier.",
)
async def stop_camera_preview_async(
    request: StopPreviewRequest,
    camera_query: ICameraQuery = Depends(get_camera_query),
    preview_service: ICameraPreviewService = Depends(get_camera_preview_service),
) -> dict:
    """Stop preview stream for a camera using unique identifier."""
    # Get camera info by unique_id to get the current index
    camera_info = await camera_query.get_camera_by_unique_id_async(request.camera_unique_id)
    if not camera_info:
        raise HTTPException(status_code=404, detail=f"Camera with unique_id '{request.camera_unique_id}' not found")
    
    # Use the index to stop preview (preview service still uses indices internally)
    await preview_service.stop_preview_async(camera_info.index)
    return {"success": True, "camera_unique_id": request.camera_unique_id, "camera_index": camera_info.index}


@router.get(
    CAMERA_PREVIEW_STREAM,
    summary="Stream camera preview (MJPEG)",
    description="Stream camera preview as MJPEG for a specific camera using unique identifier.",
)
async def stream_camera_preview_async(
    camera_unique_id: str = Query(..., description="Camera unique identifier"),
    camera_query: ICameraQuery = Depends(get_camera_query),
    preview_service: ICameraPreviewService = Depends(get_camera_preview_service),
):
    """Stream camera preview as MJPEG using unique identifier."""
    # Get camera info by unique_id to get the current index
    camera_info = await camera_query.get_camera_by_unique_id_async(camera_unique_id)
    if not camera_info:
        raise HTTPException(status_code=404, detail=f"Camera with unique_id '{camera_unique_id}' not found")
    
    camera_index = camera_info.index
    
    async def generate_frames():
        while preview_service.is_preview_active(camera_index):
            frame_bytes = await preview_service.get_frame_async(camera_index)
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            await asyncio.sleep(0.033)  # ~30 FPS

    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.websocket(CAMERA_PREVIEW_STREAM + "/ws")
async def websocket_camera_preview(websocket: WebSocket):
    """WebSocket endpoint for camera preview streaming using unique identifier."""
    from app__webapi.dependencies import get_camera_preview_service, get_camera_query
    preview_service = get_camera_preview_service()
    camera_query = get_camera_query()
    
    await websocket.accept()
    
    # Get camera_unique_id from query string
    query_params = dict(websocket.query_params)
    camera_unique_id = query_params.get("camera_unique_id", "")
    
    if not camera_unique_id:
        await websocket.close(code=1008, reason="camera_unique_id parameter required")
        return
    
    # Get camera info by unique_id to get the current index
    camera_info = await camera_query.get_camera_by_unique_id_async(camera_unique_id)
    if not camera_info:
        await websocket.close(code=1008, reason=f"Camera with unique_id '{camera_unique_id}' not found")
        return
    
    camera_index = camera_info.index
    
    try:
        while preview_service.is_preview_active(camera_index):
            frame_bytes = await preview_service.get_frame_async(camera_index)
            if frame_bytes:
                await websocket.send_bytes(frame_bytes)
            await asyncio.sleep(0.033)  # ~30 FPS
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))


class CaptureAllResponse(BaseModel):
    """Response model for capture all cameras operation."""
    success: bool
    captured_count: int
    total_cameras: int
    saved_paths: List[Dict[str, str]]  # List of {camera_unique_id: file_path}
    errors: List[str]  # List of error messages


@router.post(
    CAMERA_PREVIEW_CAPTURE,
    response_model=CaptureAllResponse,
    summary="Capture all cameras",
    description="Capture images from all available cameras simultaneously and save to _test folder.",
)
async def capture_all_cameras_async(
    camera_query: ICameraQuery = Depends(get_camera_query),
    camera_service: ICameraService = Depends(get_camera_service),
    preview_service: ICameraPreviewService = Depends(get_camera_preview_service),
    image_writer: IImageFileWriter = Depends(get_image_file_writer),
) -> CaptureAllResponse:
    """Capture images from all available cameras simultaneously."""
    from pathlib import Path
    from datetime import datetime
    from typing import Optional, Tuple
    import numpy as np
    import cv2
    
    logger = __import__("common.logger", fromlist=["get_logger"]).get_logger(__name__)
    
    try:
        # Get all available cameras
        cameras = await camera_query.scan_available_cameras_async()
        if not cameras:
            return CaptureAllResponse(
                success=False,
                captured_count=0,
                total_cameras=0,
                saved_paths=[],
                errors=["No cameras available"]
            )
        
        # Create _test folder in workspace root
        workspace_root = Path(__file__).parent.parent.parent
        test_folder = workspace_root / "_test"
        test_folder.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for this capture session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get cameras that are already open in preview service
        active_preview_indices = preview_service.get_active_cameras()
        
        # Open cameras that aren't already open, or use preview service frames
        opened_cameras: Dict[str, Tuple[CameraHandle, CameraInfo, bool]] = {}  # unique_id -> (handle, info, is_from_preview)
        cameras_to_open: List[CameraInfo] = []
        
        for camera_info in cameras:
            if camera_info.index in active_preview_indices:
                # Camera is already open in preview service, we'll get frame from there
                logger.info(f"Camera {camera_info.unique_id} (index {camera_info.index}) is already open in preview service")
                # We'll handle this separately - get frame from preview service
                continue
            else:
                cameras_to_open.append(camera_info)
        
        # Open cameras that aren't already in preview
        for camera_info in cameras_to_open:
            try:
                camera_handle = await camera_service.open_camera_async(
                    index=camera_info.index,
                    width=640,
                    height=480,
                    buffer_size=1,
                    fourcc="MJPG",
                    auto_exposure=0.75
                )
                if camera_handle:
                    opened_cameras[camera_info.unique_id] = (camera_handle, camera_info, False)
                    logger.info(f"Opened camera {camera_info.unique_id} (index {camera_info.index})")
            except Exception as e:
                logger.warning(f"Failed to open camera {camera_info.unique_id}: {e}")
        
        # Capture frames from all cameras simultaneously
        async def capture_from_camera(unique_id: str, handle: CameraHandle) -> Optional[Tuple[str, np.ndarray]]:
            """Capture a frame from a single camera."""
            try:
                frame = await camera_service.capture_frame_async(handle)
                if frame is not None:
                    return (unique_id, frame)
                return None
            except Exception as e:
                logger.error(f"Error capturing from camera {unique_id}: {e}")
                return None
        
        async def capture_from_preview(camera_info: CameraInfo) -> Optional[Tuple[str, np.ndarray]]:
            """Capture a frame from preview service."""
            try:
                # Get frame bytes from preview service
                frame_bytes = await preview_service.get_frame_async(camera_info.index)
                if frame_bytes:
                    # Decode JPEG bytes to numpy array
                    nparr = np.frombuffer(frame_bytes, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        return (camera_info.unique_id, frame)
                return None
            except Exception as e:
                logger.error(f"Error capturing from preview camera {camera_info.unique_id}: {e}")
                return None
        
        # Create capture tasks
        capture_tasks = []
        for unique_id, (handle, camera_info, is_from_preview) in opened_cameras.items():
            capture_tasks.append(capture_from_camera(unique_id, handle))
        
        # Add tasks for cameras that are in preview service
        for camera_info in cameras:
            if camera_info.index in active_preview_indices:
                capture_tasks.append(capture_from_preview(camera_info))
        
        if not capture_tasks:
            return CaptureAllResponse(
                success=False,
                captured_count=0,
                total_cameras=len(cameras),
                saved_paths=[],
                errors=["No cameras available for capture"]
            )
        
        capture_results = await asyncio.gather(*capture_tasks, return_exceptions=True)
        
        # Save all captured images
        saved_paths: List[Dict[str, str]] = []
        errors: List[str] = []
        captured_count = 0
        
        for result in capture_results:
            if isinstance(result, Exception):
                errors.append(f"Capture error: {str(result)}")
                continue
            
            if result is None:
                continue
            
            unique_id, frame = result
            # Find camera info
            camera_info = None
            for cam in cameras:
                if cam.unique_id == unique_id:
                    camera_info = cam
                    break
            
            if not camera_info:
                errors.append(f"Camera info not found for {unique_id}")
                continue
            
            # Build file path: _test/cam_0_20240101_120000.jpg
            filename = f"{unique_id}_{timestamp}.jpg"
            file_path = test_folder / filename
            
            # Save image
            success = await image_writer.save_image_async(frame, str(file_path))
            if success:
                saved_paths.append({camera_info.unique_id: str(file_path)})
                captured_count += 1
                logger.info(f"Saved image from {unique_id} to {file_path}")
            else:
                errors.append(f"Failed to save image from {unique_id}")
        
        # Close only cameras we opened (not preview service cameras)
        for unique_id, (handle, _, is_from_preview) in opened_cameras.items():
            if not is_from_preview:
                try:
                    await camera_service.close_camera_async(handle)
                except Exception as e:
                    logger.warning(f"Error closing camera {unique_id}: {e}")
        
        return CaptureAllResponse(
            success=captured_count > 0,
            captured_count=captured_count,
            total_cameras=len(cameras),
            saved_paths=saved_paths,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error in capture_all_cameras_async: {e}", exc_info=True)
        return CaptureAllResponse(
            success=False,
            captured_count=0,
            total_cameras=0,
            saved_paths=[],
            errors=[f"Internal error: {str(e)}"]
        )

