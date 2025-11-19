"""
Background worker for running Monte Carlo simulations.

Runs simulations in a background thread to prevent UI blocking.
"""

import time
from typing import List, Optional

from PySide6.QtCore import QObject, Signal

from ...data.models import Team, Game
from ...simulation.monte_carlo import simulate_season, SimulationResult
from ...utils.logger import setup_logger

logger = setup_logger(__name__)


class SimulationWorker(QObject):
    """Worker for running Monte Carlo simulations in background thread."""

    # Signals
    finished = Signal(object)  # Emits SimulationResult
    progress = Signal(str)  # Emits status messages
    error = Signal(str)  # Emits error messages
    started = Signal()  # Emits when simulation starts

    def __init__(
        self,
        games: List[Game],
        teams: List[Team],
        num_simulations: int,
        random_seed: Optional[int],
        remove_vig: bool,
        selected_week: int,
    ):
        """
        Initialize simulation worker.

        Args:
            games: List of all games
            teams: List of all teams
            num_simulations: Number of simulations to run
            random_seed: Random seed for reproducibility (None for random)
            remove_vig: Whether to remove vig from odds
            selected_week: Week to simulate from (-1 for current)
        """
        super().__init__()
        self.games = games
        self.teams = teams
        self.num_simulations = num_simulations
        self.random_seed = random_seed
        self.remove_vig = remove_vig
        self.selected_week = selected_week

    def run(self):
        """Run Monte Carlo simulation in background."""
        try:
            logger.info(
                f"Starting simulation: {self.num_simulations} simulations, "
                f"week {self.selected_week}, seed={self.random_seed}, "
                f"remove_vig={self.remove_vig}"
            )

            # Emit started signal
            self.started.emit()
            self.progress.emit(
                f"Running {self.num_simulations:,} simulations..."
            )

            # Filter games based on selected week
            if self.selected_week == -1:
                # Current week: use all games (completed games are locked in simulation)
                filtered_games = self.games
            else:
                # Specific week: only simulate games after that week
                filtered_games = self.games  # Simulation handles this internally

            # Record start time
            start_time = time.time()

            # Run simulation
            result = simulate_season(
                games=filtered_games,
                teams=self.teams,
                num_simulations=self.num_simulations,
                random_seed=self.random_seed,
                remove_vig=self.remove_vig,
            )

            # Calculate execution time
            execution_time = time.time() - start_time

            logger.info(
                f"Simulation complete: {execution_time:.2f}s "
                f"({self.num_simulations / execution_time:.0f} sims/sec)"
            )

            # Emit progress message
            self.progress.emit(
                f"Complete: {self.num_simulations:,} simulations in {execution_time:.1f}s"
            )

            # Emit result
            self.finished.emit(result)

        except Exception as e:
            logger.error(f"Simulation error: {e}")
            import traceback

            traceback.print_exc()
            self.error.emit(f"Simulation failed: {str(e)}")
