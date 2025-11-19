from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional, List

from src.data.models import Game, Team
from src.simulation.monte_carlo import (
    SimulationResult,
    simulate_season,
    SimulationCancelledError,
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class SimulationJob:
    """Represents a long-running simulation job."""

    id: str
    num_simulations: int
    random_seed: Optional[int]
    status: str = "pending"  # pending, running, completed, cancelled, error
    progress: int = 0
    message: str = ""
    result: Optional[SimulationResult] = None
    error: Optional[str] = None
    execution_time_seconds: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    _thread: Optional[threading.Thread] = field(default=None, repr=False)
    _cancel_event: threading.Event = field(default_factory=threading.Event, repr=False)

    def to_dict(self) -> Dict[str, object]:
        """Serialize job for API responses."""
        return {
            "job_id": self.id,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "num_simulations": self.num_simulations,
            "random_seed": self.random_seed,
            "result": self._serialize_result(),
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "execution_time": self.execution_time_seconds,
        }

    def _serialize_result(self) -> Optional[Dict[str, object]]:
        if not self.result:
            return None

        serialized = {
            "num_simulations": self.result.num_simulations,
            "execution_time": self.result.execution_time_seconds,
            "team_stats": {},
        }

        for team_id, stats in self.result.team_stats.items():
            serialized["team_stats"][team_id] = {
                "playoff_probability": stats.playoff_probability,
                "division_win_probability": stats.division_win_probability,
                "first_seed_probability": stats.first_seed_probability,
                "average_wins": stats.average_wins,
                "seed_probabilities": stats.seed_probabilities,
            }

        return serialized

    def cancel(self):
        """Signal cancellation for the running job."""
        if self.status in {"completed", "cancelled", "error"}:
            return
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()


class SimulationJobManager:
    """Manages lifecycle of simulation jobs."""

    def __init__(self):
        self._jobs: Dict[str, SimulationJob] = {}
        self._lock = threading.Lock()

    def start_job(
        self,
        games: List[Game],
        teams: List[Team],
        num_simulations: int,
        random_seed: Optional[int] = None,
    ) -> SimulationJob:
        """Start a new simulation job."""
        with self._lock:
            if self._has_active_job_locked():
                raise RuntimeError("Another simulation is already running")

            job_id = str(uuid.uuid4())
            job = SimulationJob(
                id=job_id,
                num_simulations=num_simulations,
                random_seed=random_seed,
                message=f"Queued {num_simulations:,} simulations",
            )
            self._jobs[job_id] = job

            thread = threading.Thread(
                target=self._run_job, args=(job, games, teams), daemon=True
            )
            job._thread = thread
            thread.start()

            return job

    def get_job(self, job_id: str) -> Optional[SimulationJob]:
        """Retrieve a job by ID."""
        with self._lock:
            return self._jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Request cancellation of a running job."""
        job = self.get_job(job_id)
        if not job:
            return False

        job.cancel()
        return True

    def _has_active_job_locked(self) -> bool:
        return any(
            job.status in {"pending", "running"} for job in self._jobs.values()
        )

    def has_active_job(self) -> bool:
        with self._lock:
            return self._has_active_job_locked()

    def _run_job(self, job: SimulationJob, games: List[Game], teams: List[Team]):
        job.status = "running"
        job.started_at = time.time()
        job.message = f"Running {job.num_simulations:,} simulations..."

        def progress_callback(pct: int):
            job.progress = pct
            job.message = f"{pct}% complete"

        try:
            result = simulate_season(
                games=games,
                teams=teams,
                num_simulations=job.num_simulations,
                random_seed=job.random_seed,
                progress_callback=progress_callback,
                cancel_callback=job.is_cancelled,
            )
            job.result = result
            job.progress = 100
            job.status = "completed"
            job.message = "Simulation complete"
            job.execution_time_seconds = result.execution_time_seconds
        except SimulationCancelledError:
            job.status = "cancelled"
            job.message = "Simulation cancelled"
        except Exception as exc:
            logger.exception("Simulation job %s failed", job.id)
            job.status = "error"
            job.error = str(exc)
            job.message = "Simulation failed"
        finally:
            job.completed_at = time.time()


