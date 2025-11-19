"""
Qt Style Sheets (QSS) for NFL Monte Carlo GUI.

Modern dark theme with sports analytics aesthetic.
Color scheme: Hybrid approach with modern blue (#2196F3) primary
and NFL official colors (#013369, #D50A0A) as accents.
"""

from .font_loader import get_font_family, get_numeric_font_family


# Color Palette
class Colors:
    """Modern dark theme color palette."""

    # Backgrounds
    BG_PRIMARY = "#121212"  # Main background
    BG_SECONDARY = "#1E1E1E"  # Card backgrounds
    BG_TERTIARY = "#252525"  # Elevated surfaces
    BG_HOVER = "#2A2A2A"  # Hover states
    BG_PRESSED = "#1A1A1A"  # Pressed states

    # Accents
    ACCENT_PRIMARY = "#2196F3"  # Modern blue (primary actions)
    ACCENT_SECONDARY = "#FF6B35"  # Energetic orange
    ACCENT_NFL_BLUE = "#013369"  # NFL official dark blue
    ACCENT_NFL_RED = "#D50A0A"  # NFL official red

    # Semantic Colors
    SUCCESS = "#4CAF50"  # Green (winning, positive)
    WARNING = "#FFC107"  # Amber (close games, caution)
    ERROR = "#F44336"  # Red (losing, negative)
    INFO = "#29B6F6"  # Light blue (informational)

    # Text
    TEXT_PRIMARY = "#FFFFFF"  # Primary text
    TEXT_SECONDARY = "#B0B0B0"  # Secondary text
    TEXT_DISABLED = "#6B6B6B"  # Disabled text
    TEXT_HINT = "#808080"  # Hint text

    # Borders & Dividers
    BORDER_DEFAULT = "#2C2C2C"  # Subtle borders
    BORDER_HOVER = "#404040"  # Hover borders
    BORDER_FOCUS = ACCENT_PRIMARY  # Focus borders
    DIVIDER = "#333333"  # Section dividers

    # Table Specific
    TABLE_HEADER_BG = "#1A1A1A"  # Table headers
    TABLE_ROW_ALT = "#1C1C1C"  # Alternating rows
    TABLE_HOVER = "#242424"  # Row hover
    TABLE_SELECTED = "#0D47A1"  # Selected row (darker blue)
    TABLE_GRID = "#2C2C2C"  # Grid lines


