"""
Simulation view (Phase 5 placeholder).

This view will contain simulation controls and results in Phase 5.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class SimulationView(QWidget):
    """Placeholder for simulation controls and results."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Setup the placeholder UI."""
        layout = QVBoxLayout()

        label = QLabel(
            "<h2>Simulation View</h2>"
            "<p>Monte Carlo simulation controls and results will appear here in Phase 5.</p>"
            "<p>Features planned:</p>"
            "<ul>"
            "<li>Number of simulations slider</li>"
            "<li>Run simulation button with progress bar</li>"
            "<li>Playoff probability table</li>"
            "<li>Division win probability table</li>"
            "<li>#1 seed probability table</li>"
            "<li>Playoff seed distribution charts</li>"
            "</ul>"
        )
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)

        layout.addWidget(label)
        self.setLayout(layout)
