"""
Tests for CacheManager.
"""

import pytest
import time
from datetime import datetime

from src.data.cache_manager import CacheManager
from src.data.models import Team, Game


class TestCacheManager:
    """Tests for CacheManager."""

    def test_initialization(self, temp_cache_dir):
        """Test CacheManager initialization creates cache directory."""
        cache = CacheManager(temp_cache_dir)
        assert temp_cache_dir.exists()
        assert cache.cache_dir == temp_cache_dir

    def test_save_and_load_schedule(self, cache_manager, sample_game):
        """Test saving and loading schedule."""
        games = [sample_game]
        cache_manager.save_schedule(games, season=2025)

        loaded_games = cache_manager.load_schedule(season=2025)
        assert loaded_games is not None
        assert len(loaded_games) == 1
        assert loaded_games[0].id == sample_game.id

    def test_is_schedule_cached_when_not_exists(self, cache_manager):
        """Test is_schedule_cached() returns False when no cache."""
        assert cache_manager.is_schedule_cached(season=2025) is False

    def test_is_schedule_cached_when_exists(self, cache_manager, sample_game):
        """Test is_schedule_cached() returns True when cache exists."""
        cache_manager.save_schedule([sample_game], season=2025)
        assert cache_manager.is_schedule_cached(season=2025) is True

    def test_is_schedule_cached_when_too_old(self, cache_manager, sample_game):
        """Test cache invalidation based on age."""
        # Save schedule
        cache_manager.save_schedule([sample_game], season=2025)

        # Wait for cache to age
        time.sleep(0.002)

        # Check with very short max age
        assert cache_manager.is_schedule_cached(season=2025, max_age_seconds=0.001) is False

    def test_save_and_load_teams(self, cache_manager, sample_team, sample_team_2):
        """Test saving and loading teams."""
        teams = [sample_team, sample_team_2]
        cache_manager.save_teams(teams)

        loaded_teams = cache_manager.load_teams()
        assert loaded_teams is not None
        assert len(loaded_teams) == 2
        assert loaded_teams[0].id == sample_team.id
        assert loaded_teams[1].id == sample_team_2.id

    def test_save_and_load_results(self, cache_manager, sample_completed_game):
        """Test saving and loading game results."""
        games = [sample_completed_game]
        cache_manager.save_results(games)

        loaded_games = cache_manager.load_results()
        assert loaded_games is not None
        assert len(loaded_games) == 1
        assert loaded_games[0].home_score == 24
        assert loaded_games[0].away_score == 17

    def test_save_and_load_overrides(self, cache_manager):
        """Test user overrides persistence."""
        overrides = {"game_123": {"home_score": 30, "away_score": 20}}
        cache_manager.save_overrides(overrides)

        loaded_overrides = cache_manager.load_overrides()
        assert loaded_overrides == overrides

    def test_load_overrides_when_not_exists(self, cache_manager):
        """Test load_overrides() returns empty dict when no file."""
        overrides = cache_manager.load_overrides()
        assert overrides == {}

    def test_clear_cache_specific_type(self, cache_manager, sample_game, sample_team):
        """Test clearing specific cache type."""
        # Create multiple caches
        cache_manager.save_schedule([sample_game], season=2025)
        cache_manager.save_teams([sample_team])
        cache_manager.save_results([sample_game])

        # Clear only schedule
        cache_manager.clear_cache("schedule")

        # Schedule should be gone, others remain
        assert cache_manager.load_schedule(season=2025) is None
        assert cache_manager.load_teams() is not None
        assert cache_manager.load_results() is not None

    def test_clear_cache_all(self, cache_manager, sample_game, sample_team):
        """Test clearing all caches (except overrides)."""
        # Create all caches
        cache_manager.save_schedule([sample_game], season=2025)
        cache_manager.save_teams([sample_team])
        cache_manager.save_results([sample_game])
        cache_manager.save_overrides({"test": "data"})

        # Clear all
        cache_manager.clear_cache()

        # All should be gone except overrides
        assert cache_manager.load_schedule(season=2025) is None
        assert cache_manager.load_teams() is None
        assert cache_manager.load_results() is None
        assert cache_manager.load_overrides() == {"test": "data"}

    def test_get_cache_info(self, cache_manager, sample_game):
        """Test cache info retrieval."""
        # Initially all should not exist
        info = cache_manager.get_cache_info()
        assert info["schedule"]["exists"] is False
        assert info["results"]["exists"] is False
        assert info["teams"]["exists"] is False

        # Save schedule
        cache_manager.save_schedule([sample_game], season=2025)

        info = cache_manager.get_cache_info()
        assert info["schedule"]["exists"] is True
        assert info["schedule"]["age_seconds"] is not None
        assert info["schedule"]["age_seconds"] < 5  # Should be very recent

    def test_serialize_deserialize_game_roundtrip(
        self, cache_manager, sample_game, sample_completed_game
    ):
        """Test Game serialization round-trip."""
        # Test incomplete game
        serialized = cache_manager._serialize_game(sample_game)
        deserialized = cache_manager._deserialize_game(serialized)

        assert deserialized.id == sample_game.id
        assert deserialized.week == sample_game.week
        assert deserialized.is_completed == sample_game.is_completed

        # Test completed game
        serialized = cache_manager._serialize_game(sample_completed_game)
        deserialized = cache_manager._deserialize_game(serialized)

        assert deserialized.home_score == sample_completed_game.home_score
        assert deserialized.away_score == sample_completed_game.away_score

    def test_serialize_deserialize_team_roundtrip(self, cache_manager, sample_team):
        """Test Team serialization round-trip."""
        serialized = cache_manager._serialize_team(sample_team)
        deserialized = cache_manager._deserialize_team(serialized)

        assert deserialized.id == sample_team.id
        assert deserialized.name == sample_team.name
        assert deserialized.conference == sample_team.conference
        assert deserialized.color == sample_team.color

    def test_game_with_overrides_serialization(self, cache_manager):
        """Test serialization of game with overrides."""
        game = Game(
            id="401234567",
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

        serialized = cache_manager._serialize_game(game)
        deserialized = cache_manager._deserialize_game(serialized)

        assert deserialized.is_overridden is True
        assert deserialized.override_home_score == 30
        assert deserialized.override_away_score == 20

    def test_clear_cache_invalid_type(self, cache_manager):
        """Test clear_cache() raises error for invalid type."""
        with pytest.raises(ValueError, match="Invalid cache type"):
            cache_manager.clear_cache("invalid_type")
