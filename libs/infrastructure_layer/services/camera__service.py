# infrastructure_layer/services/camera__service.py
"""Camera service for capturing images from cameras."""
import asyncio
import hashlib
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np

from common.camera_info import CameraInfo
from common.logger import get_logger

# Type alias for camera handle
CameraHandle = cv2.VideoCapture


class ICameraService(ABC):
    """Interface for camera operations."""

    @abstractmethod
    async def test_camera_available_async(self, index: int, timeout: float = 2.0) -> bool:
        """
        Quick test if camera index is available.
        
        Args:
            index: Camera device index
            timeout: Maximum time to wait for camera test (default: 2 seconds)
            
        Returns:
            True if camera is available, False otherwise
        """
        pass

    @abstractmethod
    async def open_camera_async(
        self, index: int, width: int, height: int, buffer_size: int = 1, fourcc: str = "MJPG", auto_exposure: float = 0.75
    ) -> Optional[CameraHandle]:
        """
        Open a camera with specified settings.
        
        Args:
            index: Camera device index
            width: Frame width
            height: Frame height
            buffer_size: Buffer size (1 for low latency)
            fourcc: FourCC codec (default: "MJPG")
            auto_exposure: Auto exposure setting (0.75 = auto)
            
        Returns:
            CameraHandle if successful, None otherwise
        """
        pass

    @abstractmethod
    async def capture_frame_async(self, camera: CameraHandle) -> Optional[np.ndarray]:
        """
        Capture a single frame from the camera.
        
        Args:
            camera: Camera handle
            
        Returns:
            Frame as numpy array (BGR format) if successful, None otherwise
        """
        pass

    @abstractmethod
    async def close_camera_async(self, camera: CameraHandle) -> None:
        """
        Close and release a camera.
        
        Args:
            camera: Camera handle to close
        """
        pass

    @abstractmethod
    async def scan_available_cameras_async(self, max_index: int) -> List[CameraInfo]:
        """
        Scan for available cameras and return unique identifiers.
        
        Args:
            max_index: Maximum camera index to scan (0 to max_index)
            
        Returns:
            List of CameraInfo objects with unique identifiers
        """
        pass
    
    @abstractmethod
    async def get_camera_info_async(self, index: int) -> Optional[CameraInfo]:
        """
        Get unique identifier and information for a camera at a specific index.
        
        Args:
            index: Camera device index
            
        Returns:
            CameraInfo if camera is available, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_camera_by_unique_id_async(self, unique_id: str) -> Optional[CameraInfo]:
        """
        Get camera information by unique identifier (logical ID).
        
        Args:
            unique_id: Logical camera identifier (e.g., "cam_0", "cam_1")
            
        Returns:
            CameraInfo if found, None otherwise
        """
        pass


class CameraService(ICameraService):
    """Implementation of camera service using OpenCV."""

    def __init__(self, registry_file: Optional[Path] = None) -> None:
        self.logger = get_logger(__name__)
        # Reduce OpenCV log verbosity - suppress warnings
        try:
            import os
            # Set OpenCV to only show errors, suppress warnings
            os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
            cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
            # Also suppress stderr for OpenCV warnings
            import warnings
            warnings.filterwarnings('ignore', category=UserWarning, module='cv2')
        except Exception:
            pass
        
        # Initialize camera registry for stable identification
        if registry_file is None:
            registry_file = Path(__file__).parent.parent.parent.parent / ".camera_registry.json"
        self.registry_file = registry_file
        self._camera_mapping: Dict[str, CameraInfo] = {}  # logical_id -> CameraInfo
        self._index_to_logical: Dict[int, str] = {}  # index -> logical_id

    async def test_camera_available_async(self, index: int, timeout: float = 120.0) -> bool:
        """
        Test if a camera index is available.

        The function is async for interface consistency but the actual
        implementation is synchronous and runs in a thread.

        Args:
            index: Camera device index.
            timeout: Unused, kept for compatibility.
        """

        def _test_sync() -> bool:
            """Synchronous check if a camera can be opened."""
            import warnings

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
                if not cap:
                    return False
                try:
                    if not cap.isOpened():
                        return False
                    return True
                finally:
                    cap.release()

        return await asyncio.to_thread(_test_sync)

    async def open_camera_async(
        self, index: int, width: int, height: int, buffer_size: int = 1, fourcc: str = "MJPG", auto_exposure: float = 0.75
    ) -> Optional[CameraHandle]:
        """
        Open camera with fallback backends.
        
        All cameras are treated equally with the same timeout.
        Tries backends in order with timeouts to prevent hanging.
        Camera settings are configured in a single batch operation for efficiency.
        """
        def _open_sync() -> Optional[CameraHandle]:
            """Synchronously open camera with fallback backends."""
            import warnings
            backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW, cv2.CAP_ANY]
            
            for backend in backends:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    cap = cv2.VideoCapture(index, backend)
                    if cap and cap.isOpened():
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size)
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
                        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, auto_exposure)
                        self.logger.info(f"Opened camera {index} with backend {backend}")
                        return cap
                    elif cap:
                        cap.release()
            return None
        
        cap = await asyncio.wait_for(
            asyncio.to_thread(_open_sync),
            timeout=120.0
        )
        if not cap:
            self.logger.error(f"Failed to open camera {index} with any backend")
        return cap

    async def capture_frame_async(self, camera: CameraHandle) -> Optional[np.ndarray]:
        """Capture a single frame from the camera."""
        def _capture_sync() -> Optional[np.ndarray]:
            """Synchronously capture a frame."""
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ok, frame = camera.read()
                if ok and frame is not None:
                    return frame
            return None
        
        return await asyncio.to_thread(_capture_sync)

    async def close_camera_async(self, camera: CameraHandle) -> None:
        """Close and release a camera."""
        await asyncio.to_thread(camera.release)
        self.logger.info("Camera closed")

    def _create_fingerprint(self, index: int, width: int, height: int, fps: int, backend: str) -> str:
        """Create deterministic fingerprint for camera identification."""
        payload = {"index": index, "width": width, "height": height, "fps": fps, "backend": backend}
        raw = json.dumps(payload, sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()[:16]
    
    async def get_camera_info_async(self, index: int) -> Optional[CameraInfo]:
        """
        Get unique identifier and information for a camera at a specific index.
        
        Enumerates camera properties to create a deterministic fingerprint.
        """
        def _get_info_sync() -> Optional[CameraInfo]:
            """Synchronously enumerate camera properties."""
            import warnings
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
                if not cap or not cap.isOpened():
                    if cap:
                        cap.release()
                    return None
                
                # Capture a frame to ensure camera is working
                ret, frame = cap.read()
                if not ret:
                    cap.release()
                    return None
                
                # Get camera properties for fingerprinting
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
                backend = cap.getBackendName() or "MSMF"
                
                cap.release()
                
                # Create fingerprint and unique_id
                fingerprint = self._create_fingerprint(index, width, height, fps, backend)
                unique_id = f"cam_{fingerprint}"
                
                return CameraInfo(
                    unique_id=unique_id,
                    index=index,
                    name=f"Camera {index}"
                )
        
        return await asyncio.wait_for(
            asyncio.to_thread(_get_info_sync),
            timeout=120.0
        )
    
    def _load_mapping(self) -> Dict[str, Dict]:
        """Load camera mapping from registry file."""
        if not self.registry_file.exists():
            return {}
        try:
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load camera mapping: {e}")
            return {}
    
    def _save_mapping(self, mapping: Dict[str, Dict]) -> None:
        """Save camera mapping to registry file."""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(mapping, f, indent=2)
            self.logger.debug(f"Saved camera mapping to {self.registry_file}")
        except Exception as e:
            self.logger.warning(f"Failed to save camera mapping: {e}")
    
    def _get_camera_props(self, index: int) -> tuple:
        """Get camera properties synchronously."""
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
            if cap and cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
                backend = cap.getBackendName() or "MSMF"
                cap.release()
                return width, height, fps, backend
            if cap:
                cap.release()
            return 640, 480, 30, "MSMF"
    
    async def scan_available_cameras_async(self, max_index: int) -> List[CameraInfo]:
        """
        Scan for available cameras and return unique identifiers with stable logical IDs.
        
        Uses deterministic enumeration + fingerprinting to assign logical IDs (cam_0, cam_1, ...)
        that remain stable during runtime and across app reloads.
        
        Args:
            max_index: Maximum camera index to scan (0 to max_index)
            
        Returns:
            List of CameraInfo objects with unique identifiers, sorted by logical ID
        """
        def _scan_sync() -> List[tuple]:
            """Synchronously enumerate all cameras with their properties."""
            import warnings
            cameras = []
            
            for idx in range(max_index + 1):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    cap = cv2.VideoCapture(idx, cv2.CAP_MSMF)
                    if not cap or not cap.isOpened():
                        if cap:
                            cap.release()
                        continue
                    
                    ret, frame = cap.read()
                    if not ret:
                        cap.release()
                        continue
                    
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
                    backend = cap.getBackendName() or "MSMF"
                    cap.release()
                    
                    cameras.append((idx, width, height, fps, backend))
            
            return cameras
        
        # Step 1: Enumerate all available cameras
        enumerated = await asyncio.to_thread(_scan_sync)
        if not enumerated:
            return []
        
        # Step 2: Load existing mapping
        old_mapping = self._load_mapping()
        
        # Step 3: Create fingerprint -> camera data mapping
        current_by_fingerprint: Dict[str, tuple] = {}
        for idx, width, height, fps, backend in enumerated:
            fingerprint = self._create_fingerprint(idx, width, height, fps, backend)
            current_by_fingerprint[fingerprint] = (idx, width, height, fps, backend)
        
        # Step 4: Reconcile with existing mapping
        result: Dict[str, tuple] = {}  # logical_id -> (index, width, height, fps, backend)
        used_fingerprints = set()
        
        # Match existing logical IDs by fingerprint
        for logical_id, old_data in old_mapping.items():
            old_fingerprint = old_data.get('fingerprint')
            if old_fingerprint and old_fingerprint in current_by_fingerprint:
                result[logical_id] = current_by_fingerprint[old_fingerprint]
                used_fingerprints.add(old_fingerprint)
                self.logger.debug(f"Matched {logical_id} to camera at index {result[logical_id][0]}")
        
        # Step 5: Assign new logical IDs to unmatched cameras (sorted by index for determinism)
        unmatched = [
            (fingerprint, data) for fingerprint, data in current_by_fingerprint.items()
            if fingerprint not in used_fingerprints
        ]
        unmatched.sort(key=lambda x: x[1][0])  # Sort by index
        
        next_id = len(result)
        for fingerprint, data in unmatched:
            logical_id = f"cam_{next_id}"
            result[logical_id] = data
            next_id += 1
            self.logger.debug(f"Assigned new {logical_id} to camera at index {data[0]}")
        
        # Step 6: Create CameraInfo objects and save mapping
        final_cameras: List[CameraInfo] = []
        new_mapping: Dict[str, Dict] = {}
        
        for logical_id, (index, width, height, fps, backend) in sorted(
            result.items(), key=lambda x: int(x[0].split('_')[1]) if '_' in x[0] else 999
        ):
            fingerprint = self._create_fingerprint(index, width, height, fps, backend)
            
            cam_info = CameraInfo(
                unique_id=logical_id,  # Use logical_id as unique_id for stability
                index=index,
                name=f"Camera {logical_id.split('_')[1] if '_' in logical_id else '?'}"
            )
            final_cameras.append(cam_info)
            
            new_mapping[logical_id] = {
                'fingerprint': fingerprint,
                'index': index,
            }
            
            self._index_to_logical[index] = logical_id
        
        self._camera_mapping = {cam.unique_id: cam for cam in final_cameras}
        self._save_mapping(new_mapping)
        
        return final_cameras
    
    async def get_camera_by_unique_id_async(self, unique_id: str) -> Optional[CameraInfo]:
        """
        Get camera information by unique identifier (logical ID).
        
        Returns camera from mapping if available. The mapping is updated
        when scan_available_cameras_async is called.
        """
        # Return from mapping if available
        return self._camera_mapping.get(unique_id)

