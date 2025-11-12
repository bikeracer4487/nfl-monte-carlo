"""
Cache manager for storing and retrieving API data locally.

Minimizes API calls by caching schedule, results, odds, and teams data.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..utils.logger import setup_logger
from .models import Team, Game


class CacheManager:
    """Manages local caching of API data."""

    def __init__(self, cache_dir: Path | str):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logger(__name__)

        # Cache file paths
        self.schedule_cache = self.cache_dir / "schedule_{season}.json"
        self.results_cache = self.cache_dir / "results_current.json"
        self.odds_cache = self.cache_dir / "odds_current.json"
        self.teams_cache = self.cache_dir / "teams.json"
        self.overrides_cache = self.cache_dir / "user_overrides.json"

    # Schedule caching
    def save_schedule(self, games: list[Game], season: int = 2025) -> None:
        """
        Save schedule to cache.

        Args:
            games: List of Game objects
            season: Season year
        """
        filepath = Path(str(self.schedule_cache).format(season=season))
        data = {
            "season": season,
            "cached_at": datetime.now().isoformat(),
            "game_count": len(games),
            "games": [self._serialize_game(game) for game in games],
        }

        self._write_json(filepath, data)
        self.logger.info(f"Saved {len(games)} games to schedule cache")

    def load_schedule(self, season: int = 2025) -> Optional[list[Game]]:
        """
        Load schedule from cache if available and valid.

        Args:
            season: Season year

        Returns:
            List of Game objects or None if cache invalid/missing
        """
        filepath = Path(str(self.schedule_cache).format(season=season))

        if not filepath.exists():
            return None

        data = self._read_json(filepath)
        if not data:
            return None

        try:
            games = [self._deserialize_game(g) for g in data.get("games", [])]
            self.logger.info(
                f"Loaded {len(games)} games from schedule cache (season {season})"
            )
            return games
        except Exception as e:
            self.logger.error(f"Failed to deserialize schedule: {e}")
            return None

    def is_schedule_cached(
        self, season: int = 2025, max_age_seconds: int = 86400
    ) -> bool:
        """
        Check if valid cached schedule exists.

        Args:
            season: Season year
            max_age_seconds: Maximum age in seconds (default: 24 hours)

        Returns:
            True if valid cache exists
        """
        filepath = Path(str(self.schedule_cache).format(season=season))
        return self._is_cache_valid(filepath, max_age_seconds)

    # Results caching
    def save_results(self, games: list[Game]) -> None:
        """
        Save game results to cache.

        Args:
            games: List of Game objects with results
        """
        data = {
            "cached_at": datetime.now().isoformat(),
            "game_count": len(games),
            "games": [self._serialize_game(game) for game in games],
        }

        self._write_json(self.results_cache, data)
        self.logger.info(f"Saved {len(games)} game results to cache")

    def load_results(self) -> Optional[list[Game]]:
        """
        Load game results from cache.

        Returns:
            List of Game objects or None if cache invalid/missing
        """
        if not self.results_cache.exists():
            return None

        data = self._read_json(self.results_cache)
        if not data:
            return None

        try:
            games = [self._deserialize_game(g) for g in data.get("games", [])]
            self.logger.info(f"Loaded {len(games)} game results from cache")
            return games
        except Exception as e:
            self.logger.error(f"Failed to deserialize results: {e}")
            return None

    def is_results_cached(self, max_age_seconds: int = 3600) -> bool:
        """
        Check if valid cached results exist.

        Args:
            max_age_seconds: Maximum age in seconds (default: 1 hour)

        Returns:
            True if valid cache exists
        """
        return self._is_cache_valid(self.results_cache, max_age_seconds)

    # Odds caching
    def save_odds(self, odds_data: dict) -> None:
        """
        Save odds data to cache.

        Args:
            odds_data: Dictionary of odds from OddsAPIClient
        """
        data = {
            "cached_at": datetime.now().isoformat(),
            "game_count": len(odds_data),
            "odds": odds_data,
        }

        self._write_json(self.odds_cache, data)
        self.logger.info(f"Saved odds for {len(odds_data)} games to cache")

    def load_odds(self) -> Optional[dict]:
        """
        Load odds from cache.

        Returns:
            Dictionary of odds or None if cache invalid/missing
        """
        if not self.odds_cache.exists():
            return None

        data = self._read_json(self.odds_cache)
        if not data:
            return None

        odds = data.get("odds", {})
        self.logger.info(f"Loaded odds for {len(odds)} games from cache")
        return odds

    def is_odds_cached(self, max_age_seconds: int = 3600) -> bool:
        """
        Check if valid cached odds exist.

        Args:
            max_age_seconds: Maximum age in seconds (default: 1 hour)

        Returns:
            True if valid cache exists
        """
        return self._is_cache_valid(self.odds_cache, max_age_seconds)

    # Teams caching
    def save_teams(self, teams: list[Team]) -> None:
        """
        Save teams to cache.

        Args:
            teams: List of Team objects
        """
        data = {
            "cached_at": datetime.now().isoformat(),
            "team_count": len(teams),
            "teams": [self._serialize_team(team) for team in teams],
        }

        self._write_json(self.teams_cache, data)
        self.logger.info(f"Saved {len(teams)} teams to cache")

    def load_teams(self) -> Optional[list[Team]]:
        """
        Load teams from cache.

        Returns:
            List of Team objects or None if cache invalid/missing
        """
        if not self.teams_cache.exists():
            return None

        data = self._read_json(self.teams_cache)
        if not data:
            return None

        try:
            teams = [self._deserialize_team(t) for t in data.get("teams", [])]
            self.logger.info(f"Loaded {len(teams)} teams from cache")
            return teams
        except Exception as e:
            self.logger.error(f"Failed to deserialize teams: {e}")
            return None

    # User overrides
    def save_overrides(self, overrides: dict) -> None:
        """
        Save user overrides.

        Args:
            overrides: Dictionary of user overrides
        """
        data = {"updated_at": datetime.now().isoformat(), "overrides": overrides}

        self._write_json(self.overrides_cache, data)
        self.logger.info(f"Saved {len(overrides)} overrides")

    def load_overrides(self) -> dict:
        """
        Load user overrides.

        Returns:
            Dictionary of overrides (empty dict if none exist)
        """
        if not self.overrides_cache.exists():
            return {}

        data = self._read_json(self.overrides_cache)
        if not data:
            return {}

        overrides = data.get("overrides", {})
        self.logger.info(f"Loaded {len(overrides)} overrides")
        return overrides

    # Utilities
    def clear_cache(self, cache_type: Optional[str] = None) -> None:
        """
        Clear cache files.

        Args:
            cache_type: Specific cache to clear ("schedule", "results", "odds", "teams")
                       If None, clears all caches (except user_overrides)
        """
        cache_map = {
            "schedule": self.schedule_cache,
            "results": self.results_cache,
            "odds": self.odds_cache,
            "teams": self.teams_cache,
        }

        if cache_type:
            if cache_type not in cache_map:
                raise ValueError(f"Invalid cache type: {cache_type}")

            filepath = cache_map[cache_type]
            if "*" in str(filepath):
                # Handle schedule cache with wildcard
                for f in self.cache_dir.glob("schedule_*.json"):
                    f.unlink()
                    self.logger.info(f"Cleared cache: {f.name}")
            elif filepath.exists():
                filepath.unlink()
                self.logger.info(f"Cleared cache: {cache_type}")
        else:
            # Clear all except overrides
            for name, filepath in cache_map.items():
                if "*" in str(filepath):
                    for f in self.cache_dir.glob("schedule_*.json"):
                        f.unlink()
                elif filepath.exists():
                    filepath.unlink()
                self.logger.info(f"Cleared cache: {name}")

    def get_cache_info(self) -> dict:
        """
        Get information about cached files.

        Returns:
            Dictionary with cache metadata:
            {
                "schedule": {"exists": True, "age_seconds": 1234, "last_modified": datetime(...)},
                "results": {...},
                ...
            }
        """
        info = {}

        cache_files = {
            "schedule": self.cache_dir / "schedule_2025.json",
            "results": self.results_cache,
            "odds": self.odds_cache,
            "teams": self.teams_cache,
            "overrides": self.overrides_cache,
        }

        for name, filepath in cache_files.items():
            if filepath.exists():
                age = self._get_file_age(filepath)
                mtime = filepath.stat().st_mtime
                info[name] = {
                    "exists": True,
                    "age_seconds": age,
                    "last_modified": datetime.fromtimestamp(mtime),
                }
            else:
                info[name] = {"exists": False, "age_seconds": None, "last_modified": None}

        return info

    # Private helper methods
    def _is_cache_valid(self, filepath: Path, max_age_seconds: int) -> bool:
        """Check if cache file exists and is not too old."""
        if not filepath.exists():
            return False

        age = self._get_file_age(filepath)
        return age is not None and age < max_age_seconds

    def _get_file_age(self, filepath: Path) -> Optional[float]:
        """Get age of file in seconds, or None if doesn't exist."""
        if not filepath.exists():
            return None

        mtime = filepath.stat().st_mtime
        return time.time() - mtime

    def _write_json(self, filepath: Path, data: dict) -> None:
        """Write data to JSON file."""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to write cache {filepath}: {e}")
            raise

    def _read_json(self, filepath: Path) -> Optional[dict]:
        """Read data from JSON file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to read cache {filepath}: {e}")
            return None

    def _serialize_game(self, game: Game) -> dict:
        """Convert Game object to JSON-serializable dict."""
        return {
            "id": game.id,
            "week": game.week,
            "season": game.season,
            "home_team_id": game.home_team_id,
            "away_team_id": game.away_team_id,
            "date": game.date.isoformat(),
            "is_completed": game.is_completed,
            "home_score": game.home_score,
            "away_score": game.away_score,
            "home_moneyline": game.home_moneyline,
            "away_moneyline": game.away_moneyline,
            "home_win_probability": game.home_win_probability,
            "away_win_probability": game.away_win_probability,
            "is_overridden": game.is_overridden,
            "override_home_score": game.override_home_score,
            "override_away_score": game.override_away_score,
            "override_home_moneyline": game.override_home_moneyline,
            "override_away_moneyline": game.override_away_moneyline,
            "last_updated": game.last_updated.isoformat()
            if game.last_updated
            else None,
            "odds_source": game.odds_source,
        }

    def _deserialize_game(self, data: dict) -> Game:
        """Convert dict to Game object."""
        return Game(
            id=data["id"],
            week=data["week"],
            season=data["season"],
            home_team_id=data["home_team_id"],
            away_team_id=data["away_team_id"],
            date=datetime.fromisoformat(data["date"]),
            is_completed=data["is_completed"],
            home_score=data.get("home_score"),
            away_score=data.get("away_score"),
            home_moneyline=data.get("home_moneyline"),
            away_moneyline=data.get("away_moneyline"),
            home_win_probability=data.get("home_win_probability"),
            away_win_probability=data.get("away_win_probability"),
            is_overridden=data.get("is_overridden", False),
            override_home_score=data.get("override_home_score"),
            override_away_score=data.get("override_away_score"),
            override_home_moneyline=data.get("override_home_moneyline"),
            override_away_moneyline=data.get("override_away_moneyline"),
            last_updated=datetime.fromisoformat(data["last_updated"])
            if data.get("last_updated")
            else None,
            odds_source=data.get("odds_source"),
        )

    def _serialize_team(self, team: Team) -> dict:
        """Convert Team object to JSON-serializable dict."""
        return {
            "id": team.id,
            "abbreviation": team.abbreviation,
            "name": team.name,
            "display_name": team.display_name,
            "location": team.location,
            "conference": team.conference,
            "division": team.division,
            "color": team.color,
            "logo_url": team.logo_url,
        }

    def _deserialize_team(self, data: dict) -> Team:
        """Convert dict to Team object."""
        return Team(
            id=data["id"],
            abbreviation=data["abbreviation"],
            name=data["name"],
            display_name=data["display_name"],
            location=data["location"],
            conference=data["conference"],
            division=data["division"],
            color=data.get("color"),
            logo_url=data.get("logo_url"),
        )