def get_dark_theme() -> str:
    """
    Get the complete dark theme stylesheet.

    Returns:
        Complete QSS stylesheet string
    """
    font_family = get_font_family()
    numeric_font = get_numeric_font_family()

    return f"""
/* =============================================================================
   GLOBAL STYLES
   ============================================================================= */

* {{
    font-family: {font_family};
    font-size: 14px;
}}

/* =============================================================================
   MAIN WINDOW
   ============================================================================= */

QMainWindow {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {Colors.BG_PRIMARY},
        stop:1 #0A0A0A
    );
    color: {Colors.TEXT_PRIMARY};
}}

/* =============================================================================
   TABLE VIEWS
   ============================================================================= */

QTableView {{
    background-color: {Colors.BG_SECONDARY};
    alternate-background-color: {Colors.TABLE_ROW_ALT};
    gridline-color: {Colors.TABLE_GRID};
    selection-background-color: {Colors.TABLE_SELECTED};
    selection-color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 8px;
    color: {Colors.TEXT_PRIMARY};
    font-size: 14px;
}}

QTableView::item {{
    padding: 10px 14px;
    border: none;
}}

QTableView::item:hover {{
    background-color: {Colors.TABLE_HOVER};
}}

QTableView::item:selected {{
    background-color: {Colors.TABLE_SELECTED};
    color: {Colors.TEXT_PRIMARY};
}}

/* Numeric cells - use tabular figures font */
QTableView::item {{
    font-family: {numeric_font};
}}

/* Table Headers */
QHeaderView::section {{
    background-color: {Colors.TABLE_HEADER_BG};
    color: {Colors.TEXT_PRIMARY};
    padding: 12px 14px;
    border: none;
    border-bottom: 2px solid {Colors.ACCENT_PRIMARY};
    border-right: 1px solid {Colors.BORDER_DEFAULT};
    font-weight: 600;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QHeaderView::section:last {{
    border-right: none;
}}

QHeaderView::section:hover {{
    background-color: {Colors.BG_HOVER};
}}

QHeaderView::section:pressed {{
    background-color: {Colors.BG_PRESSED};
}}

/* Vertical Header (Row Numbers) */
QHeaderView::section:vertical {{
    border-bottom: 1px solid {Colors.BORDER_DEFAULT};
    border-right: 2px solid {Colors.ACCENT_PRIMARY};
}}

/* =============================================================================
   TAB WIDGET
   ============================================================================= */

QTabWidget::pane {{
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 8px;
    background-color: {Colors.BG_SECONDARY};
    top: -1px;
}}

QTabBar {{
    background-color: transparent;
}}

QTabBar::tab {{
    background-color: {Colors.BG_SECONDARY};
    color: {Colors.TEXT_SECONDARY};
    border: none;
    border-bottom: 3px solid transparent;
    padding: 12px 28px;
    margin-right: 4px;
    font-weight: 500;
    font-size: 15px;
    min-width: 100px;
}}

QTabBar::tab:selected {{
    color: {Colors.ACCENT_PRIMARY};
    border-bottom: 3px solid {Colors.ACCENT_PRIMARY};
    background-color: {Colors.BG_PRIMARY};
    font-weight: 600;
}}

QTabBar::tab:hover:!selected {{
    background-color: {Colors.BG_HOVER};
    color: {Colors.TEXT_PRIMARY};
}}

QTabBar::tab:pressed {{
    background-color: {Colors.BG_PRESSED};
}}

/* =============================================================================
   GROUP BOXES (DIVISION CARDS)
   ============================================================================= */

QGroupBox {{
    background-color: {Colors.BG_SECONDARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 12px;
    margin-top: 16px;
    padding: 20px 16px 16px 16px;
    font-weight: 600;
    font-size: 16px;
    color: {Colors.TEXT_PRIMARY};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 16px;
    margin-left: 8px;
    background-color: {Colors.BG_TERTIARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 6px;
    color: {Colors.ACCENT_PRIMARY};
    font-weight: 700;
    font-size: 15px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

QGroupBox:hover {{
    border: 1px solid {Colors.BORDER_HOVER};
}}

/* =============================================================================
   COMBO BOXES (WEEK SELECTOR)
   ============================================================================= */

QComboBox {{
    background-color: {Colors.BG_SECONDARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 8px;
    padding: 10px 16px;
    color: {Colors.TEXT_PRIMARY};
    font-size: 14px;
    font-weight: 500;
    min-width: 150px;
}}

QComboBox:hover {{
    border: 1px solid {Colors.ACCENT_PRIMARY};
    background-color: {Colors.BG_HOVER};
}}

QComboBox:focus {{
    border: 2px solid {Colors.ACCENT_PRIMARY};
}}

QComboBox:on {{
    border: 2px solid {Colors.ACCENT_PRIMARY};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 30px;
    border-left: 1px solid {Colors.BORDER_DEFAULT};
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 7px solid {Colors.TEXT_SECONDARY};
    margin-right: 8px;
}}

QComboBox::down-arrow:hover {{
    border-top: 7px solid {Colors.ACCENT_PRIMARY};
}}

QComboBox QAbstractItemView {{
    background-color: {Colors.BG_SECONDARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 8px;
    selection-background-color: {Colors.ACCENT_PRIMARY};
    selection-color: {Colors.TEXT_PRIMARY};
    color: {Colors.TEXT_PRIMARY};
    padding: 4px;
}}

QComboBox QAbstractItemView::item {{
    padding: 8px 12px;
    border-radius: 4px;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {Colors.BG_HOVER};
}}

/* =============================================================================
   RADIO BUTTONS
   ============================================================================= */

QRadioButton {{
    spacing: 8px;
    color: {Colors.TEXT_PRIMARY};
    font-size: 14px;
    font-weight: 500;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
}}

QRadioButton::indicator:unchecked {{
    border: 2px solid {Colors.BORDER_HOVER};
    background-color: {Colors.BG_SECONDARY};
}}

QRadioButton::indicator:unchecked:hover {{
    border: 2px solid {Colors.ACCENT_PRIMARY};
    background-color: {Colors.BG_HOVER};
}}

QRadioButton::indicator:checked {{
    border: 2px solid {Colors.ACCENT_PRIMARY};
    background-color: {Colors.ACCENT_PRIMARY};
    /* Add inner circle */
    background: radial-gradient(
        circle,
        {Colors.TEXT_PRIMARY} 0%,
        {Colors.TEXT_PRIMARY} 35%,
        {Colors.ACCENT_PRIMARY} 35%,
        {Colors.ACCENT_PRIMARY} 100%
    );
}}

QRadioButton::indicator:checked:hover {{
    border: 2px solid #42A5F5;
}}

QRadioButton:disabled {{
    color: {Colors.TEXT_DISABLED};
}}

/* =============================================================================
   LABELS
   ============================================================================= */

QLabel {{
    color: {Colors.TEXT_PRIMARY};
    background-color: transparent;
    font-size: 14px;
}}

QLabel[heading="true"] {{
    font-size: 18px;
    font-weight: 700;
    color: {Colors.ACCENT_PRIMARY};
}}

QLabel[subheading="true"] {{
    font-size: 16px;
    font-weight: 600;
    color: {Colors.TEXT_SECONDARY};
}}

/* =============================================================================
   SCROLL AREAS
   ============================================================================= */

QScrollArea {{
    border: none;
    background-color: transparent;
}}

/* =============================================================================
   SCROLL BARS
   ============================================================================= */

/* Vertical Scrollbar */
QScrollBar:vertical {{
    border: none;
    background-color: {Colors.BG_PRIMARY};
    width: 14px;
    margin: 0px;
    border-radius: 7px;
}}

QScrollBar::handle:vertical {{
    background-color: {Colors.BG_TERTIARY};
    min-height: 30px;
    border-radius: 7px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {Colors.BORDER_HOVER};
}}

QScrollBar::handle:vertical:pressed {{
    background-color: {Colors.ACCENT_PRIMARY};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}

/* Horizontal Scrollbar */
QScrollBar:horizontal {{
    border: none;
    background-color: {Colors.BG_PRIMARY};
    height: 14px;
    margin: 0px;
    border-radius: 7px;
}}

QScrollBar::handle:horizontal {{
    background-color: {Colors.BG_TERTIARY};
    min-width: 30px;
    border-radius: 7px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {Colors.BORDER_HOVER};
}}

QScrollBar::handle:horizontal:pressed {{
    background-color: {Colors.ACCENT_PRIMARY};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: none;
}}

/* =============================================================================
   STATUS BAR
   ============================================================================= */

QStatusBar {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {Colors.TABLE_HEADER_BG},
        stop:1 {Colors.BG_PRIMARY}
    );
    color: {Colors.TEXT_SECONDARY};
    border-top: 1px solid {Colors.BORDER_DEFAULT};
    font-size: 12px;
    padding: 6px 12px;
}}

QStatusBar::item {{
    border: none;
}}

QStatusBar QLabel {{
    color: {Colors.TEXT_SECONDARY};
    font-size: 12px;
}}

/* =============================================================================
   MENU BAR
   ============================================================================= */

QMenuBar {{
    background-color: {Colors.BG_SECONDARY};
    color: {Colors.TEXT_PRIMARY};
    border-bottom: 1px solid {Colors.BORDER_DEFAULT};
    padding: 4px 8px;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 6px 16px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
}}

QMenuBar::item:selected {{
    background-color: {Colors.ACCENT_PRIMARY};
    color: {Colors.TEXT_PRIMARY};
}}

QMenuBar::item:pressed {{
    background-color: #1976D2;
}}

/* =============================================================================
   MENU (DROPDOWN)
   ============================================================================= */

QMenu {{
    background-color: {Colors.BG_SECONDARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 8px;
    padding: 8px;
    color: {Colors.TEXT_PRIMARY};
}}

QMenu::item {{
    padding: 8px 32px 8px 24px;
    border-radius: 4px;
    font-size: 14px;
}}

QMenu::item:selected {{
    background-color: {Colors.ACCENT_PRIMARY};
    color: {Colors.TEXT_PRIMARY};
}}

QMenu::item:disabled {{
    color: {Colors.TEXT_DISABLED};
}}

QMenu::separator {{
    height: 1px;
    background-color: {Colors.BORDER_DEFAULT};
    margin: 6px 12px;
}}

QMenu::indicator {{
    width: 16px;
    height: 16px;
    margin-left: 6px;
}}

/* =============================================================================
   PUSH BUTTONS
   ============================================================================= */

QPushButton {{
    background-color: {Colors.ACCENT_PRIMARY};
    color: {Colors.TEXT_PRIMARY};
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: 600;
    min-width: 100px;
}}

QPushButton:hover {{
    background-color: #42A5F5;
}}

QPushButton:pressed {{
    background-color: #1976D2;
}}

QPushButton:disabled {{
    background-color: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_DISABLED};
}}

QPushButton[secondary="true"] {{
    background-color: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
}}

QPushButton[secondary="true"]:hover {{
    background-color: {Colors.BG_HOVER};
    border: 1px solid {Colors.ACCENT_PRIMARY};
}}

/* =============================================================================
   TOOL TIPS
   ============================================================================= */

QToolTip {{
    background-color: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}}

/* =============================================================================
   WIDGETS (GENERAL)
   ============================================================================= */

QWidget {{
    color: {Colors.TEXT_PRIMARY};
    selection-background-color: {Colors.ACCENT_PRIMARY};
    selection-color: {Colors.TEXT_PRIMARY};
}}

QWidget:focus {{
    outline: none;
}}

/* =============================================================================
   TEXT EDIT / LINE EDIT
   ============================================================================= */

QTextEdit, QLineEdit {{
    background-color: {Colors.BG_SECONDARY};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
}}

QTextEdit:hover, QLineEdit:hover {{
    border: 1px solid {Colors.ACCENT_PRIMARY};
}}

QTextEdit:focus, QLineEdit:focus {{
    border: 2px solid {Colors.ACCENT_PRIMARY};
}}

/* =============================================================================
   SPLITTER
   ============================================================================= */

QSplitter::handle {{
    background-color: {Colors.BORDER_DEFAULT};
}}

QSplitter::handle:hover {{
    background-color: {Colors.ACCENT_PRIMARY};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}
"""


# For backward compatibility and easy access
DARK_THEME = get_dark_theme()


# Future: Light theme can be added here
def get_light_theme() -> str:
    """Get light theme stylesheet (not yet implemented)."""
    return ""


LIGHT_THEME = ""  # Placeholder for future implementation
