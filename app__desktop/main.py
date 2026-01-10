# app__desktop/main.py
"""Desktop GUI application entry point."""
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from app__desktop.window import MainWindow


def main() -> int:
    """Main entry point for desktop application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Walnut Camera Preview")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

