"""
Tests for probability conversion utilities.
"""

import pytest
from datetime import datetime

from src.simulation.probabilities import (
    american_odds_to_probability,
    remove_vig,
    validate_odds,
    get_game_probabilities,
    calculate_vig_percentage,
)
from src.data.models import Game


class TestAmericanOddsToProbability:
    """Tests for American odds conversion."""

    def test_favorite_odds(self):
        """Test conversion of negative (favorite) odds."""
        # -150: bet $150 to win $100 → 60% implied probability
        prob = american_odds_to_probability(-150)
        assert prob == pytest.approx(0.6, abs=0.001)

    def test_underdog_odds(self):
        """Test conversion of positive (underdog) odds."""
        # +130: bet $100 to win $130 → 43.5% implied probability
        prob = american_odds_to_probability(130)
        assert prob == pytest.approx(0.4348, abs=0.001)

    def test_heavy_favorite(self):
        """Test conversion of heavily favored team."""
        # -500: bet $500 to win $100 → 83.3% implied probability
        prob = american_odds_to_probability(-500)
        assert prob == pytest.approx(0.8333, abs=0.001)

    def test_heavy_underdog(self):
        """Test conversion of heavy underdog."""
        # +400: bet $100 to win $400 → 20% implied probability
        prob = american_odds_to_probability(400)
        assert prob == pytest.approx(0.2, abs=0.001)

    def test_pick_em_favorite(self):
        """Test slight favorite (close to 50/50)."""
        # -110: bet $110 to win $100 → 52.4% implied probability
        prob = american_odds_to_probability(-110)
        assert prob == pytest.approx(0.5238, abs=0.001)

    def test_pick_em_underdog(self):
        """Test slight underdog (close to 50/50)."""
        # +105: bet $100 to win $105 → 48.8% implied probability
        prob = american_odds_to_probability(105)
        assert prob == pytest.approx(0.4878, abs=0.001)

    def test_zero_odds_raises_error(self):
        """Test that zero odds raises ValueError."""
        with pytest.raises(ValueError, match="cannot be zero"):
            american_odds_to_probability(0)

    def test_probabilities_in_valid_range(self):
        """Test that all probabilities are between 0 and 1."""
        test_odds = [-1000, -500, -200, -150, -110, 100, 110, 150, 200, 500, 1000]
        for odds in test_odds:
            prob = american_odds_to_probability(odds)
            assert 0 < prob < 1, f"Probability for odds {odds} is out of range: {prob}"


