# app__desktop/di_container.py
"""Desktop application dependency injection container."""
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Type

from dependency_injector import containers, providers

from common.di_container import (
    DependencyProviderWrapper,
    _container_resolve,
    _create_provider,
    _normalize_attr_name,
)
from common.di_registry import DIRegistry, Scope
from common.interfaces import IAppConfig
from infrastructure_layer.services.camera__service import ICameraService, CameraService
from infrastructure_layer.file_writers.image_file__writer import IImageFileWriter, ImageFileWriter
from app__desktop.app_config import DesktopAppConfig
from app__desktop.services.camera_capture_service import CameraCaptureService

if TYPE_CHECKING:
    from app__desktop.window import MainWindow


def create_camera_capture_service(
    camera_service: ICameraService,
    image_writer: IImageFileWriter,
    app_config: DesktopAppConfig,
) -> CameraCaptureService:
    """Factory function to create camera capture service."""
    return CameraCaptureService(
        camera_service=camera_service,
        image_writer=image_writer,
        app_config=app_config,
    )


# Register dependencies with scopes
DIRegistry.register(ICameraService, CameraService, Scope.SINGLETON)
DIRegistry.register(IImageFileWriter, ImageFileWriter, Scope.SINGLETON)
DIRegistry.register(IAppConfig, DesktopAppConfig, Scope.SINGLETON)


class DesktopContainer(containers.DeclarativeContainer):
    """
    Desktop application DI container.
    
    This is the composition root where all desktop-specific dependencies are wired together.
    Uses common DI utilities from common.di_container for generic functionality.
    """
    
    # Configuration
    config_path = providers.Configuration()
    
    # Core services
    app_config = providers.Singleton(
        lambda config_path: DesktopAppConfig.load_from_yaml(Path(config_path)),
        config_path=config_path,
    )
    
    # Camera services
    camera_service = providers.Singleton(CameraService)
    
    image_writer = providers.Singleton(ImageFileWriter)
    
    camera_capture_service = providers.Factory(
        create_camera_capture_service,
        camera_service=camera_service,
        image_writer=image_writer,
        app_config=app_config,
    )
    


def bootstrap_container(config_path: Path) -> DesktopContainer:
    """
    Bootstrap the desktop container by creating providers from DIRegistry.
    
    This function:
    1. Creates the container instance first
    2. Creates providers for all registered interfaces with their scopes
    3. Adds them to the container instance
    """
    # Create container instance first
    container = DesktopContainer()
    
    # Configure container with config path
    container.config_path.from_value(str(config_path))
    
    # Start with core providers that are already in the container
    providers_map: Dict[Type[Any], providers.Provider] = {
        IAppConfig: container.app_config,
        ICameraService: container.camera_service,
        IImageFileWriter: container.image_writer,
    }
    
    # Register all DIRegistry interfaces
    for interface in DIRegistry._registry.keys():
        if interface in providers_map:
            continue
        
        # Get registration info (implementation and scope)
        registration = DIRegistry.get_registration(interface)
        
        # Create provider for this interface with scope
        provider = _create_provider(
            interface,
            registration.implementation,
            providers_map,
            visited=set(),
            scope=registration.scope,
        )
        
        # Add as attribute to container instance
        attr_name = _normalize_attr_name(interface)
        setattr(container, attr_name, provider)
        providers_map[interface] = provider
    
    return container

