"""
Tests for standings calculator.
"""

import pytest
from datetime import datetime

from src.simulation.standings import (
    calculate_standings,
    update_standing_from_game,
    is_division_game,
    is_conference_game,
    sort_standings_simple,
    get_division_standings,
    get_conference_standings,
)
from src.data.models import Team, Game, Standing


class TestIsDivisionGame:
    """Tests for division game detection."""

    def test_same_division(self):
        """Test teams in same division."""
        team1 = Team(
            id="1",
            abbreviation="KC",
            name="Kansas City Chiefs",
            display_name="Chiefs",
            location="Kansas City",
            conference="AFC",
            division="West",
        )
        team2 = Team(
            id="2",
            abbreviation="LV",
            name="Las Vegas Raiders",
            display_name="Raiders",
            location="Las Vegas",
            conference="AFC",
            division="West",
        )

        assert is_division_game(team1, team2) is True

    def test_different_division_same_conference(self):
        """Test teams in same conference but different divisions."""
        team1 = Team(
            id="1",
            abbreviation="KC",
            name="Kansas City Chiefs",
            display_name="Chiefs",
            location="Kansas City",
            conference="AFC",
            division="West",
        )
        team2 = Team(
            id="2",
            abbreviation="BAL",
            name="Baltimore Ravens",
            display_name="Ravens",
            location="Baltimore",
            conference="AFC",
            division="North",
        )

        assert is_division_game(team1, team2) is False

    def test_different_conference(self):
        """Test teams in different conferences."""
        team1 = Team(
            id="1",
            abbreviation="KC",
            name="Kansas City Chiefs",
            display_name="Chiefs",
            location="Kansas City",
            conference="AFC",
            division="West",
        )
        team2 = Team(
            id="2",
            abbreviation="SF",
            name="San Francisco 49ers",
            display_name="49ers",
            location="San Francisco",
            conference="NFC",
            division="West",
        )

        assert is_division_game(team1, team2) is False


class TestIsConferenceGame:
    """Tests for conference game detection."""

    def test_same_conference_same_division(self):
        """Test teams in same conference and division."""
        team1 = Team(
            id="1",
            abbreviation="KC",
            name="Kansas City Chiefs",
            display_name="Chiefs",
            location="Kansas City",
            conference="AFC",
            division="West",
        )
        team2 = Team(
            id="2",
            abbreviation="LV",
            name="Las Vegas Raiders",
            display_name="Raiders",
            location="Las Vegas",
            conference="AFC",
            division="West",
        )

        assert is_conference_game(team1, team2) is True

    def test_same_conference_different_division(self):
        """Test teams in same conference but different divisions."""
        team1 = Team(
            id="1",
            abbreviation="KC",
            name="Kansas City Chiefs",
            display_name="Chiefs",
            location="Kansas City",
            conference="AFC",
            division="West",
        )
        team2 = Team(
            id="2",
            abbreviation="BAL",
            name="Baltimore Ravens",
            display_name="Ravens",
            location="Baltimore",
            conference="AFC",
            division="North",
        )

        assert is_conference_game(team1, team2) is True

    def test_different_conference(self):
        """Test teams in different conferences."""
        team1 = Team(
            id="1",
            abbreviation="KC",
            name="Kansas City Chiefs",
            display_name="Chiefs",
            location="Kansas City",
            conference="AFC",
            division="West",
        )
        team2 = Team(
            id="2",
            abbreviation="SF",
            name="San Francisco 49ers",
            display_name="49ers",
            location="San Francisco",
            conference="NFC",
            division="West",
        )

        assert is_conference_game(team1, team2) is False


