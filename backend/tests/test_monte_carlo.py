"""
Tests for Monte Carlo simulation engine.
"""

import pytest
from datetime import datetime

from src.simulation.monte_carlo import (
    simulate_season,
    determine_playoff_teams_simple,
    determine_division_winners_simple,
    TeamSimulationStats,
    SimulationResult,
)
from src.data.models import Team, Game


class TestTeamSimulationStats:
    """Tests for TeamSimulationStats data class."""

    def test_playoff_probability(self):
        """Test playoff probability calculation."""
        stats = TeamSimulationStats(
            team_id="1", made_playoffs_count=7500, total_simulations=10000
        )
        assert stats.playoff_probability == 0.75

    def test_playoff_probability_zero_sims(self):
        """Test playoff probability with zero simulations."""
        stats = TeamSimulationStats(
            team_id="1", made_playoffs_count=0, total_simulations=0
        )
        assert stats.playoff_probability == 0.0

    def test_division_win_probability(self):
        """Test division win probability calculation."""
        stats = TeamSimulationStats(
            team_id="1", won_division_count=6000, total_simulations=10000
        )
        assert stats.division_win_probability == 0.6

    def test_average_wins(self):
        """Test average wins calculation."""
        stats = TeamSimulationStats(
            team_id="1", wins_distribution=[10, 11, 12, 10, 11]
        )
        assert stats.average_wins == pytest.approx(10.8)

    def test_average_wins_empty(self):
        """Test average wins with empty distribution."""
        stats = TeamSimulationStats(team_id="1", wins_distribution=[])
        assert stats.average_wins == 0.0

    def test_wins_percentiles(self):
        """Test wins percentiles calculation."""
        # Create distribution with 100 values for easy percentile calculation
        wins = list(range(0, 18)) * 6  # 108 values from 0-17 wins
        stats = TeamSimulationStats(team_id="1", wins_distribution=wins)

        percentiles = stats.wins_percentiles
        assert 10 in percentiles
        assert 25 in percentiles
        assert 50 in percentiles
        assert 75 in percentiles
        assert 90 in percentiles

    def test_wins_percentiles_empty(self):
        """Test wins percentiles with empty distribution."""
        stats = TeamSimulationStats(team_id="1", wins_distribution=[])
        assert stats.wins_percentiles == {}


class TestSimulationResult:
    """Tests for SimulationResult data class."""

    def test_get_team_stats(self):
        """Test retrieving team statistics."""
        stats1 = TeamSimulationStats(team_id="1")
        stats2 = TeamSimulationStats(team_id="2")
        result = SimulationResult(team_stats={"1": stats1, "2": stats2})

        assert result.get_team_stats("1") == stats1
        assert result.get_team_stats("2") == stats2
        assert result.get_team_stats("999") is None

    def test_get_playoff_probabilities(self):
        """Test extracting playoff probabilities."""
        stats1 = TeamSimulationStats(
            team_id="1", made_playoffs_count=8000, total_simulations=10000
        )
        stats2 = TeamSimulationStats(
            team_id="2", made_playoffs_count=3000, total_simulations=10000
        )
        result = SimulationResult(team_stats={"1": stats1, "2": stats2})

        probs = result.get_playoff_probabilities()
        assert probs["1"] == 0.8
        assert probs["2"] == 0.3

    def test_get_division_win_probabilities(self):
        """Test extracting division win probabilities."""
        stats1 = TeamSimulationStats(
            team_id="1", won_division_count=6000, total_simulations=10000
        )
        stats2 = TeamSimulationStats(
            team_id="2", won_division_count=1000, total_simulations=10000
        )
        result = SimulationResult(team_stats={"1": stats1, "2": stats2})

        probs = result.get_division_win_probabilities()
        assert probs["1"] == 0.6
        assert probs["2"] == 0.1

    def test_get_average_wins(self):
        """Test extracting average wins."""
        stats1 = TeamSimulationStats(team_id="1", wins_distribution=[10, 11, 12])
        stats2 = TeamSimulationStats(team_id="2", wins_distribution=[5, 6, 7])
        result = SimulationResult(team_stats={"1": stats1, "2": stats2})

        avg_wins = result.get_average_wins()
        assert avg_wins["1"] == pytest.approx(11.0)
        assert avg_wins["2"] == pytest.approx(6.0)


