"""
Standings view for NFL teams.

Displays NFL standings with division/conference/league-wide views.
"""

from typing import List, Dict

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QRadioButton,
    QButtonGroup,
    QLabel,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QScrollArea,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ..data.models import Team, Game, Standing
from ..simulation.standings import (
    calculate_standings,
    get_division_standings,
    get_conference_standings,
)
from ..utils.logger import setup_logger

from .models.standings_model import StandingsTableModel
from .widgets.week_selector import WeekSelector

logger = setup_logger(__name__)


class StandingsView(QWidget):
    """View for displaying NFL standings."""

    VIEW_DIVISION = "division"
    VIEW_CONFERENCE = "conference"
    VIEW_LEAGUE = "league"

    def __init__(self, teams: List[Team], games: List[Game]):
        """
        Initialize standings view.

        Args:
            teams: List of all NFL teams
            games: List of all games
        """
        super().__init__()

        self.teams = teams
        self.teams_dict = {team.id: team for team in teams}
        self.games = games
        self.current_view = self.VIEW_DIVISION
        self.selected_week = -1  # -1 means current/all completed games

        self.setup_ui()
        self.update_standings()

    def setup_ui(self):
        """Setup the user interface."""
        main_layout = QVBoxLayout()

        # Top controls
        controls_layout = QHBoxLayout()

        # Week selector
        week_label = QLabel("Week:")
        self.week_selector = WeekSelector(current_week=-1)
        self.week_selector.weekChanged.connect(self.on_week_changed)

        controls_layout.addWidget(week_label)
        controls_layout.addWidget(self.week_selector)
        controls_layout.addSpacing(20)

        # View mode selector
        view_label = QLabel("View:")
        controls_layout.addWidget(view_label)

        self.view_group = QButtonGroup()

        self.division_radio = QRadioButton("Division")
        self.conference_radio = QRadioButton("Conference")
        self.league_radio = QRadioButton("League-wide")

        self.division_radio.setChecked(True)  # Default view

        self.view_group.addButton(self.division_radio)
        self.view_group.addButton(self.conference_radio)
        self.view_group.addButton(self.league_radio)

        self.division_radio.toggled.connect(
            lambda checked: self.on_view_changed(self.VIEW_DIVISION) if checked else None
        )
        self.conference_radio.toggled.connect(
            lambda checked: self.on_view_changed(self.VIEW_CONFERENCE)
            if checked
            else None
        )
        self.league_radio.toggled.connect(
            lambda checked: self.on_view_changed(self.VIEW_LEAGUE) if checked else None
        )

        controls_layout.addWidget(self.division_radio)
        controls_layout.addWidget(self.conference_radio)
        controls_layout.addWidget(self.league_radio)

        controls_layout.addStretch()

        main_layout.addLayout(controls_layout)

        # Standings display area (will be populated based on view mode)
        self.standings_container = QWidget()
        self.standings_layout = QVBoxLayout()
        self.standings_container.setLayout(self.standings_layout)

        # Wrap in scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Never show horizontal scrollbar
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # Show vertical when needed
        scroll_area.setWidget(self.standings_container)

        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def on_week_changed(self, week: int):
        """
        Handle week selection change.

        Args:
            week: Selected week (-1 for current, 1-18 for specific)
        """
        logger.info(f"Week changed to: {week}")
        self.selected_week = week
        self.update_standings()

    def on_view_changed(self, view: str):
        """
        Handle view mode change.

        Args:
            view: View mode (division, conference, or league)
        """
        logger.info(f"View changed to: {view}")
        self.current_view = view
        self.update_standings()

    def update_standings(self):
        """Update standings display based on current selections."""
        # Filter games by selected week
        if self.selected_week == -1:
            # Current week: use all completed games
            filtered_games = [g for g in self.games if g.is_completed]
        else:
            # Specific week: use games up to and including that week
            filtered_games = [
                g for g in self.games if g.week <= self.selected_week
            ]

        # Calculate standings
        standings_dict = calculate_standings(filtered_games, self.teams)

        # Clear current display
        self.clear_standings_display()

        # Display based on view mode
        if self.current_view == self.VIEW_DIVISION:
            self.display_division_view(standings_dict)
        elif self.current_view == self.VIEW_CONFERENCE:
            self.display_conference_view(standings_dict)
        else:  # VIEW_LEAGUE
            self.display_league_view(standings_dict)

    def clear_standings_display(self):
        """Clear the standings display area."""
        while self.standings_layout.count():
            item = self.standings_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def display_division_view(self, standings_dict: Dict[str, Standing]):
        """
        Display standings in division view (8 divisions stacked vertically).

        Args:
            standings_dict: Dictionary of standings by team_id
        """
        # Create vertical layout for stacking divisions
        divisions_layout = QVBoxLayout()
        divisions_layout.setSpacing(15)

        # Order divisions by conference (AFC first, then NFC)
        divisions = [
            ("AFC", "East"),
            ("AFC", "North"),
            ("AFC", "South"),
            ("AFC", "West"),
            ("NFC", "East"),
            ("NFC", "North"),
            ("NFC", "South"),
            ("NFC", "West"),
        ]

        for conf, div in divisions:
            # Get division standings
            div_standings = get_division_standings(standings_dict, self.teams, conf, div)

            # Create group box for this division
            group_box = QGroupBox(f"{conf} {div}")
            group_layout = QVBoxLayout()
            group_layout.setContentsMargins(10, 15, 10, 10)

            # Create table for this division
            table = self.create_standings_table(div_standings)

            # Set reasonable height for 4 teams + header
            table.setMaximumHeight(180)

            group_layout.addWidget(table)
            group_box.setLayout(group_layout)

            # Add shadow effect for card elevation
            self._add_card_shadow(group_box)

            divisions_layout.addWidget(group_box)

        # Add stretch at bottom to prevent last division from expanding
        divisions_layout.addStretch()

        self.standings_layout.addLayout(divisions_layout)

    def display_conference_view(self, standings_dict: Dict[str, Standing]):
        """
        Display standings in conference view (AFC and NFC stacked vertically).

        Args:
            standings_dict: Dictionary of standings by team_id
        """
        # Create vertical layout for stacking conferences
        conf_layout = QVBoxLayout()
        conf_layout.setSpacing(15)

        for conf in ["AFC", "NFC"]:
            # Get conference standings
            conf_standings = [
                s for s in standings_dict.values()
                if self.teams_dict[s.team_id].conference == conf
            ]
            conf_standings.sort(key=lambda s: s.win_percentage, reverse=True)

            # Create group box
            group_box = QGroupBox(conf)
            group_layout = QVBoxLayout()
            group_layout.setContentsMargins(10, 15, 10, 10)

            # Create table
            table = self.create_standings_table(conf_standings)
            table.setMaximumHeight(600)  # 16 teams + header

            group_layout.addWidget(table)
            group_box.setLayout(group_layout)

            # Add shadow effect for card elevation
            self._add_card_shadow(group_box)

            conf_layout.addWidget(group_box)

        self.standings_layout.addLayout(conf_layout)

    def display_league_view(self, standings_dict: Dict[str, Standing]):
        """
        Display standings in league-wide view (all 32 teams).

        Args:
            standings_dict: Dictionary of standings by team_id
        """
        # Get all standings sorted by win percentage
        all_standings = list(standings_dict.values())
        all_standings.sort(key=lambda s: s.win_percentage, reverse=True)

        # Create table
        table = self.create_standings_table(all_standings)
        table.setMinimumHeight(700)

        self.standings_layout.addWidget(table)

    def create_standings_table(self, standings: List[Standing]) -> QTableView:
        """
        Create a QTableView for standings data.

        Args:
            standings: List of Standing objects to display

        Returns:
            Configured QTableView
        """
        # Create model
        model = StandingsTableModel(standings, self.teams_dict)

        # Create view
        table = QTableView()
        table.setModel(model)

        # Configure table
        table.setSortingEnabled(True)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableView.SelectRows)
        table.setSelectionMode(QTableView.SingleSelection)

        # Resize columns
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

        # Hide vertical header (row numbers)
        table.verticalHeader().setVisible(False)

        return table

    def _add_card_shadow(self, widget: QWidget):
        """
        Add drop shadow effect to a widget for card elevation.

        Args:
            widget: Widget to add shadow to (typically QGroupBox)
        """
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)  # Shadow blur
        shadow.setXOffset(0)  # No horizontal offset
        shadow.setYOffset(3)  # Slight vertical offset for depth
        shadow.setColor(QColor(0, 0, 0, 100))  # Semi-transparent black
        widget.setGraphicsEffect(shadow)

    def update_data(self, games: List[Game]):
        """
        Update with new game data (called after refresh).

        Args:
            games: Updated list of games
        """
        self.games = games
        self.update_standings()
