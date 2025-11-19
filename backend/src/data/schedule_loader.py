"""
High-level interface for loading NFL schedule with automatic caching.

Combines ESPN API and cache manager for seamless data loading.
"""

from typing import Optional

from ..utils.logger import setup_logger
from .cache_manager import CacheManager
from .espn_api import ESPNAPIClient
from .models import Game, Team


class ScheduleLoader:
    """High-level interface for loading NFL schedule."""

    def __init__(self, espn_client: ESPNAPIClient, cache_manager: CacheManager):
        """
        Initialize schedule loader.

        Args:
            espn_client: ESPN API client
            cache_manager: Cache manager
        """
        self.espn_client = espn_client
        self.cache_manager = cache_manager
        self.logger = setup_logger(__name__)

    def load_schedule(
        self, season: int = 2025, force_refresh: bool = False
    ) -> list[Game]:
        """
        Load NFL schedule from cache or API.

        Args:
            season: Season year
            force_refresh: If True, bypass cache and fetch from API

        Returns:
            List of Game objects

        Logic:
            1. If force_refresh is False and valid cache exists, return cached data
            2. Otherwise, fetch from ESPN API
            3. Save to cache
            4. Return games
        """
        if not force_refresh and self.cache_manager.is_schedule_cached(season):
            self.logger.info(f"Loading {season} schedule from cache")
            cached_schedule = self.cache_manager.load_schedule(season)
            if cached_schedule:
                return cached_schedule

        self.logger.info(f"Fetching {season} schedule from ESPN API")
        games = self.espn_client.fetch_schedule(season)

        if games:
            self.logger.info(f"Saving {len(games)} games to cache")
            self.cache_manager.save_schedule(games, season)
        else:
            self.logger.warning(f"No games found for {season} season")

        return games

    def load_teams(self, force_refresh: bool = False) -> list[Team]:
        """
        Load all NFL teams from cache or API.

        Args:
            force_refresh: If True, bypass cache and fetch from API

        Returns:
            List of Team objects (32 teams)
        """
        if not force_refresh:
            cached_teams = self.cache_manager.load_teams()
            if cached_teams:
                self.logger.info("Loading teams from cache")
                return cached_teams

        self.logger.info("Fetching teams from ESPN API")
        teams = self.espn_client.fetch_teams()

        if teams:
            self.logger.info(f"Saving {len(teams)} teams to cache")
            self.cache_manager.save_teams(teams)
        else:
            self.logger.warning("No teams found")

        return teams

    def update_results(self, week: Optional[int] = None) -> list[Game]:
        """
        Update game results from ESPN scoreboard.

        Args:
            week: Optional week number (if None, gets current week)

        Returns:
            List of updated Game objects
        """
        self.logger.info(f"Fetching game results for week {week or 'current'}")
        updated_games = self.espn_client.fetch_scoreboard(week)

        if updated_games:
            self.cache_manager.save_results(updated_games)
            self.logger.info(f"Updated results for {len(updated_games)} games")
        else:
            self.logger.info("No game results to update")

        return updated_games

    def get_cached_results(self) -> Optional[list[Game]]:
        """
        Get cached game results without fetching from API.

        Returns:
            List of Game objects or None if no cached results
        """
        return self.cache_manager.load_results()

    def clear_all_cache(self) -> None:
        """Clear all cached data (except user overrides)."""
        self.logger.info("Clearing all cache")
        self.cache_manager.clear_cache()

    def get_cache_status(self) -> dict:
        """
        Get status of all caches.

        Returns:
            Dictionary with cache information
        """
        return self.cache_manager.get_cache_info()
