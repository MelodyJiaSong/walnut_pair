# app__batch/app_config.py
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml
from common.enums import WalnutSideEnum
from common.interfaces import (
    IAppConfig,
    DatabaseConfig,
    CameraConfig,
    AlgorithmConfig,
    BasicSimilarityConfig,
    AdvancedSimilarityConfig,
    FinalSimilarityConfig,
)
from common.path_utils import normalize_path





class AppConfig(IAppConfig):
    def __init__(
        self,
        image_root: str,
        database: dict,
        algorithm: dict,
        cameras: Optional[dict],
    ) -> None:
        # Normalize path based on current environment (WSL vs Windows)
        self._image_root: str = normalize_path(image_root)
        self._database: DatabaseConfig = DatabaseConfig(**database)
        
        # Validate algorithm configuration fields explicitly
        if "comparison_mode" not in algorithm:
            raise ValueError("Algorithm 'comparison_mode' is required in config.yml")
        if "basic" not in algorithm:
            raise ValueError("Algorithm 'basic' configuration is required in config.yml")
        if "advanced" not in algorithm:
            raise ValueError("Algorithm 'advanced' configuration is required in config.yml")
        if "final" not in algorithm:
            raise ValueError("Algorithm 'final' configuration is required in config.yml")
        
        comparison_mode: str = algorithm["comparison_mode"]
        basic_config = algorithm["basic"]
        advanced_config = algorithm["advanced"]
        final_config = algorithm["final"]
        
        self._algorithm: AlgorithmConfig = AlgorithmConfig(
            comparison_mode=comparison_mode,
            basic=BasicSimilarityConfig(**basic_config),
            advanced=AdvancedSimilarityConfig(**advanced_config),
            final=FinalSimilarityConfig(**final_config),
        )
        
        # Load camera configurations
        self._cameras: Dict[WalnutSideEnum, CameraConfig] = {}
        if cameras:
            side_mapping = {
                "FRONT": WalnutSideEnum.FRONT,
                "BACK": WalnutSideEnum.BACK,
                "LEFT": WalnutSideEnum.LEFT,
                "RIGHT": WalnutSideEnum.RIGHT,
                "TOP": WalnutSideEnum.TOP,
                "DOWN": WalnutSideEnum.DOWN,
            }
            for side_name, camera_data in cameras.items():
                side_enum = side_mapping.get(side_name.upper())
                if side_enum:
                    self._cameras[side_enum] = CameraConfig(**camera_data)

    @property
    def image_root(self) -> str:
        return self._image_root

    @property
    def database(self) -> DatabaseConfig:
        return self._database

    @property
    def algorithm(self) -> AlgorithmConfig:
        return self._algorithm

    @property
    def cameras(self) -> Dict[WalnutSideEnum, CameraConfig]:
        """Get camera configurations by side."""
        return self._cameras

    def get_camera_config(self, side: WalnutSideEnum) -> Optional[CameraConfig]:
        """Get camera configuration for a specific side."""
        return self._cameras.get(side)

    @classmethod
    def load_from_yaml(cls, yaml_path: Path) -> "AppConfig":
        with open(yaml_path, "r") as f:
            cfg = yaml.safe_load(f)
        
        # Validate required fields explicitly
        if "image_root" not in cfg:
            raise ValueError("Configuration file must include 'image_root'")
        if "database" not in cfg:
            raise ValueError("Configuration file must include 'database'")
        if "algorithm" not in cfg:
            raise ValueError("Configuration file must include 'algorithm'")
        
        # Normalize image_root path
        cfg["image_root"] = normalize_path(cfg["image_root"])
        
        # Explicitly pass cameras (None if not present, since it's optional)
        cameras = cfg["cameras"] if "cameras" in cfg else None
        
        return cls(
            image_root=cfg["image_root"],
            database=cfg["database"],
            algorithm=cfg["algorithm"],
            cameras=cameras,
        )
