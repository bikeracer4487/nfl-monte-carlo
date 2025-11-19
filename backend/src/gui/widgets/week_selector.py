"""
Week selector widget for NFL schedule navigation.

Provides a dropdown to select current week or specific weeks 1-18.
"""

from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import Signal


class WeekSelector(QComboBox):
    """Dropdown widget for selecting NFL week."""

    # Custom signal emitted when week changes
    # Emits -1 for "Current Week", or 1-18 for specific weeks
    weekChanged = Signal(int)

    def __init__(self, current_week: int = -1):
        """
        Initialize week selector.

        Args:
            current_week: Initial week to select (-1 for current, 1-18 for specific)
        """
        super().__init__()

        self.populate_weeks()
        self.set_current_week(current_week)

        # Connect internal signal to custom signal
        self.currentIndexChanged.connect(self._on_week_changed)

    def populate_weeks(self):
        """Populate dropdown with week options."""
        # Add "Current Week" option
        self.addItem("Current Week", userData=-1)

        # Add weeks 1-18
        for week in range(1, 19):
            self.addItem(f"Week {week}", userData=week)

    def set_current_week(self, week: int):
        """
        Set the currently selected week.

        Args:
            week: Week number (-1 for current, 1-18 for specific)
        """
        # Find index for this week
        for i in range(self.count()):
            if self.itemData(i) == week:
                self.setCurrentIndex(i)
                break

    def get_selected_week(self) -> int:
        """
        Get the currently selected week.

        Returns:
            Week number (-1 for current, 1-18 for specific)
        """
        return self.currentData()

    def _on_week_changed(self, index: int):
        """Handle week selection change."""
        week = self.itemData(index)
        self.weekChanged.emit(week)
