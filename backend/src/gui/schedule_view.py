"""
Schedule editor view (Phase 6 placeholder).

This view will contain the schedule with override capabilities in Phase 6.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class ScheduleView(QWidget):
    """Placeholder for schedule editor."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Setup the placeholder UI."""
        layout = QVBoxLayout()

        label = QLabel(
            "<h2>Schedule Editor</h2>"
            "<p>Schedule editing and override capabilities will appear here in Phase 6.</p>"
            "<p>Features planned:</p>"
            "<ul>"
            "<li>Full season schedule table</li>"
            "<li>Filter by week/team</li>"
            "<li>Override game outcomes</li>"
            "<li>Override betting odds</li>"
            "<li>Reset overrides</li>"
            "<li>'What If' scenario builder</li>"
            "</ul>"
        )
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)

        layout.addWidget(label)
        self.setLayout(layout)
