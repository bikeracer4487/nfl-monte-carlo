"""
Qt model for NFL standings table.

Provides QAbstractTableModel for displaying standings in QTableView.
"""

from typing import List, Dict, Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QFont

from ...data.models import Standing, Team


class StandingsTableModel(QAbstractTableModel):
    """Table model for NFL standings."""

    # Column indices
    COL_TEAM = 0
    COL_WINS = 1
    COL_LOSSES = 2
    COL_TIES = 3
    COL_PCT = 4
    COL_DIV = 5
    COL_CONF = 6

    HEADERS = ["Team", "W", "L", "T", "PCT", "DIV", "CONF"]

    def __init__(self, standings: List[Standing], teams: Dict[str, Team]):
        """
        Initialize standings model.

        Args:
            standings: List of Standing objects to display
            teams: Dictionary mapping team_id to Team object
        """
        super().__init__()
        self._standings = standings
        self._teams = teams

    def rowCount(self, parent=QModelIndex()) -> int:
        """Return number of rows (teams)."""
        if parent.isValid():
            return 0
        return len(self._standings)

    def columnCount(self, parent=QModelIndex()) -> int:
        """Return number of columns."""
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """
        Return data for given index and role.

        Args:
            index: Model index (row, column)
            role: Data role (Display, TextAlignment, Font, etc.)

        Returns:
            Data for the cell, or None
        """
        if not index.isValid():
            return None

        if index.row() >= len(self._standings):
            return None

        standing = self._standings[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            return self._get_display_data(standing, col)

        elif role == Qt.TextAlignmentRole:
            # Center-align numeric columns
            if col in [self.COL_WINS, self.COL_LOSSES, self.COL_TIES]:
                return Qt.AlignCenter
            elif col == self.COL_PCT:
                return Qt.AlignCenter
            else:
                return Qt.AlignLeft | Qt.AlignVCenter

        elif role == Qt.FontRole:
            # Bold font for team names
            if col == self.COL_TEAM:
                font = QFont()
                font.setBold(True)
                return font

        return None

    def _get_display_data(self, standing: Standing, col: int) -> str:
        """
        Get display text for a cell.

        Args:
            standing: Standing object for this row
            col: Column index

        Returns:
            Display text
        """
        if col == self.COL_TEAM:
            # Get team abbreviation
            team = self._teams.get(standing.team_id)
            return team.abbreviation if team else standing.team_id

        elif col == self.COL_WINS:
            return str(standing.wins)

        elif col == self.COL_LOSSES:
            return str(standing.losses)

        elif col == self.COL_TIES:
            return str(standing.ties)

        elif col == self.COL_PCT:
            # Format as .XXX (e.g., .750)
            return f"{standing.win_percentage:.3f}"

        elif col == self.COL_DIV:
            # Division record (W-L or W-L-T)
            if standing.division_ties > 0:
                return f"{standing.division_wins}-{standing.division_losses}-{standing.division_ties}"
            else:
                return f"{standing.division_wins}-{standing.division_losses}"

        elif col == self.COL_CONF:
            # Conference record (W-L or W-L-T)
            if standing.conference_ties > 0:
                return f"{standing.conference_wins}-{standing.conference_losses}-{standing.conference_ties}"
            else:
                return f"{standing.conference_wins}-{standing.conference_losses}"

        return ""

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> Any:
        """
        Return header data for given section.

        Args:
            section: Column or row index
            orientation: Horizontal (column headers) or Vertical (row headers)
            role: Data role

        Returns:
            Header text or None
        """
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if section < len(self.HEADERS):
                return self.HEADERS[section]

        elif orientation == Qt.Vertical:
            # Row numbers (1-indexed)
            return str(section + 1)

        return None

    def update_standings(self, standings: List[Standing]):
        """
        Update the standings data and refresh the view.

        Args:
            standings: New list of Standing objects
        """
        self.beginResetModel()
        self._standings = standings
        self.endResetModel()

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        """
        Sort standings by column.

        Args:
            column: Column index to sort by
            order: Ascending or Descending
        """
        self.layoutAboutToBeChanged.emit()

        reverse = order == Qt.DescendingOrder

        if column == self.COL_TEAM:
            # Sort by team abbreviation
            self._standings.sort(
                key=lambda s: self._teams[s.team_id].abbreviation
                if s.team_id in self._teams
                else "",
                reverse=reverse,
            )

        elif column == self.COL_WINS:
            self._standings.sort(key=lambda s: s.wins, reverse=reverse)

        elif column == self.COL_LOSSES:
            self._standings.sort(key=lambda s: s.losses, reverse=reverse)

        elif column == self.COL_TIES:
            self._standings.sort(key=lambda s: s.ties, reverse=reverse)

        elif column == self.COL_PCT:
            self._standings.sort(key=lambda s: s.win_percentage, reverse=reverse)

        elif column == self.COL_DIV:
            self._standings.sort(
                key=lambda s: s.division_win_percentage, reverse=reverse
            )

        elif column == self.COL_CONF:
            self._standings.sort(
                key=lambda s: s.conference_win_percentage, reverse=reverse
            )

        self.layoutChanged.emit()
