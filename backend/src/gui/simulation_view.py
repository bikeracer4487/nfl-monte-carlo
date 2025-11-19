"""
Simulation view for running and displaying Monte Carlo simulations.

Provides controls for configuring simulations and displays playoff probability results.
"""

from typing import List, Dict, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableView,
    QLabel,
    QHeaderView,
    QMessageBox,
)
from PySide6.QtCore import Qt, QThread

from ..data.models import Team, Game
from ..simulation.monte_carlo import SimulationResult
from ..utils.logger import setup_logger

from .widgets.simulation_controls import SimulationControls
from .models.simulation_model import PlayoffProbabilityModel
from .workers.simulation_worker import SimulationWorker

logger = setup_logger(__name__)


class SimulationView(QWidget):
    """View for running Monte Carlo simulations and displaying results."""

    def __init__(self, teams: List[Team], games: List[Game]):
        """
        Initialize simulation view.

        Args:
            teams: List of all NFL teams
            games: List of all games
        """
        super().__init__()

        self.teams = teams
        self.teams_dict = {team.id: team for team in teams}
        self.games = games

        # Simulation state
        self.current_result: Optional[SimulationResult] = None
        self.worker: Optional[SimulationWorker] = None
        self.thread: Optional[QThread] = None

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        # Top: Simulation controls
        self.controls = SimulationControls()
        self.controls.runSimulation.connect(self.on_run_simulation)
        self.controls.cancelSimulation.connect(self.on_cancel_simulation)
        main_layout.addWidget(self.controls)

        # Middle: Results table
        results_label = QLabel("<h3>Playoff Probabilities</h3>")
        main_layout.addWidget(results_label)

        self.results_table = QTableView()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableView.SelectRows)
        self.results_table.setSelectionMode(QTableView.SingleSelection)
        self.results_table.setSortingEnabled(True)

        # Configure header
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

        # Hide vertical header
        self.results_table.verticalHeader().setVisible(False)

        main_layout.addWidget(self.results_table)

        # Bottom: Status message
        self.no_results_label = QLabel(
            "<p style='color: #888;'>No simulation results yet. "
            "Configure parameters above and click 'Run Simulation' to begin.</p>"
        )
        self.no_results_label.setAlignment(Qt.AlignCenter)
        self.no_results_label.setWordWrap(True)
        main_layout.addWidget(self.no_results_label)

        # Initially hide table, show no results message
        self.results_table.setVisible(False)

        self.setLayout(main_layout)

    def on_run_simulation(
        self, num_sims: int, use_seed: bool, seed: int, week: int, use_odds: bool
    ):
        """
        Handle run simulation request.

        Args:
            num_sims: Number of simulations to run
            use_seed: Whether to use random seed
            seed: Random seed value
            week: Week to simulate from
            use_odds: Whether to use game odds
        """
        logger.info(
            f"Running simulation: num_sims={num_sims}, use_seed={use_seed}, "
            f"seed={seed}, week={week}, use_odds={use_odds}"
        )

        # Create worker and thread
        self.worker = SimulationWorker(
            games=self.games,
            teams=self.teams,
            num_simulations=num_sims,
            random_seed=seed if use_seed else None,
            remove_vig=self.controls.remove_vig_check.isChecked(),
            selected_week=week,
            use_odds=use_odds,
        )
        self.thread = QThread()

        # Move worker to thread
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.started.connect(self.on_simulation_started)
        self.worker.finished.connect(self.on_simulation_complete)
        self.worker.progress.connect(self.on_simulation_progress)
        self.worker.progress_value.connect(self.controls.progress_bar.setValue)
        self.worker.error.connect(self.on_simulation_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Start thread
        self.thread.start()

    def on_cancel_simulation(self):
        """Handle cancel simulation request."""
        logger.info("Cancellation requested")

        if self.thread and self.thread.isRunning():
            # Request interruption
            self.thread.requestInterruption()
            self.thread.quit()
            self.thread.wait()

        self.controls.simulation_complete()
        self.controls.set_status("Simulation cancelled")

    def on_simulation_started(self):
        """Handle simulation started."""
        logger.info("Simulation started")

    def on_simulation_progress(self, message: str):
        """
        Handle simulation progress update.

        Args:
            message: Progress message
        """
        self.controls.set_status(message)

    def on_simulation_complete(self, result: SimulationResult):
        """
        Handle simulation completion.

        Args:
            result: SimulationResult containing statistics
        """
        logger.info(f"Simulation complete: {result.num_simulations} simulations")

        # Store result
        self.current_result = result

        # Update UI
        self.controls.simulation_complete()

        # Create/update table model
        model = PlayoffProbabilityModel(result, self.teams_dict)
        self.results_table.setModel(model)

        # Show table, hide no results message
        self.results_table.setVisible(True)
        self.no_results_label.setVisible(False)

        # Sort by playoff probability (column 2) descending by default
        self.results_table.sortByColumn(2, Qt.DescendingOrder)

        logger.info("Results table updated")

    def on_simulation_error(self, error_message: str):
        """
        Handle simulation error.

        Args:
            error_message: Error message
        """
        logger.error(f"Simulation error: {error_message}")

        self.controls.simulation_complete()
        self.controls.set_status(f"Error: {error_message}")

        QMessageBox.warning(
            self,
            "Simulation Error",
            f"An error occurred during simulation:\n\n{error_message}",
        )

    def update_data(self, games: List[Game]):
        """
        Update with new game data (called after refresh).

        Args:
            games: Updated list of games
        """
        self.games = games
        logger.info(f"SimulationView data updated: {len(games)} games")
