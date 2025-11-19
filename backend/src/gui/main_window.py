"""
Main application window for NFL Monte Carlo simulation.

Provides the top-level GUI with menu bar, status bar, and tabbed views.
"""

from datetime import datetime
from typing import List, Dict

from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QStatusBar,
    QMenuBar,
    QMenu,
    QMessageBox,
    QApplication,
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QAction

from ..data.models import Team, Game
from ..data.espn_api import ESPNAPIClient, ESPNAPIError
from ..data.cache_manager import CacheManager
from ..data.schedule_loader import ScheduleLoader
from ..utils.config import Config
from ..utils.logger import setup_logger

from .standings_view import StandingsView
from .simulation_view import SimulationView
from .schedule_view import ScheduleView

logger = setup_logger(__name__)


class DataRefreshWorker(QObject):
    """Worker for refreshing data in background thread."""

    finished = Signal(list)  # Emits updated games list
    progress = Signal(str)  # Emits status messages
    error = Signal(str)  # Emits error messages

    def __init__(self, espn_client: ESPNAPIClient, cache_manager: CacheManager, season: int):
        super().__init__()
        self.espn_client = espn_client
        self.cache_manager = cache_manager
        self.season = season

    def run(self):
        """Run data refresh in background."""
        try:
            self.progress.emit("Fetching latest game results from ESPN...")
            games = self.espn_client.fetch_schedule(self.season)

            self.progress.emit("Updating cache...")
            self.cache_manager.save_schedule(games, self.season)

            self.progress.emit("Refresh complete")
            self.finished.emit(games)
        except ESPNAPIError as e:
            self.error.emit(f"API Error: {str(e)}")
        except Exception as e:
            self.error.emit(f"Unexpected error: {str(e)}")


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Setup logger
        self.logger = setup_logger(__name__)

        # Load configuration
        self.config = Config.load()

        # Initialize data layer
        self.logger.info("Initializing data layer...")
        self.espn_client = ESPNAPIClient(
            self.config.ESPN_API_BASE_URL, self.config.ESPN_CORE_API_BASE_URL
        )
        self.cache_manager = CacheManager(self.config.CACHE_DIRECTORY)
        self.schedule_loader = ScheduleLoader(self.espn_client, self.cache_manager)

        # Load data
        self.logger.info("Loading teams and schedule...")
        self.teams: List[Team] = []
        self.games: List[Game] = []
        self.teams_dict: Dict[str, Team] = {}

        try:
            self.teams = self.schedule_loader.load_teams(force_refresh=False)
            self.teams_dict = {team.id: team for team in self.teams}
            self.games = self.schedule_loader.load_schedule(2025, force_refresh=False)
            self.logger.info(
                f"Loaded {len(self.teams)} teams and {len(self.games)} games"
            )
        except Exception as e:
            self.logger.error(f"Failed to load data: {e}")
            QMessageBox.critical(
                self,
                "Data Loading Error",
                f"Failed to load teams and schedule:\n\n{str(e)}\n\nThe application may not function correctly.",
            )

        # Setup UI
        self.setup_ui()

        # Apply modern dark theme
        from .styles import DARK_THEME

        self.setStyleSheet(DARK_THEME)

        self.logger.info("Main window initialized successfully")

    def setup_ui(self):
        """Setup the user interface."""
        # Window properties
        self.setWindowTitle("NFL Monte Carlo Simulation")
        self.resize(1280, 720)  # Widescreen format

        # Create tab widget for different views
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)  # Cleaner appearance

        # Create views
        self.standings_view = StandingsView(self.teams, self.games)
        self.simulation_view = SimulationView(self.teams, self.games)
        self.schedule_view = ScheduleView()

        # Add views to tabs
        self.tabs.addTab(self.standings_view, "Standings")
        self.tabs.addTab(self.simulation_view, "Simulation")
        self.tabs.addTab(self.schedule_view, "Schedule")

        # Set as central widget
        self.setCentralWidget(self.tabs)

        # Create menu bar
        self.create_menu_bar()

        # Create status bar
        self.create_status_bar()

    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        standings_action = QAction("&Standings", self)
        standings_action.setStatusTip("Show standings view")
        standings_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        view_menu.addAction(standings_action)

        simulation_action = QAction("S&imulation", self)
        simulation_action.setStatusTip("Show simulation view")
        simulation_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        view_menu.addAction(simulation_action)

        schedule_action = QAction("Sche&dule", self)
        schedule_action.setStatusTip("Show schedule view")
        schedule_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        view_menu.addAction(schedule_action)

        # Data menu
        data_menu = menubar.addMenu("&Data")

        refresh_action = QAction("&Refresh Results", self)
        refresh_action.setShortcut("Ctrl+R")
        refresh_action.setStatusTip("Refresh game results from ESPN")
        refresh_action.triggered.connect(self.refresh_data)
        data_menu.addAction(refresh_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_status_bar(self):
        """Create the application status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # Show initial status
        self.update_status_message("Ready")

        # Show data timestamps if available
        self.update_timestamp_status()

    def update_status_message(self, message: str):
        """Update the status bar message."""
        self.statusbar.showMessage(message)

    def update_timestamp_status(self):
        """Update status bar with last updated timestamps."""
        # Get cache info
        cache_info = self.cache_manager.get_cache_info()

        # Cache info returns dict with keys: "schedule", "results", "teams"
        # Each value is a dict with "exists", "age_seconds", "last_modified"
        schedule_info = cache_info.get("schedule")

        if schedule_info and schedule_info.get("exists") and schedule_info.get("last_modified"):
            timestamp = schedule_info["last_modified"]
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            self.statusbar.showMessage(f"Last updated: {formatted_time}", 5000)
        else:
            self.statusbar.showMessage("No cached data", 5000)

    def refresh_data(self):
        """Refresh game results from ESPN in background thread."""
        self.logger.info("Starting data refresh...")

        # Disable refresh action during refresh
        self.findChild(QAction, "Refresh Results")

        # Create worker and thread
        self.worker = DataRefreshWorker(
            self.espn_client, self.cache_manager, season=2025
        )
        self.thread = QThread()

        # Move worker to thread
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_refresh_complete)
        self.worker.progress.connect(self.update_status_message)
        self.worker.error.connect(self.on_refresh_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Start thread
        self.update_status_message("Refreshing data...")
        self.thread.start()

    def on_refresh_complete(self, games: List[Game]):
        """Handle completion of data refresh."""
        self.logger.info(f"Data refresh complete: {len(games)} games")
        self.games = games

        # Update views with new data
        self.standings_view.update_data(self.games)
        self.simulation_view.update_data(self.games)

        # Update status
        self.update_status_message("Data refresh complete")
        self.update_timestamp_status()

        # Show completion message
        QMessageBox.information(
            self,
            "Refresh Complete",
            f"Successfully refreshed {len(games)} games from ESPN.",
        )

    def on_refresh_error(self, error_message: str):
        """Handle error during data refresh."""
        self.logger.error(f"Data refresh error: {error_message}")
        self.update_status_message("Refresh failed")

        QMessageBox.warning(
            self, "Refresh Error", f"Failed to refresh data:\n\n{error_message}"
        )

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About NFL Monte Carlo Simulation",
            "<h3>NFL Monte Carlo Simulation</h3>"
            "<p>A desktop application for estimating NFL playoff probabilities "
            "using Monte Carlo simulations with unbiased 50/50 coin flips.</p>"
            "<p><b>Phase 4:</b> GUI Foundation</p>"
            "<p>Built with PySide6 and Python</p>",
        )

    def closeEvent(self, event):
        """Handle window close event."""
        self.logger.info("Application closing")
        event.accept()
