"""
Tests for ScheduleLoader.
"""

import pytest
from unittest.mock import Mock, MagicMock

from src.data.schedule_loader import ScheduleLoader
from src.data.models import Team, Game


class TestScheduleLoader:
    """Tests for ScheduleLoader."""

    @pytest.fixture
    def mock_espn_client(self):
        """Create mock ESPN API client."""
        return Mock()

    @pytest.fixture
    def mock_cache_manager(self):
        """Create mock CacheManager."""
        return Mock()

    @pytest.fixture
    def schedule_loader(self, mock_espn_client, mock_cache_manager):
        """Create ScheduleLoader with mocked dependencies."""
        return ScheduleLoader(mock_espn_client, mock_cache_manager)

    # Tests for load_schedule()

    def test_load_schedule_from_cache(
        self, schedule_loader, mock_cache_manager, sample_game
    ):
        """Test loading schedule from cache when valid cache exists."""
        # Setup mocks
        mock_cache_manager.is_schedule_cached.return_value = True
        mock_cache_manager.load_schedule.return_value = [sample_game]

        # Load schedule
        games = schedule_loader.load_schedule(season=2025, force_refresh=False)

        # Verify cache was checked and used
        mock_cache_manager.is_schedule_cached.assert_called_once_with(2025)
        mock_cache_manager.load_schedule.assert_called_once_with(2025)
        assert games == [sample_game]
        assert len(games) == 1

    def test_load_schedule_from_api_when_no_cache(
        self, schedule_loader, mock_espn_client, mock_cache_manager, sample_game
    ):
        """Test fetching schedule from API when no cache exists."""
        # Setup mocks
        mock_cache_manager.is_schedule_cached.return_value = False
        mock_espn_client.fetch_schedule.return_value = [sample_game]

        # Load schedule
        games = schedule_loader.load_schedule(season=2025, force_refresh=False)

        # Verify API was called and result cached
        mock_cache_manager.is_schedule_cached.assert_called_once_with(2025)
        mock_espn_client.fetch_schedule.assert_called_once_with(2025)
        mock_cache_manager.save_schedule.assert_called_once_with([sample_game], 2025)
        assert games == [sample_game]

    def test_load_schedule_force_refresh(
        self, schedule_loader, mock_espn_client, mock_cache_manager, sample_game
    ):
        """Test force refresh bypasses cache."""
        # Setup mocks
        mock_cache_manager.is_schedule_cached.return_value = True
        mock_espn_client.fetch_schedule.return_value = [sample_game]

        # Load schedule with force_refresh=True
        games = schedule_loader.load_schedule(season=2025, force_refresh=True)

        # Verify cache was NOT checked, API was called directly
        mock_cache_manager.is_schedule_cached.assert_not_called()
        mock_espn_client.fetch_schedule.assert_called_once_with(2025)
        mock_cache_manager.save_schedule.assert_called_once_with([sample_game], 2025)
        assert games == [sample_game]

    def test_load_schedule_cache_returns_none(
        self, schedule_loader, mock_espn_client, mock_cache_manager, sample_game
    ):
        """Test fallback to API when cache returns None."""
        # Setup mocks - cache exists but returns None (corrupted?)
        mock_cache_manager.is_schedule_cached.return_value = True
        mock_cache_manager.load_schedule.return_value = None
        mock_espn_client.fetch_schedule.return_value = [sample_game]

        # Load schedule
        games = schedule_loader.load_schedule(season=2025, force_refresh=False)

        # Verify API was called as fallback
        mock_espn_client.fetch_schedule.assert_called_once_with(2025)
        mock_cache_manager.save_schedule.assert_called_once_with([sample_game], 2025)
        assert games == [sample_game]

    def test_load_schedule_api_returns_empty(
        self, schedule_loader, mock_espn_client, mock_cache_manager
    ):
        """Test handling of empty schedule from API."""
        # Setup mocks
        mock_cache_manager.is_schedule_cached.return_value = False
        mock_espn_client.fetch_schedule.return_value = []

        # Load schedule
        games = schedule_loader.load_schedule(season=2025, force_refresh=False)

        # Verify empty result is handled gracefully
        mock_espn_client.fetch_schedule.assert_called_once_with(2025)
        mock_cache_manager.save_schedule.assert_not_called()  # Don't cache empty
        assert games == []

    # Tests for load_teams()

    def test_load_teams_from_cache(
        self, schedule_loader, mock_cache_manager, sample_team, sample_team_2
    ):
        """Test loading teams from cache when available."""
        # Setup mocks
        teams = [sample_team, sample_team_2]
        mock_cache_manager.load_teams.return_value = teams

        # Load teams
        result = schedule_loader.load_teams(force_refresh=False)

        # Verify cache was used
        mock_cache_manager.load_teams.assert_called_once()
        assert result == teams
        assert len(result) == 2

    def test_load_teams_from_api_when_no_cache(
        self, schedule_loader, mock_espn_client, mock_cache_manager, sample_team
    ):
        """Test fetching teams from API when no cache exists."""
        # Setup mocks
        mock_cache_manager.load_teams.return_value = None
        mock_espn_client.fetch_teams.return_value = [sample_team]

        # Load teams
        teams = schedule_loader.load_teams(force_refresh=False)

        # Verify API was called and result cached
        mock_cache_manager.load_teams.assert_called_once()
        mock_espn_client.fetch_teams.assert_called_once()
        mock_cache_manager.save_teams.assert_called_once_with([sample_team])
        assert teams == [sample_team]

    def test_load_teams_force_refresh(
        self, schedule_loader, mock_espn_client, mock_cache_manager, sample_team
    ):
        """Test force refresh bypasses cache for teams."""
        # Setup mocks
        mock_espn_client.fetch_teams.return_value = [sample_team]

        # Load teams with force_refresh=True
        teams = schedule_loader.load_teams(force_refresh=True)

        # Verify cache was NOT checked
        mock_cache_manager.load_teams.assert_not_called()
        mock_espn_client.fetch_teams.assert_called_once()
        mock_cache_manager.save_teams.assert_called_once_with([sample_team])
        assert teams == [sample_team]

    def test_load_teams_api_returns_empty(
        self, schedule_loader, mock_espn_client, mock_cache_manager
    ):
        """Test handling of empty teams from API."""
        # Setup mocks
        mock_cache_manager.load_teams.return_value = None
        mock_espn_client.fetch_teams.return_value = []

        # Load teams
        teams = schedule_loader.load_teams(force_refresh=False)

        # Verify empty result is handled
        mock_espn_client.fetch_teams.assert_called_once()
        mock_cache_manager.save_teams.assert_not_called()  # Don't cache empty
        assert teams == []

    # Tests for update_results()

    def test_update_results_with_week(
        self, schedule_loader, mock_espn_client, mock_cache_manager, sample_completed_game
    ):
        """Test updating results for specific week."""
        # Setup mocks
        mock_espn_client.fetch_scoreboard.return_value = [sample_completed_game]

        # Update results
        games = schedule_loader.update_results(week=1)

        # Verify scoreboard was fetched and cached
        mock_espn_client.fetch_scoreboard.assert_called_once_with(1)
        mock_cache_manager.save_results.assert_called_once_with([sample_completed_game])
        assert games == [sample_completed_game]

    def test_update_results_current_week(
        self, schedule_loader, mock_espn_client, mock_cache_manager, sample_completed_game
    ):
        """Test updating results for current week (no week specified)."""
        # Setup mocks
        mock_espn_client.fetch_scoreboard.return_value = [sample_completed_game]

        # Update results without week
        games = schedule_loader.update_results(week=None)

        # Verify scoreboard was fetched with None (current week)
        mock_espn_client.fetch_scoreboard.assert_called_once_with(None)
        mock_cache_manager.save_results.assert_called_once_with([sample_completed_game])
        assert games == [sample_completed_game]

    def test_update_results_no_games(
        self, schedule_loader, mock_espn_client, mock_cache_manager
    ):
        """Test handling of no game results."""
        # Setup mocks
        mock_espn_client.fetch_scoreboard.return_value = []

        # Update results
        games = schedule_loader.update_results(week=1)

        # Verify empty result is handled
        mock_espn_client.fetch_scoreboard.assert_called_once_with(1)
        mock_cache_manager.save_results.assert_not_called()  # Don't cache empty
        assert games == []

    # Tests for get_cached_results()

    def test_get_cached_results_exists(
        self, schedule_loader, mock_cache_manager, sample_completed_game
    ):
        """Test getting cached results when they exist."""
        # Setup mocks
        mock_cache_manager.load_results.return_value = [sample_completed_game]

        # Get cached results
        games = schedule_loader.get_cached_results()

        # Verify results were loaded from cache
        mock_cache_manager.load_results.assert_called_once()
        assert games == [sample_completed_game]

    def test_get_cached_results_not_exists(
        self, schedule_loader, mock_cache_manager
    ):
        """Test getting cached results when none exist."""
        # Setup mocks
        mock_cache_manager.load_results.return_value = None

        # Get cached results
        games = schedule_loader.get_cached_results()

        # Verify None is returned
        mock_cache_manager.load_results.assert_called_once()
        assert games is None

    # Tests for clear_all_cache()

    def test_clear_all_cache(self, schedule_loader, mock_cache_manager):
        """Test clearing all cache."""
        # Clear cache
        schedule_loader.clear_all_cache()

        # Verify cache manager's clear was called
        mock_cache_manager.clear_cache.assert_called_once()

    # Tests for get_cache_status()

    def test_get_cache_status(self, schedule_loader, mock_cache_manager):
        """Test getting cache status."""
        # Setup mock
        expected_status = {
            "schedule": {"exists": True, "age_seconds": 1234},
            "results": {"exists": False, "age_seconds": None},
        }
        mock_cache_manager.get_cache_info.return_value = expected_status

        # Get status
        status = schedule_loader.get_cache_status()

        # Verify status was retrieved
        mock_cache_manager.get_cache_info.assert_called_once()
        assert status == expected_status