class TestSimulateSeason:
    """Tests for main simulate_season function."""

    @pytest.fixture
    def sample_teams(self):
        """Create sample teams for testing."""
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
                abbreviation="SF",
                name="San Francisco 49ers",
                display_name="49ers",
                location="San Francisco",
                conference="NFC",
                division="West",
            ),
        ]

    @pytest.fixture
    def sample_games(self):
        """Create sample games for testing."""
        return [
            # Completed game
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
            # Remaining game
            Game(
                id="game2",
                week=2,
                season=2025,
                home_team_id="2",
                away_team_id="1",
                date=datetime(2025, 9, 14, 13, 0),
                is_completed=False,
            ),
        ]

    def test_simulate_season_deterministic(self, sample_teams, sample_games):
        """Test that simulation produces deterministic results with fixed seed."""
        result1 = simulate_season(
            sample_games, sample_teams, num_simulations=100, random_seed=42
        )
        result2 = simulate_season(
            sample_games, sample_teams, num_simulations=100, random_seed=42
        )

        # Should produce identical results
        stats1_team1 = result1.get_team_stats("1")
        stats2_team1 = result2.get_team_stats("1")

        assert stats1_team1.wins_distribution == stats2_team1.wins_distribution

    def test_simulate_season_respects_completed_games(self, sample_teams, sample_games):
        """Test that simulation uses actual results for completed games."""
        result = simulate_season(
            sample_games, sample_teams, num_simulations=100, random_seed=42
        )

        stats_team1 = result.get_team_stats("1")
        stats_team2 = result.get_team_stats("2")

        # Game 1 is completed: Team 1 (home) won 24-17
        # So Team 1 should have at least 1 win in all simulations
        # Team 2 should have at least 1 loss in all simulations
        assert all(wins >= 1 for wins in stats_team1.wins_distribution)

        # Team 2 can have 0 or 1 wins depending on game 2 simulation
        assert all(wins <= 1 for wins in stats_team2.wins_distribution)

    def test_simulate_season_coin_flip_distribution(self, sample_teams):
        """Test that simulated outcomes default to 50/50 coin flips."""
        # Create a single incomplete game
        games = [
            Game(
                id="game1",
                week=1,
                season=2025,
                home_team_id="1",
                away_team_id="2",
                date=datetime(2025, 9, 7, 13, 0),
                is_completed=False,
            )
        ]

        result = simulate_season(
            games, sample_teams, num_simulations=10000, random_seed=42
        )

        stats_team1 = result.get_team_stats("1")

        # Team 1 should win ~50% of simulations (coin flip)
        wins = sum(1 for w in stats_team1.wins_distribution if w == 1)
        win_rate = wins / 10000

        # Allow some statistical variance (~2 standard deviations)
        # Expected: 0.50, stddev ≈ sqrt(0.5*0.5/10000) ≈ 0.005
        # 95% confidence: 0.50 ± 2*0.005 = [0.49, 0.51]
        assert 0.48 < win_rate < 0.52, f"Win rate {win_rate} outside expected range"

    def test_simulate_season_no_remaining_games(self, sample_teams):
        """Test simulation when all games are completed."""
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

        result = simulate_season(games, sample_teams, num_simulations=100)

        stats_team1 = result.get_team_stats("1")
        stats_team2 = result.get_team_stats("2")

        # All simulations should have identical results (1 win each)
        assert all(wins == 1 for wins in stats_team1.wins_distribution)
        assert all(wins == 1 for wins in stats_team2.wins_distribution)

    def test_simulate_season_performance(self, sample_teams):
        """Test that 10,000 simulations complete in reasonable time."""
        # Create a full season worth of games (17 per team, ~272 total for NFL)
        # For testing, use smaller subset (17 games)
        games = []
        start_date = datetime(2025, 9, 7)
        for week in range(1, 18):
            # Use timedelta to properly add days
            from datetime import timedelta

            game_date = start_date + timedelta(days=(week - 1) * 7)
            games.append(
                Game(
                    id=f"game_week{week}",
                    week=week,
                    season=2025,
                    home_team_id="1",
                    away_team_id="2",
                    date=game_date,
                    is_completed=False,
                )
            )

        result = simulate_season(games, sample_teams, num_simulations=10000)

        # Should complete in < 15 seconds (Phase 3 includes tiebreaker calculations)
        # Phase 2 (simple) was ~1 second, Phase 3 (with tiebreakers) is ~10-11 seconds
        # This is expected due to standings calculation and playoff seeding per simulation
        assert result.execution_time_seconds < 15.0

    def test_simulate_season_result_structure(self, sample_teams, sample_games):
        """Test that simulation result has correct structure."""
        result = simulate_season(
            sample_games, sample_teams, num_simulations=100, random_seed=42
        )

        assert result.num_simulations == 100
        assert result.execution_time_seconds > 0
        assert len(result.team_stats) == 2
        assert "1" in result.team_stats
        assert "2" in result.team_stats

        for team_id, stats in result.team_stats.items():
            assert stats.total_simulations == 100
            assert len(stats.wins_distribution) == 100


