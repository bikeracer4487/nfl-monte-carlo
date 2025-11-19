"""
Simulation controls widget for configuring and running Monte Carlo simulations.

Provides UI controls for simulation parameters and execution.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QCheckBox,
    QPushButton,
    QProgressBar,
)
from PySide6.QtCore import Qt, Signal

from ...utils.logger import setup_logger

logger = setup_logger(__name__)


class SimulationControls(QWidget):
    """Widget for simulation configuration and control."""

    # Signals
    runSimulation = Signal(int, bool, int, int, bool)  # num_sims, use_seed, seed, week, use_odds
    cancelSimulation = Signal()

    def __init__(self):
        """Initialize simulation controls."""
        super().__init__()

        self.is_running = False

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface."""
        main_layout = QVBoxLayout()

        # Create group box for controls
        controls_group = QGroupBox("Simulation Configuration")
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(15)

        # Row 1: Number of simulations
        sims_layout = QHBoxLayout()
        sims_layout.addWidget(QLabel("Number of Simulations:"))

        self.num_sims_spin = QSpinBox()
        self.num_sims_spin.setMinimum(100)
        self.num_sims_spin.setMaximum(1_000_000)
        self.num_sims_spin.setValue(10_000)
        self.num_sims_spin.setSingleStep(1000)
        self.num_sims_spin.setGroupSeparatorShown(True)
        sims_layout.addWidget(self.num_sims_spin)

        # Preset buttons
        preset_1k = QPushButton("1K")
        preset_1k.setMaximumWidth(60)
        preset_1k.clicked.connect(lambda: self.num_sims_spin.setValue(1_000))
        sims_layout.addWidget(preset_1k)

        preset_10k = QPushButton("10K")
        preset_10k.setMaximumWidth(60)
        preset_10k.clicked.connect(lambda: self.num_sims_spin.setValue(10_000))
        sims_layout.addWidget(preset_10k)

        preset_100k = QPushButton("100K")
        preset_100k.setMaximumWidth(60)
        preset_100k.clicked.connect(lambda: self.num_sims_spin.setValue(100_000))
        sims_layout.addWidget(preset_100k)

        preset_1m = QPushButton("1M")
        preset_1m.setMaximumWidth(60)
        preset_1m.clicked.connect(lambda: self.num_sims_spin.setValue(1_000_000))
        sims_layout.addWidget(preset_1m)

        sims_layout.addStretch()
        controls_layout.addLayout(sims_layout)

        # Row 2: Options
        options_layout = QHBoxLayout()

        self.use_odds_check = QCheckBox("Use game odds")
        self.use_odds_check.setChecked(True)
        self.use_odds_check.setToolTip("If unchecked, all matchups are treated as 50/50 coin tosses")
        options_layout.addWidget(self.use_odds_check)

        options_layout.addSpacing(20)

        self.remove_vig_check = QCheckBox("Remove vig from odds")
        self.remove_vig_check.setChecked(True)
        options_layout.addWidget(self.remove_vig_check)

        options_layout.addSpacing(20)

        self.use_seed_check = QCheckBox("Use random seed:")
        self.use_seed_check.setChecked(False)
        options_layout.addWidget(self.use_seed_check)

        self.random_seed_spin = QSpinBox()
        self.random_seed_spin.setMinimum(0)
        self.random_seed_spin.setMaximum(999_999)
        self.random_seed_spin.setValue(42)
        self.random_seed_spin.setEnabled(False)
        self.use_seed_check.toggled.connect(self.random_seed_spin.setEnabled)
        options_layout.addWidget(self.random_seed_spin)

        options_layout.addStretch()
        controls_layout.addLayout(options_layout)

        # Row 3: Week selection
        week_layout = QHBoxLayout()
        week_layout.addWidget(QLabel("Simulate from:"))

        # Import WeekSelector here to avoid circular imports
        from .week_selector import WeekSelector

        self.week_selector = WeekSelector(current_week=-1)
        week_layout.addWidget(self.week_selector)

        week_layout.addStretch()
        controls_layout.addLayout(week_layout)

        # Row 4: Action buttons
        buttons_layout = QHBoxLayout()

        self.run_button = QPushButton("Run Simulation")
        self.run_button.setObjectName("primary_button")
        self.run_button.clicked.connect(self.on_run_clicked)
        buttons_layout.addWidget(self.run_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        buttons_layout.addWidget(self.cancel_button)

        buttons_layout.addStretch()
        controls_layout.addLayout(buttons_layout)

        # Row 5: Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        controls_layout.addWidget(self.progress_bar)

        # Row 6: Status message
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        controls_layout.addWidget(self.status_label)

        controls_group.setLayout(controls_layout)
        main_layout.addWidget(controls_group)

        self.setLayout(main_layout)

    def on_run_clicked(self):
        """Handle run button click."""
        num_sims = self.num_sims_spin.value()
        use_seed = self.use_seed_check.isChecked()
        seed = self.random_seed_spin.value() if use_seed else -1
        week = self.week_selector.current_week
        use_odds = self.use_odds_check.isChecked()

        logger.info(
            f"Run simulation clicked: {num_sims} sims, seed={seed}, week={week}, use_odds={use_odds}"
        )

        # Update UI state
        self.set_running(True)
        self.progress_bar.setValue(0)

        # Emit signal
        self.runSimulation.emit(num_sims, use_seed, seed, week, use_odds)

    def on_cancel_clicked(self):
        """Handle cancel button click."""
        logger.info("Cancel simulation clicked")
        self.cancelSimulation.emit()

    def set_running(self, running: bool):
        """
        Update UI state for running/idle.

        Args:
            running: True if simulation is running, False if idle
        """
        self.is_running = running

        # Update button states
        self.run_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)

        # Update progress bar visibility
        self.progress_bar.setVisible(running)

        # Update controls
        self.num_sims_spin.setEnabled(not running)
        self.use_odds_check.setEnabled(not running)
        self.remove_vig_check.setEnabled(not running)
        self.use_seed_check.setEnabled(not running)
        self.random_seed_spin.setEnabled(not running and self.use_seed_check.isChecked())
        self.week_selector.setEnabled(not running)

    def set_status(self, message: str):
        """
        Set status message.

        Args:
            message: Status message to display
        """
        self.status_label.setText(message)

    def simulation_complete(self):
        """Handle simulation completion."""
        self.set_running(False)
