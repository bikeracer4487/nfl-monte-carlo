"""
Score generation for Monte Carlo simulations.

Provides Poisson-based score generation for simulating game outcomes.
"""

import numpy as np
from typing import Optional


# NFL league averages (approximate)
DEFAULT_POINTS_MEAN = 24.0  # Average points per team per game
DEFAULT_POINTS_STDDEV = 10.0  # Standard deviation


def generate_game_score(
    mean: float = DEFAULT_POINTS_MEAN,
    random_state: Optional[np.random.RandomState] = None,
) -> int:
    """
    Generate a single game score using Poisson distribution.

    Args:
        mean: Average points (lambda parameter for Poisson)
        random_state: Optional numpy RandomState for reproducibility

    Returns:
        Generated score (integer)
    """
    if random_state is None:
        return int(np.random.poisson(mean))
    return int(random_state.poisson(mean))


def generate_game_scores_vectorized(
    num_games: int,
    mean: float = DEFAULT_POINTS_MEAN,
    random_state: Optional[np.random.RandomState] = None,
) -> np.ndarray:
    """
    Generate multiple game scores efficiently using vectorized operations.

    Args:
        num_games: Number of scores to generate
        mean: Average points (lambda parameter for Poisson)
        random_state: Optional numpy RandomState for reproducibility

    Returns:
        Array of generated scores (num_games,)
    """
    if random_state is None:
        return np.random.poisson(mean, size=num_games)
    return random_state.poisson(mean, size=num_games)


def generate_game_scores_matrix(
    num_simulations: int,
    num_games: int,
    mean: float = DEFAULT_POINTS_MEAN,
    random_state: Optional[np.random.RandomState] = None,
) -> np.ndarray:
    """
    Generate scores for multiple simulations efficiently.

    Used in Monte Carlo simulation to generate scores for all games
    across all simulation iterations at once.

    Args:
        num_simulations: Number of simulation iterations
        num_games: Number of games per simulation
        mean: Average points (lambda parameter for Poisson)
        random_state: Optional numpy RandomState for reproducibility

    Returns:
        Array of scores (num_simulations, num_games)
    """
    if random_state is None:
        return np.random.poisson(mean, size=(num_simulations, num_games))
    return random_state.poisson(mean, size=(num_simulations, num_games))


def generate_game_outcome_with_scores(
    home_win_probability: float,
    mean_score: float = DEFAULT_POINTS_MEAN,
    random_state: Optional[np.random.RandomState] = None,
) -> tuple[bool, int, int]:
    """
    Generate a complete game outcome: winner and scores.

    Args:
        home_win_probability: Probability that home team wins (0.0-1.0)
        mean_score: Average points per team
        random_state: Optional numpy RandomState for reproducibility

    Returns:
        Tuple of (home_wins, home_score, away_score)
    """
    if random_state is None:
        home_wins = np.random.random() < home_win_probability
        home_score = int(np.random.poisson(mean_score))
        away_score = int(np.random.poisson(mean_score))
    else:
        home_wins = random_state.random() < home_win_probability
        home_score = int(random_state.poisson(mean_score))
        away_score = int(random_state.poisson(mean_score))

    # Ensure the score reflects the winner
    # If home team should win but score is lower, flip scores
    if home_wins and away_score >= home_score:
        home_score, away_score = away_score + 1, home_score
    elif not home_wins and home_score >= away_score:
        home_score, away_score = away_score, home_score + 1

    return home_wins, home_score, away_score


def generate_outcomes_with_scores_vectorized(
    home_win_probabilities: np.ndarray,
    mean_score: float = DEFAULT_POINTS_MEAN,
    random_state: Optional[np.random.RandomState] = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate game outcomes with scores for multiple games (vectorized).

    Args:
        home_win_probabilities: Array of home win probabilities
        mean_score: Average points per team
        random_state: Optional numpy RandomState for reproducibility

    Returns:
        Tuple of (home_wins_array, home_scores_array, away_scores_array)
    """
    num_games = len(home_win_probabilities)

    if random_state is None:
        random_vals = np.random.random(num_games)
        home_scores = np.random.poisson(mean_score, size=num_games)
        away_scores = np.random.poisson(mean_score, size=num_games)
    else:
        random_vals = random_state.random(num_games)
        home_scores = random_state.poisson(mean_score, size=num_games)
        away_scores = random_state.poisson(mean_score, size=num_games)

    home_wins = random_vals < home_win_probabilities

    # Ensure scores reflect winners
    # Where home should win but didn't score more, give home team one more point than away
    fix_home_wins = home_wins & (away_scores >= home_scores)
    home_scores[fix_home_wins] = away_scores[fix_home_wins] + 1

    # Where away should win but didn't score more, give away team one more point than home
    fix_away_wins = ~home_wins & (home_scores >= away_scores)
    away_scores[fix_away_wins] = home_scores[fix_away_wins] + 1

    return home_wins.astype(int), home_scores, away_scores
