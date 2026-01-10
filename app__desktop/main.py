# app__desktop/main.py
"""Desktop GUI application entry point."""
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from common.logger import configure_logging, get_logger
from app__desktop.di_container import bootstrap_container
from app__desktop.window import MainWindow


def main() -> int:
    """Main entry point for desktop application."""
    # Configure logging
    configure_logging(log_level="INFO")
    logger = get_logger(__name__)
    
    try:
        # Get project root and config path
        project_root = Path(__file__).resolve().parent.parent
        config_path = project_root / "app__desktop" / "config.yml"
        
        # Bootstrap DI container
        container = bootstrap_container(config_path)
        
        # Get dependencies from container
        camera_service = container.camera_service()
        camera_capture_service = container.camera_capture_service()
        app_config = container.app_config()
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName(app_config.ui.window.title)
        
        # Create and show main window with injected dependencies
        window = MainWindow(
            camera_service=camera_service,
            camera_capture_service=camera_capture_service,
            app_config=app_config,
        )
        window.show()
        
        return app.exec()
        
    except Exception as e:
        logger.error(f"Error starting desktop application: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

