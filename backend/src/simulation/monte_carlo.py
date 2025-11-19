"""
Monte Carlo simulation engine for NFL season outcomes.

Uses vectorized NumPy operations for high performance simulation of
thousands of season outcomes using unbiased 50/50 coin flips for every remaining game.
Phase 3 includes tiebreaker-based playoff seeding.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable
from copy import deepcopy

import numpy as np

from ..data.models import Game, Team, Standing
from ..utils.logger import setup_logger
from .scores import generate_game_score, DEFAULT_POINTS_MEAN
from .standings import calculate_standings
from .tiebreakers import seed_conference_playoffs, determine_division_winners

logger = setup_logger(__name__)


@dataclass
class TeamSimulationStats:
    """Statistics for a single team across all simulations."""

    team_id: str
    wins_distribution: List[int] = field(default_factory=list)
    made_playoffs_count: int = 0
    won_division_count: int = 0
    first_seed_count: int = 0  # Conference #1 seed (bye week)
    seed_counts: Dict[int, int] = field(default_factory=lambda: {i: 0 for i in range(1, 8)})  # Seeds 1-7
    total_simulations: int = 0

    @property
    def playoff_probability(self) -> float:
        """Probability of making playoffs."""
        if self.total_simulations == 0:
            return 0.0
        return self.made_playoffs_count / self.total_simulations

    @property
    def division_win_probability(self) -> float:
        """Probability of winning division."""
        if self.total_simulations == 0:
            return 0.0
        return self.won_division_count / self.total_simulations

    @property
    def first_seed_probability(self) -> float:
        """Probability of getting #1 seed (bye week)."""
        if self.total_simulations == 0:
            return 0.0
        return self.first_seed_count / self.total_simulations

    @property
    def seed_probabilities(self) -> Dict[int, float]:
        """Probability of each playoff seed (1-7)."""
        if self.total_simulations == 0:
            return {i: 0.0 for i in range(1, 8)}
        return {
            seed: count / self.total_simulations
            for seed, count in self.seed_counts.items()
        }

    @property
    def average_wins(self) -> float:
        """Average number of wins across simulations."""
        if not self.wins_distribution:
            return 0.0
        return np.mean(self.wins_distribution)

    @property
    def wins_percentiles(self) -> Dict[int, float]:
        """Win distribution percentiles (10th, 25th, 50th, 75th, 90th)."""
        if not self.wins_distribution:
            return {}
        return {
            10: np.percentile(self.wins_distribution, 10),
            25: np.percentile(self.wins_distribution, 25),
            50: np.percentile(self.wins_distribution, 50),
            75: np.percentile(self.wins_distribution, 75),
            90: np.percentile(self.wins_distribution, 90),
        }


@dataclass
class SimulationResult:
    """Aggregated results from Monte Carlo simulations."""

    team_stats: Dict[str, TeamSimulationStats] = field(default_factory=dict)
    num_simulations: int = 0
    execution_time_seconds: float = 0.0

    def get_team_stats(self, team_id: str) -> Optional[TeamSimulationStats]:
        """Get statistics for a specific team."""
        return self.team_stats.get(team_id)

    def get_playoff_probabilities(self) -> Dict[str, float]:
        """Get playoff probabilities for all teams."""
        return {
            team_id: stats.playoff_probability
            for team_id, stats in self.team_stats.items()
        }

    def get_division_win_probabilities(self) -> Dict[str, float]:
        """Get division winner probabilities for all teams."""
        return {
            team_id: stats.division_win_probability
            for team_id, stats in self.team_stats.items()
        }

    def get_average_wins(self) -> Dict[str, float]:
        """Get average wins for all teams."""
        return {
            team_id: stats.average_wins for team_id, stats in self.team_stats.items()
        }