class TestDeterminePlayoffTeamsSimple:
    """Tests for simple playoff determination (placeholder for Phase 3)."""

    @pytest.fixture
    def nfl_teams(self):
        """Create sample NFL teams."""
        teams = []
        team_id = 1
        for conference in ["AFC", "NFC"]:
            for division in ["North", "South", "East", "West"]:
                for i in range(4):
                    teams.append(
                        Team(
                            id=str(team_id),
                            abbreviation=f"{conference[:1]}{division[:1]}{i+1}",
                            name=f"{conference} {division} Team {i+1}",
                            display_name=f"Team {team_id}",
                            location="City",
                            conference=conference,
                            division=division,
                        )
                    )
                    team_id += 1
        return teams

    def test_determine_playoff_teams_simple(self, nfl_teams):
        """Test simple playoff determination."""
        # Create wins distribution (teams 1-7 AFC, teams 17-23 NFC make playoffs)
        team_wins = {team.id: 10 - int(team.id) for team in nfl_teams}

        playoff_teams = determine_playoff_teams_simple(nfl_teams, team_wins)

        # Should have 14 teams (7 AFC, 7 NFC)
        assert len(playoff_teams) == 14

        # Check that top 7 AFC teams made it
        afc_playoff = [tid for tid in playoff_teams if tid in ["1", "2", "3", "4", "5", "6", "7"]]
        assert len(afc_playoff) == 7

        # Check that top 7 NFC teams made it
        nfc_playoff = [tid for tid in playoff_teams if tid in ["17", "18", "19", "20", "21", "22", "23"]]
        assert len(nfc_playoff) == 7


class TestDetermineDivisionWinnersSimple:
    """Tests for simple division winner determination (placeholder for Phase 3)."""

    @pytest.fixture
    def division_teams(self):
        """Create sample teams in one division."""
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
                abbreviation="LAC",
                name="Los Angeles Chargers",
                display_name="Chargers",
                location="Los Angeles",
                conference="AFC",
                division="West",
            ),
            Team(
                id="3",
                abbreviation="DEN",
                name="Denver Broncos",
                display_name="Broncos",
                location="Denver",
                conference="AFC",
                division="West",
            ),
            Team(
                id="4",
                abbreviation="LV",
                name="Las Vegas Raiders",
                display_name="Raiders",
                location="Las Vegas",
                conference="AFC",
                division="West",
            ),
        ]

    def test_determine_division_winners_simple(self, division_teams):
        """Test simple division winner determination."""
        team_wins = {"1": 12, "2": 10, "3": 8, "4": 6}

        winners = determine_division_winners_simple(division_teams, team_wins)

        assert "AFC_West" in winners
        assert winners["AFC_West"] == "1"  # KC with 12 wins
