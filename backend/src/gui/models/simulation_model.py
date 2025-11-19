"""
Table models for displaying Monte Carlo simulation results.

Implements Qt Model/View architecture for efficient rendering of simulation data.
"""

from typing import List, Dict, Any

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QColor

from ...data.models import Team
from ...simulation.monte_carlo import SimulationResult, TeamSimulationStats


class PlayoffProbabilityModel(QAbstractTableModel):
    """Table model for displaying playoff probabilities for all teams."""

    def __init__(self, result: SimulationResult, teams_dict: Dict[str, Team]):
        """
        Initialize playoff probability model.

        Args:
            result: SimulationResult containing team statistics
            teams_dict: Dictionary mapping team_id to Team object
        """
        super().__init__()
        self.result = result
        self.teams_dict = teams_dict

        # Build sorted list of (team_id, stats) tuples
        self._data: List[tuple[str, TeamSimulationStats]] = []
        self._build_data()

    def _build_data(self):
        """Build and sort data list."""
        self._data = []

        for team_id, stats in self.result.team_stats.items():
            self._data.append((team_id, stats))

        # Sort by playoff probability descending
        self._data.sort(key=lambda x: x[1].playoff_probability, reverse=True)

    def rowCount(self, parent=QModelIndex()) -> int:
        """Return number of rows."""
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        """Return number of columns."""
        if parent.isValid():
            return 0
        return 5  # Team, Avg Wins, Playoff %, Division Win %, #1 Seed %

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        """Return data for given index and role."""
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self._data):
            return None

        team_id, stats = self._data[row]
        team = self.teams_dict.get(team_id)

        if role == Qt.DisplayRole:
            if col == 0:  # Team
                return team.display_name if team else team_id
            elif col == 1:  # Avg Wins
                return f"{stats.average_wins:.1f}"
            elif col == 2:  # Playoff %
                return f"{stats.playoff_probability * 100:.1f}%"
            elif col == 3:  # Division Win %
                return f"{stats.division_win_probability * 100:.1f}%"
            elif col == 4:  # #1 Seed %
                return f"{stats.first_seed_probability * 100:.1f}%"

        elif role == Qt.TextAlignmentRole:
            if col == 0:  # Team name - left aligned
                return Qt.AlignLeft | Qt.AlignVCenter
            else:  # Numbers - right aligned
                return Qt.AlignRight | Qt.AlignVCenter

        elif role == Qt.BackgroundRole:
            # Color-code rows based on playoff probability
            prob = stats.playoff_probability

            if prob >= 0.8:  # >= 80% - high probability (green tint)
                return QColor(27, 94, 32, 40)  # Semi-transparent dark green
            elif prob >= 0.3:  # 30-80% - medium probability (yellow tint)
                return QColor(245, 127, 23, 30)  # Semi-transparent orange
            else:  # < 30% - low probability (red tint)
                return QColor(183, 28, 28, 30)  # Semi-transparent red

        elif role == Qt.UserRole:
            # Store raw data for sorting
            if col == 0:
                return team.display_name if team else team_id
            elif col == 1:
                return stats.average_wins
            elif col == 2:
                return stats.playoff_probability
            elif col == 3:
                return stats.division_win_probability
            elif col == 4:
                return stats.first_seed_probability

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole
    ) -> Any:
        """Return header data."""
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            headers = ["Team", "Avg Wins", "Playoff %", "Division Win %", "#1 Seed %"]
            if section < len(headers):
                return headers[section]

        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        """Sort table by column."""
        self.layoutAboutToBeChanged.emit()

        reverse = order == Qt.DescendingOrder

        if column == 0:  # Team name
            self._data.sort(
                key=lambda x: self.teams_dict.get(x[0]).display_name
                if self.teams_dict.get(x[0])
                else x[0],
                reverse=reverse,
            )
        elif column == 1:  # Avg Wins
            self._data.sort(key=lambda x: x[1].average_wins, reverse=reverse)
        elif column == 2:  # Playoff %
            self._data.sort(key=lambda x: x[1].playoff_probability, reverse=reverse)
        elif column == 3:  # Division Win %
            self._data.sort(key=lambda x: x[1].division_win_probability, reverse=reverse)
        elif column == 4:  # #1 Seed %
            self._data.sort(key=lambda x: x[1].first_seed_probability, reverse=reverse)

        self.layoutChanged.emit()

    def update_data(self, result: SimulationResult):
        """
        Update model with new simulation results.

        Args:
            result: New SimulationResult to display
        """
        self.beginResetModel()
        self.result = result
        self._build_data()
        self.endResetModel()

    def get_team_id_at_row(self, row: int) -> str:
        """
        Get team_id for given row.

        Args:
            row: Row index

        Returns:
            Team ID string
        """
        if 0 <= row < len(self._data):
            return self._data[row][0]
        return ""