class TestUpdateStandingFromGame:
    """Tests for updating standings from game results."""

    @pytest.fixture
    def sample_teams(self):
        """Create sample teams."""
        team1 = Team(
            id="1",
            abbreviation="KC",
            name="Kansas City Chiefs",
            display_name="Chiefs",
            location="Kansas City",
            conference="AFC",
            division="West",
        )
        team2 = Team(
            id="2",
            abbreviation="LV",
            name="Las Vegas Raiders",
            display_name="Raiders",
            location="Las Vegas",
            conference="AFC",
            division="West",
        )
        return team1, team2

    def test_update_home_win(self, sample_teams):
        """Test standings update when home team wins."""
        team1, team2 = sample_teams
        standing1 = Standing(team_id="1")
        standing2 = Standing(team_id="2")

        game = Game(
            id="game1",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=True,
            home_score=24,
            away_score=17,
        )

        update_standing_from_game(standing1, standing2, game, team1, team2)

        assert standing1.wins == 1
        assert standing1.losses == 0
        assert standing2.wins == 0
        assert standing2.losses == 1

    def test_update_away_win(self, sample_teams):
        """Test standings update when away team wins."""
        team1, team2 = sample_teams
        standing1 = Standing(team_id="1")
        standing2 = Standing(team_id="2")

        game = Game(
            id="game1",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=True,
            home_score=17,
            away_score=24,
        )

        update_standing_from_game(standing1, standing2, game, team1, team2)

        assert standing1.wins == 0
        assert standing1.losses == 1
        assert standing2.wins == 1
        assert standing2.losses == 0

    def test_update_tie(self, sample_teams):
        """Test standings update for tie game."""
        team1, team2 = sample_teams
        standing1 = Standing(team_id="1")
        standing2 = Standing(team_id="2")

        game = Game(
            id="game1",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=True,
            home_score=21,
            away_score=21,
        )

        update_standing_from_game(standing1, standing2, game, team1, team2)

        assert standing1.ties == 1
        assert standing2.ties == 1
        assert standing1.wins == 0
        assert standing2.wins == 0

    def test_update_division_game(self, sample_teams):
        """Test division record updates for division game."""
        team1, team2 = sample_teams  # Same division
        standing1 = Standing(team_id="1")
        standing2 = Standing(team_id="2")

        game = Game(
            id="game1",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=True,
            home_score=24,
            away_score=17,
        )

        update_standing_from_game(standing1, standing2, game, team1, team2)

        assert standing1.division_wins == 1
        assert standing2.division_losses == 1

    def test_update_conference_game(self, sample_teams):
        """Test conference record updates for conference game."""
        team1, team2 = sample_teams  # Same conference
        standing1 = Standing(team_id="1")
        standing2 = Standing(team_id="2")

        game = Game(
            id="game1",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=True,
            home_score=24,
            away_score=17,
        )

        update_standing_from_game(standing1, standing2, game, team1, team2)

        assert standing1.conference_wins == 1
        assert standing2.conference_losses == 1

    def test_update_points(self, sample_teams):
        """Test points for/against updates."""
        team1, team2 = sample_teams
        standing1 = Standing(team_id="1")
        standing2 = Standing(team_id="2")

        game = Game(
            id="game1",
            week=1,
            season=2025,
            home_team_id="1",
            away_team_id="2",
            date=datetime(2025, 9, 7, 13, 0),
            is_completed=True,
            home_score=24,
            away_score=17,
        )

        update_standing_from_game(standing1, standing2, game, team1, team2)

        assert standing1.points_for == 24
        assert standing1.points_against == 17
        assert standing2.points_for == 17
        assert standing2.points_against == 24


class TestCalculateStandings:
    """Tests for calculating standings from games."""

    @pytest.fixture
    def sample_teams(self):
        """Create sample teams."""
        return [
            Team(
                id="1",
                abbreviation="KC",
                name="Kansas City Chiefs",
                display_name="Chiefs",
                location="Kansas City",
                conference="AFC",
                division="West",
            ),
            Team(
                id="2",
                abbreviation="LV",
                name="Las Vegas Raiders",
                display_name="Raiders",
                location="Las Vegas",
                conference="AFC",
                division="West",
            ),
        ]

    def test_calculate_standings_simple(self, sample_teams):
        """Test calculating standings from completed games."""
        games = [
            Game(
                id="game1",
                week=1,
                season=2025,
                home_team_id="1",
                away_team_id="2",
                date=datetime(2025, 9, 7, 13, 0),
                is_completed=True,
                home_score=24,
                away_score=17,
            ),
            Game(
                id="game2",
                week=2,
                season=2025,
                home_team_id="2",
                away_team_id="1",
                date=datetime(2025, 9, 14, 13, 0),
                is_completed=True,
                home_score=21,
                away_score=20,
            ),
        ]

        standings = calculate_standings(games, sample_teams)

        # Team 1: 1-1 (won game1, lost game2)
        assert standings["1"].wins == 1
        assert standings["1"].losses == 1

        # Team 2: 1-1 (lost game1, won game2)
        assert standings["2"].wins == 1
        assert standings["2"].losses == 1

    def test_calculate_standings_all_teams_initialized(self, sample_teams):
        """Test that all teams get initialized standings even with no games."""
        games = []

        standings = calculate_standings(games, sample_teams)

        assert len(standings) == 2
        assert "1" in standings
        assert "2" in standings
        assert standings["1"].wins == 0
        assert standings["2"].wins == 0

    def test_calculate_standings_skips_incomplete_games(self, sample_teams):
        """Test that incomplete games without winners are skipped."""
        games = [
            Game(
                id="game1",
                week=1,
                season=2025,
                home_team_id="1",
                away_team_id="2",
                date=datetime(2025, 9, 7, 13, 0),
                is_completed=False,  # Not completed
            )
        ]

        standings = calculate_standings(games, sample_teams)

        # No wins/losses since game not completed
        assert standings["1"].wins == 0
        assert standings["2"].wins == 0