class TestRemoveVig:
    """Tests for vig removal (probability normalization)."""

    def test_remove_vig_basic(self):
        """Test vig removal with typical odds."""
        # Probabilities sum to 1.035 (3.5% vig)
        prob_home, prob_away = remove_vig(0.6, 0.435)

        # Should now sum to 1.0
        assert prob_home + prob_away == pytest.approx(1.0)

        # Proportions maintained
        assert prob_home == pytest.approx(0.5797, abs=0.001)
        assert prob_away == pytest.approx(0.4203, abs=0.001)

    def test_remove_vig_already_normalized(self):
        """Test vig removal when probabilities already sum to 1."""
        prob_home, prob_away = remove_vig(0.5, 0.5)

        assert prob_home == pytest.approx(0.5)
        assert prob_away == pytest.approx(0.5)

    def test_remove_vig_high_vig(self):
        """Test vig removal with high bookmaker margin."""
        # 10% vig (uncommon but possible)
        prob_home, prob_away = remove_vig(0.55, 0.55)

        assert prob_home + prob_away == pytest.approx(1.0)
        assert prob_home == pytest.approx(0.5)
        assert prob_away == pytest.approx(0.5)

    def test_remove_vig_unequal_probabilities(self):
        """Test vig removal preserves relative probabilities."""
        prob_home, prob_away = remove_vig(0.7, 0.35)

        # Should sum to 1.0
        assert prob_home + prob_away == pytest.approx(1.0)

        # Home should still be twice as likely as away (0.7 / 0.35 = 2)
        assert prob_home / prob_away == pytest.approx(2.0)

    def test_remove_vig_negative_probability_raises_error(self):
        """Test that negative probabilities raise ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            remove_vig(-0.5, 0.5)

        with pytest.raises(ValueError, match="cannot be negative"):
            remove_vig(0.5, -0.5)

    def test_remove_vig_zero_sum_raises_error(self):
        """Test that zero sum raises ValueError."""
        with pytest.raises(ValueError, match="cannot both be zero"):
            remove_vig(0, 0)


class TestValidateOdds:
    """Tests for odds validation."""

    def test_validate_valid_odds_favorite_home(self):
        """Test validation of valid odds (home favorite)."""
        assert validate_odds(-150, 130) is True

    def test_validate_valid_odds_favorite_away(self):
        """Test validation of valid odds (away favorite)."""
        assert validate_odds(140, -160) is True

    def test_validate_both_none(self):
        """Test that both None is valid (missing odds)."""
        assert validate_odds(None, None) is True

    def test_validate_one_none_invalid(self):
        """Test that one None is invalid."""
        assert validate_odds(-150, None) is False
        assert validate_odds(None, 130) is False

    def test_validate_both_negative_invalid(self):
        """Test that both negative odds is invalid."""
        assert validate_odds(-150, -130) is False

    def test_validate_both_positive_invalid(self):
        """Test that both positive odds is invalid."""
        assert validate_odds(150, 130) is False

    def test_validate_zero_odds_invalid(self):
        """Test that zero odds is invalid."""
        assert validate_odds(0, 130) is False
        assert validate_odds(-150, 0) is False
        assert validate_odds(0, 0) is False


class TestGetGameProbabilities:
    """Tests for extracting probabilities from Game objects."""

    def test_get_probabilities_with_vig_removal(self):
        """Test getting probabilities with vig removal (default)."""
        game = Game(
            id="401234567",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=False,
            home_moneyline=-150,
            away_moneyline=130,
        )

        prob_home, prob_away = get_game_probabilities(game, remove_vig_flag=True)

        # Should sum to 1.0 (vig removed)
        assert prob_home + prob_away == pytest.approx(1.0)
        assert prob_home > prob_away  # Home is favorite

    def test_get_probabilities_without_vig_removal(self):
        """Test getting probabilities without vig removal."""
        game = Game(
            id="401234567",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=False,
            home_moneyline=-150,
            away_moneyline=130,
        )

        prob_home, prob_away = get_game_probabilities(game, remove_vig_flag=False)

        # Should sum to > 1.0 (vig included)
        assert prob_home + prob_away > 1.0
        assert prob_home == pytest.approx(0.6, abs=0.001)
        assert prob_away == pytest.approx(0.4348, abs=0.001)

    def test_get_probabilities_missing_odds(self):
        """Test handling of missing odds."""
        game = Game(
            id="401234567",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=False,
            home_moneyline=None,
            away_moneyline=None,
        )

        prob_home, prob_away = get_game_probabilities(game)

        # Should default to 50/50
        assert prob_home == 0.5
        assert prob_away == 0.5

    def test_get_probabilities_uses_override_odds(self):
        """Test that override odds take precedence."""
        game = Game(
            id="401234567",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=False,
            home_moneyline=-150,
            away_moneyline=130,
            is_overridden=True,
            override_home_moneyline=-200,  # Different from original
            override_away_moneyline=170,
        )

        prob_home, prob_away = get_game_probabilities(game, remove_vig_flag=False)

        # Should use override odds (-200, 170) not original (-150, 130)
        expected_home = american_odds_to_probability(-200)
        expected_away = american_odds_to_probability(170)

        assert prob_home == pytest.approx(expected_home, abs=0.001)
        assert prob_away == pytest.approx(expected_away, abs=0.001)

    def test_get_probabilities_partial_override(self):
        """Test override with only some odds overridden."""
        game = Game(
            id="401234567",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=False,
            home_moneyline=-150,
            away_moneyline=130,
            is_overridden=True,
            override_home_moneyline=-200,  # Override home only
            override_away_moneyline=None,  # Keep original away
        )

        prob_home, prob_away = get_game_probabilities(game, remove_vig_flag=False)

        # Should use override home (-200) and original away (130)
        expected_home = american_odds_to_probability(-200)
        expected_away = american_odds_to_probability(130)

        assert prob_home == pytest.approx(expected_home, abs=0.001)
        assert prob_away == pytest.approx(expected_away, abs=0.001)

    def test_get_probabilities_invalid_odds(self):
        """Test handling of invalid odds."""
        game = Game(
            id="401234567",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=False,
            home_moneyline=-150,
            away_moneyline=-130,  # Invalid: both negative
        )

        prob_home, prob_away = get_game_probabilities(game)

        # Should default to 50/50 for invalid odds
        assert prob_home == 0.5
        assert prob_away == 0.5

    def test_get_probabilities_custom_default(self):
        """Test custom default probability for missing odds."""
        game = Game(
            id="401234567",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=False,
            home_moneyline=None,
            away_moneyline=None,
        )

        prob_home, prob_away = get_game_probabilities(game, default_probability=0.6)

        # Should use custom default
        assert prob_home == 0.6
        assert prob_away == 0.6


class TestCalculateVigPercentage:
    """Tests for vig percentage calculation."""

    def test_calculate_vig_typical(self):
        """Test vig calculation with typical odds."""
        # Probabilities sum to 1.035 (3.5% vig)
        vig = calculate_vig_percentage(0.6, 0.435)
        assert vig == pytest.approx(0.035, abs=0.001)

    def test_calculate_vig_zero(self):
        """Test vig calculation when probabilities sum to 1.0."""
        vig = calculate_vig_percentage(0.5, 0.5)
        assert vig == pytest.approx(0.0, abs=0.001)

    def test_calculate_vig_high(self):
        """Test vig calculation with high margin."""
        # Probabilities sum to 1.10 (10% vig)
        vig = calculate_vig_percentage(0.55, 0.55)
        assert vig == pytest.approx(0.10, abs=0.001)

    def test_calculate_vig_negative_returns_zero(self):
        """Test that negative vig (underround) returns 0."""
        # Probabilities sum to 0.95 (shouldn't happen in real bookmaking)
        vig = calculate_vig_percentage(0.45, 0.50)
        assert vig == 0.0
