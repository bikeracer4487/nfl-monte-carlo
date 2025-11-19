#!/usr/bin/env python3
"""
Main entry point for NFL Monte Carlo simulation GUI application.

Launches the PySide6 GUI for exploring NFL playoff probabilities.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication

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

    # Create Qt application
    app = QApplication(sys.argv)

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
