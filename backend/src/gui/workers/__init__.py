"""
Workers package for background tasks.

Contains QObject workers for running long-running operations in background threads.
"""

from .simulation_worker import SimulationWorker

__all__ = ["SimulationWorker"]