class TestSortStandingsSimple:
    """Tests for simple standings sorting."""

    def test_sort_by_win_percentage(self):
        """Test sorting standings by win percentage."""
        standings = [
            Standing(team_id="1", wins=10, losses=7),  # 58.8%
            Standing(team_id="2", wins=13, losses=4),  # 76.5%
            Standing(team_id="3", wins=8, losses=9),  # 47.1%
        ]

        sorted_standings = sort_standings_simple(standings)

        assert sorted_standings[0].team_id == "2"  # 13-4 (best)
        assert sorted_standings[1].team_id == "1"  # 10-7
        assert sorted_standings[2].team_id == "3"  # 8-9 (worst)

    def test_sort_with_ties(self):
        """Test sorting with tie games."""
        standings = [
            Standing(team_id="1", wins=10, losses=6, ties=1),  # 61.8%
            Standing(team_id="2", wins=10, losses=7, ties=0),  # 58.8%
        ]

        sorted_standings = sort_standings_simple(standings)

        # Team with tie has higher win percentage
        assert sorted_standings[0].team_id == "1"
        assert sorted_standings[1].team_id == "2"

    def test_sort_identical_records(self):
        """Test sorting with identical records (no tiebreaker in Phase 2)."""
        standings = [
            Standing(team_id="1", wins=10, losses=7),
            Standing(team_id="2", wins=10, losses=7),
        ]

        sorted_standings = sort_standings_simple(standings)

        # Both have same win%, order preserved (stable sort)
        assert len(sorted_standings) == 2
        # No specific order guaranteed without tiebreakers


class TestGetDivisionStandings:
    """Tests for getting division-specific standings."""

    @pytest.fixture
    def afc_west_teams(self):
        """Create AFC West teams."""
        return [
            Team(
                id="1",
                abbreviation="KC",
                name="Kansas City Chiefs",
                display_name="Chiefs",
                location="Kansas City",
                conference="AFC",
                division="West",
            ),
            Team(
                id="2",
                abbreviation="LV",
                name="Las Vegas Raiders",
                display_name="Raiders",
                location="Las Vegas",
                conference="AFC",
                division="West",
            ),
            Team(
                id="3",
                abbreviation="LAC",
                name="Los Angeles Chargers",
                display_name="Chargers",
                location="Los Angeles",
                conference="AFC",
                division="West",
            ),
            Team(
                id="4",
                abbreviation="DEN",
                name="Denver Broncos",
                display_name="Broncos",
                location="Denver",
                conference="AFC",
                division="West",
            ),
        ]

    def test_get_division_standings(self, afc_west_teams):
        """Test getting standings for a specific division."""
        standings_dict = {
            "1": Standing(team_id="1", wins=12, losses=5),
            "2": Standing(team_id="2", wins=9, losses=8),
            "3": Standing(team_id="3", wins=11, losses=6),
            "4": Standing(team_id="4", wins=6, losses=11),
        }

        afc_west = get_division_standings(
            standings_dict, afc_west_teams, "AFC", "West"
        )

        assert len(afc_west) == 4
        assert afc_west[0].team_id == "1"  # KC 12-5
        assert afc_west[1].team_id == "3"  # LAC 11-6
        assert afc_west[2].team_id == "2"  # LV 9-8
        assert afc_west[3].team_id == "4"  # DEN 6-11


class TestGetConferenceStandings:
    """Tests for getting conference-specific standings."""

    @pytest.fixture
    def afc_teams(self):
        """Create sample AFC teams."""
        return [
            Team(
                id="1",
                abbreviation="KC",
                name="Kansas City Chiefs",
                display_name="Chiefs",
                location="Kansas City",
                conference="AFC",
                division="West",
            ),
            Team(
                id="2",
                abbreviation="BAL",
                name="Baltimore Ravens",
                display_name="Ravens",
                location="Baltimore",
                conference="AFC",
                division="North",
            ),
            Team(
                id="3",
                abbreviation="BUF",
                name="Buffalo Bills",
                display_name="Bills",
                location="Buffalo",
                conference="AFC",
                division="East",
            ),
        ]

    def test_get_conference_standings(self, afc_teams):
        """Test getting standings for a specific conference."""
        standings_dict = {
            "1": Standing(team_id="1", wins=12, losses=5),
            "2": Standing(team_id="2", wins=13, losses=4),
            "3": Standing(team_id="3", wins=11, losses=6),
        }

        afc = get_conference_standings(standings_dict, afc_teams, "AFC")

        assert len(afc) == 3
        assert afc[0].team_id == "2"  # BAL 13-4
        assert afc[1].team_id == "1"  # KC 12-5
        assert afc[2].team_id == "3"  # BUF 11-6
