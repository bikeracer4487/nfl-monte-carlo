"""
Font loader for custom typography.

Loads the Inter variable font family for use in the GUI.
"""

from pathlib import Path
from PySide6.QtGui import QFontDatabase
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


def load_custom_fonts() -> bool:
    """
    Load custom fonts into the Qt font database.

    Returns:
        True if fonts loaded successfully, False otherwise
    """
    fonts_dir = Path(__file__).parent / "fonts"

    # Inter variable font files
    font_files = [
        "InterVariable.ttf",
        "InterVariable-Italic.ttf",
    ]

    success_count = 0

    for font_file in font_files:
        font_path = fonts_dir / font_file

        if not font_path.exists():
            logger.warning(f"Font file not found: {font_path}")
            continue

        font_id = QFontDatabase.addApplicationFont(str(font_path))

        if font_id == -1:
            logger.error(f"Failed to load font: {font_file}")
        else:
            # Get the font family names that were loaded
            families = QFontDatabase.applicationFontFamilies(font_id)
            logger.info(f"Loaded font: {font_file} (families: {', '.join(families)})")
            success_count += 1

    if success_count > 0:
        logger.info(f"Successfully loaded {success_count}/{len(font_files)} custom fonts")
        return True
    else:
        logger.warning("No custom fonts loaded, will use system fonts as fallback")
        return False


def get_font_family() -> str:
    """
    Get the primary font family string for use in stylesheets.

    Returns:
        Font family CSS string with fallbacks
    """
    # Inter variable font with system font fallbacks
    return (
        "'Inter', "  # Custom Inter font if loaded
        "-apple-system, "  # macOS San Francisco
        "BlinkMacSystemFont, "  # macOS
        "'Segoe UI', "  # Windows
        "Roboto, "  # Android, Chrome OS
        "Oxygen, "  # KDE
        "Ubuntu, "  # Ubuntu
        "Cantarell, "  # GNOME
        "'Helvetica Neue', "  # macOS fallback
        "Arial, "  # Universal fallback
        "sans-serif"  # Generic fallback
    )


def get_numeric_font_family() -> str:
    """
    Get the numeric font family string for statistics and numbers.

    Returns:
        Font family CSS string optimized for numbers
    """
    # For numbers, we want monospace/tabular figures
    # Inter variable font supports tabular figures via CSS
    return (
        "'Inter', "  # Inter has tabular figures
        "'SF Mono', "  # macOS monospace
        "'Segoe UI', "  # Windows (has tabular nums)
        "Consolas, "  # Windows monospace fallback
        "'Courier New', "  # Universal monospace
        "monospace"  # Generic fallback
    )
