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
from app__webapi.dependencies import get_camera_query, get_camera_preview_service
from app__webapi.routes import (
    CAMERA_PREVIEW_BASE,
    CAMERA_PREVIEW_LIST,
    CAMERA_PREVIEW_START,
    CAMERA_PREVIEW_STOP,
    CAMERA_PREVIEW_STREAM,
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