def simulate_season(
    games: List[Game],
    teams: List[Team],
    num_simulations: int = 10000,
    random_seed: Optional[int] = None,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> SimulationResult:
    """
    Run Monte Carlo simulation of NFL season using vectorized NumPy operations.

    This is the main entry point for simulations. It:
    1. Separates completed games (use actual results) from remaining games
    2. Treats each remaining matchup as a 50/50 coin flip
    3. Generates random outcomes for all remaining games across all simulations
    4. Calculates standings for each simulation
    5. Aggregates results into statistics

    Args:
        games: List of all games in the season
        teams: List of all teams
        num_simulations: Number of Monte Carlo simulations to run (default: 10000)
        random_seed: Optional random seed for reproducibility
        progress_callback: Optional callback function receiving percentage complete (0-100)

    Returns:
        SimulationResult with aggregated statistics

    Example:
        >>> result = simulate_season(games, teams, num_simulations=10000)
        >>> chiefs_stats = result.get_team_stats("12")  # Kansas City
        >>> print(f"Playoff odds: {chiefs_stats.playoff_probability:.1%}")
        Playoff odds: 87.3%
    """
    import time

    start_time = time.time()

    if random_seed is not None:
        np.random.seed(random_seed)

    logger.info(f"Starting {num_simulations:,} simulations with {len(games)} games")

    # Separate completed and remaining games
    completed_games = [g for g in games if g.is_completed]
    remaining_games = [g for g in games if not g.is_completed]

    logger.info(
        f"Games: {len(completed_games)} completed, {len(remaining_games)} remaining"
    )

    # Extract probabilities for remaining games
    # No per-game weighting is required—every matchup is treated as 50/50.

    # Create probability matrix: (num_simulations × num_games)
    if remaining_games:
        # Generate ALL random outcomes at once (vectorized)
        random_matrix = np.random.random((num_simulations, len(remaining_games)))

        # Home wins = 1, Away wins = 0
        home_wins_matrix = (random_matrix < 0.5).astype(int)

        # Generate ALL random scores at once (vectorized)
        # Generate random poisson scores for all games in all simulations
        home_scores_matrix = np.random.poisson(DEFAULT_POINTS_MEAN, size=(num_simulations, len(remaining_games)))
        away_scores_matrix = np.random.poisson(DEFAULT_POINTS_MEAN, size=(num_simulations, len(remaining_games)))

        # Fix scores to match winners
        # 1. Where home won but score <= away score
        fix_home_wins = (home_wins_matrix == 1) & (away_scores_matrix >= home_scores_matrix)
        home_scores_matrix[fix_home_wins] = away_scores_matrix[fix_home_wins] + 1

        # 2. Where away won (home_wins == 0) but score <= home score
        fix_away_wins = (home_wins_matrix == 0) & (home_scores_matrix >= away_scores_matrix)
        away_scores_matrix[fix_away_wins] = home_scores_matrix[fix_away_wins] + 1

        logger.info(
            f"Generated {num_simulations * len(remaining_games):,} random game outcomes"
        )
    else:
        # All games completed, no simulations needed
        home_wins_matrix = np.zeros((num_simulations, 0), dtype=int)
        home_scores_matrix = np.zeros((num_simulations, 0), dtype=int)
        away_scores_matrix = np.zeros((num_simulations, 0), dtype=int)

    # Initialize team stats
    team_stats = {
        team.id: TeamSimulationStats(
            team_id=team.id, total_simulations=num_simulations
        )
        for team in teams
    }

    # Create team ID to index mapping
    team_id_to_idx = {team.id: idx for idx, team in enumerate(teams)}

    # Process each simulation
    
    # Pre-allocate simulation objects to avoid deepcopy overhead in loop
    # We'll reuse these objects for every simulation, just updating scores
    simulation_buffer_games = [deepcopy(g) for g in remaining_games]
    for game in simulation_buffer_games:
        game.is_completed = True
        
    # Progress reporting variables
    last_progress_pct = -1
    progress_interval = max(1, num_simulations // 100)  # Report every 1%
    
    for sim_idx in range(num_simulations):
        # Report progress
        if progress_callback and sim_idx % progress_interval == 0:
            pct = int((sim_idx / num_simulations) * 100)
            if pct > last_progress_pct:
                progress_callback(pct)
                last_progress_pct = pct
                
        # Create list of all games for this simulation (completed + simulated)
        # optimization: construct list without deepcopying completed_games (they are read-only here)
        sim_games = completed_games + simulation_buffer_games

        # Apply pre-calculated scores to simulation games
        if remaining_games:
            for game_idx, sim_game in enumerate(simulation_buffer_games):
                sim_game.home_score = int(home_scores_matrix[sim_idx, game_idx])
                sim_game.away_score = int(away_scores_matrix[sim_idx, game_idx])

        # Calculate full standings with tiebreaker data
        standings_dict = calculate_standings(sim_games, teams)

        # Store win totals
        for team_id, standing in standings_dict.items():
            team_stats[team_id].wins_distribution.append(standing.wins)

        # Determine division winners (with tiebreakers)
        division_winners = determine_division_winners(teams, standings_dict, sim_games)
        for winner_id in division_winners.values():
            team_stats[winner_id].won_division_count += 1

        # Determine playoff seeding for each conference (with tiebreakers)
        for conference in ["AFC", "NFC"]:
            try:
                playoff_seeds = seed_conference_playoffs(
                    teams, standings_dict, sim_games, conference
                )

                # Track playoff appearances and seeds
                for seed_num, team_id in enumerate(playoff_seeds, start=1):
                    team_stats[team_id].made_playoffs_count += 1
                    team_stats[team_id].seed_counts[seed_num] += 1

                    if seed_num == 1:
                        team_stats[team_id].first_seed_count += 1
            except Exception as e:
                logger.warning(f"Error in playoff seeding for {conference} in sim {sim_idx}: {e}")
                # Fall back to simple method for this simulation
                continue

    if progress_callback:
        progress_callback(100)

    execution_time = time.time() - start_time
    logger.info(
        f"Simulations complete in {execution_time:.2f}s "
        f"({num_simulations/execution_time:.0f} sims/sec)"
    )

    return SimulationResult(
        team_stats=team_stats,
        num_simulations=num_simulations,
        execution_time_seconds=execution_time,
    )


def determine_playoff_teams_simple(
    teams: List[Team], team_wins: Dict[str, int], teams_per_conference: int = 7
) -> List[str]:
    """
    Simple playoff determination: top N teams by wins in each conference.

    This is a placeholder for Phase 2. Phase 3 will implement full
    tiebreaker logic for accurate playoff determination.

    Args:
        teams: List of all teams
        team_wins: Dictionary mapping team_id to win count
        teams_per_conference: Number of playoff teams per conference (default: 7)

    Returns:
        List of team IDs that made playoffs
    """
    afc_teams = [t for t in teams if t.conference == "AFC"]
    nfc_teams = [t for t in teams if t.conference == "NFC"]

    playoff_teams = []

    # AFC playoffs
    afc_sorted = sorted(afc_teams, key=lambda t: team_wins[t.id], reverse=True)
    playoff_teams.extend([t.id for t in afc_sorted[:teams_per_conference]])

    # NFC playoffs
    nfc_sorted = sorted(nfc_teams, key=lambda t: team_wins[t.id], reverse=True)
    playoff_teams.extend([t.id for t in nfc_sorted[:teams_per_conference]])

    return playoff_teams


def determine_division_winners_simple(
    teams: List[Team], team_wins: Dict[str, int]
) -> Dict[str, str]:
    """
    Simple division winner determination: team with most wins in each division.

    This is a placeholder for Phase 2. Phase 3 will implement full
    tiebreaker logic for accurate division winner determination.

    Args:
        teams: List of all teams
        team_wins: Dictionary mapping team_id to win count

    Returns:
        Dictionary mapping division name (e.g., "AFC_North") to winner team_id
    """
    divisions = {}
    division_keys = []

    # Group teams by division
    for conference in ["AFC", "NFC"]:
        for division in ["North", "South", "East", "West"]:
            div_teams = [
                t
                for t in teams
                if t.conference == conference and t.division == division
            ]
            if div_teams:
                div_key = f"{conference}_{division}"
                divisions[div_key] = div_teams
                division_keys.append(div_key)

    # Determine winner for each division
    winners = {}
    for div_key, div_teams in divisions.items():
        winner = max(div_teams, key=lambda t: team_wins[t.id])
        winners[div_key] = winner.id

    return winners
