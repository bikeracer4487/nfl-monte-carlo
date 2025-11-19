"""
Tests for data models (Team, Game, Standing).
"""

import pytest
from datetime import datetime

from src.data.models import Team, Game, Standing


class TestTeam:
    """Tests for Team model."""

    def test_team_creation(self, sample_team):
        """Test Team object creation."""
        assert sample_team.id == "1"
        assert sample_team.abbreviation == "ATL"
        assert sample_team.name == "Atlanta Falcons"
        assert sample_team.conference == "NFC"
        assert sample_team.division == "South"

    def test_team_str_representation(self, sample_team):
        """Test __str__ method."""
        assert str(sample_team) == "Atlanta Falcons"

    def test_full_division(self, sample_team):
        """Test full_division() method."""
        assert sample_team.full_division() == "NFC South"

    def test_team_with_optional_fields(self):
        """Test Team creation with optional fields."""
        team = Team(
            id="3",
            abbreviation="KC",
            name="Kansas City Chiefs",
            display_name="Chiefs",
            location="Kansas City",
            conference="AFC",
            division="West",
            color="#E31837",
            logo_url="https://example.com/kc_logo.png",
        )
        assert team.color == "#E31837"
        assert team.logo_url == "https://example.com/kc_logo.png"


class TestGame:
    """Tests for Game model."""

    def test_game_creation(self, sample_game):
        """Test Game object creation."""
        assert sample_game.id == "401234567"
        assert sample_game.week == 1
        assert sample_game.season == 2025
        assert sample_game.home_team_id == "1"
        assert sample_game.away_team_id == "2"
        assert sample_game.is_completed is False

    def test_get_winner_completed_game(self, sample_completed_game):
        """Test get_winner_id() for completed game."""
        winner = sample_completed_game.get_winner_id()
        assert winner == "1"  # Home team won 24-17

    def test_get_winner_incomplete_game(self, sample_game):
        """Test get_winner_id() returns None for incomplete game."""
        winner = sample_game.get_winner_id()
        assert winner is None

    def test_get_winner_tie_game(self, sample_tie_game):
        """Test get_winner_id() returns None for tie."""
        winner = sample_tie_game.get_winner_id()
        assert winner is None

    def test_get_winner_away_team(self):
        """Test get_winner_id() when away team wins."""
        game = Game(
            id="401234570",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=True,
            home_score=17,
            away_score=24,
        )
        assert game.get_winner_id() == "2"  # Away team won

    def test_get_effective_scores_no_override(self, sample_completed_game):
        """Test get_effective_scores() without override."""
        home_score, away_score = sample_completed_game.get_effective_scores()
        assert home_score == 24
        assert away_score == 17

    def test_get_effective_scores_with_override(self):
        """Test get_effective_scores() with override."""
        game = Game(
            id="401234571",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=True,
            home_score=24,
            away_score=17,
            is_overridden=True,
            override_home_score=30,
            override_away_score=20,
        )
        home_score, away_score = game.get_effective_scores()
        assert home_score == 30
        assert away_score == 20

    def test_get_effective_odds_no_override(self, sample_game):
        """Test get_effective_odds() without override."""
        home_odds, away_odds = sample_game.get_effective_odds()
        assert home_odds == -150
        assert away_odds == 130

    def test_get_effective_odds_with_override(self):
        """Test get_effective_odds() with override."""
        game = Game(
            id="401234572",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=False,
            home_moneyline=-150,
            away_moneyline=130,
            is_overridden=True,
            override_home_moneyline=-200,
            override_away_moneyline=180,
        )
        home_odds, away_odds = game.get_effective_odds()
        assert home_odds == -200
        assert away_odds == 180

    def test_get_winner_with_override(self):
        """Test that overrides affect winner determination."""
        game = Game(
            id="401234573",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=True,
            home_score=24,
            away_score=17,
            is_overridden=True,
            override_home_score=10,
            override_away_score=27,
        )
        # Original: home wins 24-17, but override: away wins 27-10
        assert game.get_winner_id() == "2"


class TestStanding:
    """Tests for Standing model."""

    def test_standing_creation(self, sample_standing):
        """Test Standing object creation."""
        assert sample_standing.team_id == "1"
        assert sample_standing.wins == 10
        assert sample_standing.losses == 5
        assert sample_standing.ties == 2

    def test_win_percentage_calculation(self):
        """Test win_percentage property."""
        # Test 10-5-0 (66.7%)
        standing = Standing(team_id="1", wins=10, losses=5, ties=0)
        assert abs(standing.win_percentage - 0.6667) < 0.001

        # Test 10-5-2 (64.7%)  - ties count as 0.5 wins
        standing = Standing(team_id="1", wins=10, losses=5, ties=2)
        expected = (10 + 0.5 * 2) / (10 + 5 + 2)
        assert abs(standing.win_percentage - expected) < 0.001

        # Test 0-0-0 (0%)
        standing = Standing(team_id="1", wins=0, losses=0, ties=0)
        assert standing.win_percentage == 0.0

    def test_division_win_percentage(self):
        """Test division_win_percentage property."""
        standing = Standing(
            team_id="1", division_wins=4, division_losses=2, division_ties=0
        )
        assert abs(standing.division_win_percentage - 0.6667) < 0.001

    def test_conference_win_percentage(self):
        """Test conference_win_percentage property."""
        standing = Standing(
            team_id="1", conference_wins=7, conference_losses=5, conference_ties=0
        )
        assert abs(standing.conference_win_percentage - 0.5833) < 0.001

    def test_net_points(self, sample_standing):
        """Test net_points property."""
        # 350 - 300 = 50
        assert sample_standing.net_points == 50

    def test_net_points_negative(self):
        """Test negative point differential."""
        standing = Standing(team_id="1", points_for=200, points_against=300)
        assert standing.net_points == -100

    def test_str_representation(self):
        """Test __str__ method."""
        standing = Standing(team_id="1", wins=10, losses=5, ties=2)
        result = str(standing)
        assert "team_id=1" in result
        assert "10-5-2" in result
        assert "pct=" in result
