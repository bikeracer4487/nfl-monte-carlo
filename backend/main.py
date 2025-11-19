#!/usr/bin/env python3
"""
Main entry point for NFL Monte Carlo simulation GUI application.

Launches the PySide6 GUI for exploring NFL playoff probabilities.
"""

import sys
import os
import platform
import ctypes
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from src.gui.main_window import MainWindow
from src.gui.font_loader import load_custom_fonts
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Launch the GUI application."""
    # Load environment variables
    load_dotenv()

    logger.info("=" * 60)
    logger.info("NFL Monte Carlo Simulation - GUI Application")
    logger.info("=" * 60)

    # Windows Taskbar Icon Fix
    # Ensures the app icon shows separately from Python in the taskbar
    if platform.system() == "Windows":
        myappid = "nflmontecarlo.simulator.gui.1.0"  # Arbitrary unique ID
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            logger.warning(f"Failed to set AppUserModelID: {e}")

    # Create Qt application
    app = QApplication(sys.argv)

    # Set Application Icon
    # In PyInstaller bundle, icon is in sys._MEIPASS
    # In dev environment, icon is in repo root (parent of backend)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        icon_path = Path(sys._MEIPASS) / "final_icon.png"
    else:
        icon_path = Path(__file__).parent.parent / "final_icon.png"

    if icon_path.exists():
        logger.info(f"Loading application icon from: {icon_path}")
        app.setWindowIcon(QIcon(str(icon_path)))
    else:
        logger.warning(f"Application icon not found at: {icon_path}")

    # Load custom fonts (Inter)
    load_custom_fonts()
    app.setApplicationName("NFL Monte Carlo Simulation")
    app.setOrganizationName("NFL Monte Carlo")

    # Create and show main window
    try:
        window = MainWindow()
        window.show()

        logger.info("Application started successfully")

        # Start event loop
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
