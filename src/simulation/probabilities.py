"""
Probability conversion utilities for Monte Carlo simulation.

Converts American odds (moneyline format) to win probabilities,
with optional vig removal for more accurate probabilities.
"""

from typing import Optional, Tuple

from ..data.models import Game
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


def american_odds_to_probability(odds: int) -> float:
    """
    Convert American odds to implied win probability.

    American odds format:
    - Negative (favorite): -150 means bet $150 to win $100
    - Positive (underdog): +130 means bet $100 to win $130

    Args:
        odds: American odds (negative for favorites, positive for underdogs)

    Returns:
        Implied probability as float between 0 and 1

    Raises:
        ValueError: If odds is 0 or invalid

    Examples:
        >>> american_odds_to_probability(-150)
        0.6  # 60% probability
        >>> american_odds_to_probability(130)
        0.4347826086956522  # 43.5% probability
    """
    if odds == 0:
        raise ValueError("Odds cannot be zero")

    if odds < 0:
        # Favorite: probability = abs(odds) / (abs(odds) + 100)
        return abs(odds) / (abs(odds) + 100)
    else:
        # Underdog: probability = 100 / (odds + 100)
        return 100 / (odds + 100)


def remove_vig(prob_home: float, prob_away: float) -> Tuple[float, float]:
    """
    Remove bookmaker's vig (margin) by normalizing probabilities to sum to 1.0.

    Bookmakers build in a margin (vig), causing probabilities to sum > 100%.
    This function normalizes them to true probabilities.

    Args:
        prob_home: Home team implied probability (0-1)
        prob_away: Away team implied probability (0-1)

    Returns:
        Tuple of (normalized_home_prob, normalized_away_prob)

    Raises:
        ValueError: If probabilities are invalid (negative, sum to zero)

    Example:
        >>> remove_vig(0.60, 0.435)  # Sum = 1.035 (3.5% vig)
        (0.5797101449275362, 0.42028985507246375)  # Now sums to 1.0
    """
    if prob_home < 0 or prob_away < 0:
        raise ValueError("Probabilities cannot be negative")

    total = prob_home + prob_away

    if total == 0:
        raise ValueError("Probabilities cannot both be zero")

    return prob_home / total, prob_away / total


def validate_odds(home_odds: Optional[int], away_odds: Optional[int]) -> bool:
    """
    Validate that odds are in valid American odds format.

    Valid odds:
    - Exactly one must be negative (favorite)
    - Exactly one must be positive (underdog)
    - Neither can be zero
    - Both can be None (missing odds)

    Args:
        home_odds: Home team American odds (or None if missing)
        away_odds: Away team American odds (or None if missing)

    Returns:
        True if odds are valid, False otherwise
    """
    # Both None is valid (missing odds)
    if home_odds is None and away_odds is None:
        return True

    # If one is None, both must be None
    if home_odds is None or away_odds is None:
        return False

    # Neither can be zero
    if home_odds == 0 or away_odds == 0:
        return False

    # Exactly one should be negative (favorite) and one positive (underdog)
    # Both negative or both positive is invalid
    if (home_odds < 0 and away_odds < 0) or (home_odds > 0 and away_odds > 0):
        return False

    return True


def get_game_probabilities(
    game: Game, remove_vig_flag: bool = True, default_probability: float = 0.5
) -> Tuple[float, float]:
    """
    Extract win probabilities for a game, with optional vig removal.

    Handles edge cases:
    - Missing odds → returns default (0.5, 0.5)
    - Invalid odds → returns default (0.5, 0.5)
    - Override odds take precedence if game is overridden

    Args:
        game: Game object with odds information
        remove_vig_flag: If True, remove bookmaker's vig (default: True)
        default_probability: Probability to use when odds missing (default: 0.5)

    Returns:
        Tuple of (home_win_probability, away_win_probability)

    Example:
        >>> game = Game(..., home_moneyline=-150, away_moneyline=130)
        >>> get_game_probabilities(game)
        (0.58, 0.42)  # Normalized probabilities with vig removed
    """
    # Use override odds if game is overridden
    if game.is_overridden:
        home_odds = game.override_home_moneyline or game.home_moneyline
        away_odds = game.override_away_moneyline or game.away_moneyline
    else:
        home_odds = game.home_moneyline
        away_odds = game.away_moneyline

    # Validate odds
    if not validate_odds(home_odds, away_odds):
        logger.warning(
            f"Game {game.id}: Invalid or missing odds, using {default_probability:.1%} default"
        )
        return (default_probability, default_probability)

    # If both None (validated above), return default
    if home_odds is None and away_odds is None:
        return (default_probability, default_probability)

    # Convert to probabilities
    try:
        prob_home = american_odds_to_probability(home_odds)
        prob_away = american_odds_to_probability(away_odds)

        # Remove vig if requested
        if remove_vig_flag:
            prob_home, prob_away = remove_vig(prob_home, prob_away)

        return (prob_home, prob_away)

    except (ValueError, ZeroDivisionError) as e:
        logger.warning(
            f"Game {game.id}: Error converting odds ({home_odds}, {away_odds}): {e}. "
            f"Using {default_probability:.1%} default"
        )
        return (default_probability, default_probability)


def calculate_vig_percentage(prob_home: float, prob_away: float) -> float:
    """
    Calculate the bookmaker's vig (overround) percentage.

    The vig is how much the probabilities sum to above 100%.
    Example: If probabilities sum to 105%, vig is 5%.

    Args:
        prob_home: Home team implied probability (0-1)
        prob_away: Away team implied probability (0-1)

    Returns:
        Vig percentage (e.g., 0.05 for 5% vig)

    Example:
        >>> calculate_vig_percentage(0.60, 0.45)
        0.05  # 5% vig
    """
    total = prob_home + prob_away
    return max(0, total - 1.0)
