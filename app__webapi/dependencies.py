# app__webapi/dependencies.py
"""FastAPI dependency injection setup with request scoping."""
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application_layer.queries.camera__query import ICameraQuery, CameraQuery
from application_layer.queries.walnut_comparison__query import IWalnutComparisonQuery
from infrastructure_layer.services.camera__service import ICameraService, CameraService
from infrastructure_layer.services.camera_preview__service import ICameraPreviewService, CameraPreviewService
from infrastructure_layer.file_writers.image_file__writer import IImageFileWriter, ImageFileWriter
from app__webapi.di_container import WebAPIContainer, bootstrap_webapi_container

# Global container instance (Singleton scope)
_container: Optional[WebAPIContainer] = None

# Global singleton services
_camera_service: Optional[ICameraService] = None
_camera_preview_service: Optional[ICameraPreviewService] = None
_camera_query: Optional[ICameraQuery] = None
_image_file_writer: Optional[IImageFileWriter] = None


def get_container() -> WebAPIContainer:
    """Get or create the global DI container (Singleton scope)."""
    global _container
    if _container is None:
        project_root = Path(__file__).resolve().parent.parent
        config_path = project_root / "app__webapi" / "config.yml"
        _container = bootstrap_webapi_container(config_path)
    return _container


async def get_session(
    container: WebAPIContainer = Depends(get_container),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get async session for current request (Request scope).
    
    This dependency creates a new session per request and ensures
    it's properly closed after the request completes.
    """
    session = container.session()
    try:
        yield session
    finally:
        await session.close()


def get_camera_service() -> ICameraService:
    """Get camera service (singleton)."""
    global _camera_service
    if _camera_service is None:
        _camera_service = CameraService()
    return _camera_service


def get_camera_preview_service(
    camera_service: ICameraService = Depends(get_camera_service),
) -> ICameraPreviewService:
    """Get camera preview service (singleton)."""
    global _camera_preview_service
    if _camera_preview_service is None:
        _camera_preview_service = CameraPreviewService(camera_service)
    return _camera_preview_service


def get_camera_query(
    camera_service: ICameraService = Depends(get_camera_service),
) -> ICameraQuery:
    """Get camera query service (singleton)."""
    global _camera_query
    if _camera_query is None:
        _camera_query = CameraQuery(camera_service, max_scan_index=15)
    return _camera_query


def get_image_file_writer() -> IImageFileWriter:
    """Get image file writer (singleton)."""
    global _image_file_writer
    if _image_file_writer is None:
        _image_file_writer = ImageFileWriter()
    return _image_file_writer


def get_walnut_comparison_query(
    session: AsyncSession = Depends(get_session),
    container: WebAPIContainer = Depends(get_container),
) -> IWalnutComparisonQuery:
    """
    Get walnut comparison query service for current request (Request scope).
    
    Creates a new query instance per request with the request-scoped session.
    """
    # Create a new reader with the request-scoped session
    from infrastructure_layer.db_readers import WalnutComparisonDBReader
    from application_layer.queries.walnut_comparison__query import WalnutComparisonQuery
    
    reader = WalnutComparisonDBReader(session)
    mapper = container.walnut_comparison_mapper()
    return WalnutComparisonQuery(comparison_reader=reader, comparison_mapper=mapper)


def shutdown_container() -> None:
    """Clean up container resources on shutdown."""
    global _container, _camera_preview_service
    if _camera_preview_service is not None:
        # Stop all active previews gracefully
        import asyncio
        try:
            active_cameras = list(_camera_preview_service.get_active_cameras())
            if active_cameras:
                # Create tasks to stop all previews
                tasks = [
                    _camera_preview_service.stop_preview_async(camera_index)
                    for camera_index in active_cameras
                ]
                # Run cleanup synchronously if possible, or create tasks
                loop = None
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, create tasks
                        for task in tasks:
                            asyncio.create_task(task)
                    else:
                        # If loop exists but not running, run cleanup
                        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                except RuntimeError:
                    # No event loop, create a new one for cleanup
                    asyncio.run(asyncio.gather(*tasks, return_exceptions=True))
        except Exception as e:
            # Log but don't fail on shutdown cleanup
            import logging
            logging.getLogger(__name__).warning(f"Error during camera preview cleanup: {e}")
        finally:
            _camera_preview_service = None
    if _container is not None:
        try:
            session_factory = _container.session_factory()
            if session_factory is not None and hasattr(session_factory, "engine"):
                # Note: This is called during shutdown, so we can't use await
                # The engine will be disposed when the process exits
                pass
        except Exception:
            pass
        _container = None
