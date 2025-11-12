"""
ESPN API client for fetching NFL data.

Provides interface to ESPN's unofficial NFL API for schedules, scores, and teams.
"""

import time
from datetime import datetime
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.logger import setup_logger
from .models import Team, Game


class ESPNAPIError(Exception):
    """Custom exception for ESPN API errors."""

    pass


class ESPNAPIClient:
    """Client for ESPN's unofficial NFL API."""

    def __init__(self, base_url: str, core_api_url: str):
        """
        Initialize ESPN API client.

        Args:
            base_url: Base URL for ESPN site API
            core_api_url: Base URL for ESPN core API
        """
        self.base_url = base_url.rstrip("/")
        self.core_api_url = core_api_url.rstrip("/")
        self.logger = setup_logger(__name__)

        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def fetch_teams(self) -> list[Team]:
        """
        Fetch all NFL teams.

        Returns:
            List of Team objects (32 teams)

        Raises:
            ESPNAPIError: If API call fails
        """
        self.logger.info("Fetching NFL teams from ESPN")
        url = f"{self.base_url}/sports/football/nfl/teams"

        try:
            response_data = self._make_request(url)

            teams = []
            sports_data = response_data.get("sports", [])

            if not sports_data:
                raise ESPNAPIError("No sports data in response")

            leagues = sports_data[0].get("leagues", [])
            if not leagues:
                raise ESPNAPIError("No leagues data in response")

            teams_data = leagues[0].get("teams", [])

            for team_item in teams_data:
                team_data = team_item.get("team", {})

                team = Team(
                    id=team_data.get("id", ""),
                    abbreviation=team_data.get("abbreviation", ""),
                    name=team_data.get("name", ""),
                    display_name=team_data.get("displayName", ""),
                    location=team_data.get("location", ""),
                    conference=team_data.get("groups", {}).get("id", "").split("/")[-1].upper() if team_data.get("groups") else "",
                    division=team_data.get("groups", {}).get("name", "").split()[-1] if team_data.get("groups") else "",
                    color=team_data.get("color"),
                    logo_url=team_data.get("logos", [{}])[0].get("href")
                    if team_data.get("logos")
                    else None,
                )

                teams.append(team)

            self.logger.info(f"Successfully fetched {len(teams)} teams")
            return teams

        except requests.RequestException as e:
            raise ESPNAPIError(f"Failed to fetch teams: {e}") from e
        except (KeyError, IndexError, ValueError) as e:
            raise ESPNAPIError(f"Failed to parse teams data: {e}") from e

    def fetch_schedule(self, season: int = 2025) -> list[Game]:
        """
        Fetch complete season schedule.

        Args:
            season: Season year (default: 2025)

        Returns:
            List of Game objects

        Raises:
            ESPNAPIError: If API call fails
        """
        self.logger.info(f"Fetching {season} NFL schedule from ESPN")
        url = (
            f"{self.core_api_url}/sports/football/leagues/nfl/"
            f"seasons/{season}/types/2/events"
        )
        params = {"limit": 1000}

        try:
            response_data = self._make_request(url, params)

            items = response_data.get("items", [])
            if not items:
                self.logger.warning("No games found in schedule")
                return []

            games = []
            for item in items:
                # Each item has a $ref URL to the detailed game data
                game_url = item.get("$ref", "")
                if game_url:
                    try:
                        game = self._fetch_game_details(game_url)
                        if game:
                            games.append(game)
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to fetch game details from {game_url}: {e}"
                        )
                        continue

            self.logger.info(f"Successfully fetched {len(games)} games")
            return games

        except requests.RequestException as e:
            raise ESPNAPIError(f"Failed to fetch schedule: {e}") from e
        except (KeyError, ValueError) as e:
            raise ESPNAPIError(f"Failed to parse schedule data: {e}") from e

    def fetch_scoreboard(self, week: Optional[int] = None) -> list[Game]:
        """
        Fetch current scoreboard (completed games).

        Args:
            week: Optional week number (if None, fetches current week)

        Returns:
            List of completed Game objects with scores

        Raises:
            ESPNAPIError: If API call fails
        """
        self.logger.info(f"Fetching scoreboard for week {week or 'current'}")
        url = f"{self.base_url}/sports/football/nfl/scoreboard"

        params = {}
        if week is not None:
            params["week"] = week

        try:
            response_data = self._make_request(url, params)

            events = response_data.get("events", [])
            if not events:
                self.logger.info("No games found in scoreboard")
                return []

            games = []
            for event in events:
                try:
                    game = self._parse_scoreboard_game(event)
                    if game:
                        games.append(game)
                except Exception as e:
                    self.logger.warning(f"Failed to parse game: {e}")
                    continue

            self.logger.info(f"Successfully fetched {len(games)} game results")
            return games

        except requests.RequestException as e:
            raise ESPNAPIError(f"Failed to fetch scoreboard: {e}") from e

    def _fetch_game_details(self, game_url: str) -> Optional[Game]:
        """
        Fetch detailed game information from a specific URL.

        Args:
            game_url: URL to game details

        Returns:
            Game object or None if parsing fails
        """
        try:
            game_data = self._make_request(game_url)

            game_id = game_data.get("id", "")
            date_str = game_data.get("date", "")
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

            season = game_data.get("season", {}).get("year", 2025)
            week = game_data.get("week", {}).get("number", 1)

            competitions = game_data.get("competitions", [])
            if not competitions:
                return None

            competition = competitions[0]
            competitors = competition.get("competitors", [])

            if len(competitors) != 2:
                return None

            # Determine home and away teams
            home_competitor = next(
                (c for c in competitors if c.get("homeAway") == "home"), None
            )
            away_competitor = next(
                (c for c in competitors if c.get("homeAway") == "away"), None
            )

            if not home_competitor or not away_competitor:
                return None

            home_team_id = home_competitor.get("id", "")
            away_team_id = away_competitor.get("id", "")

            # Check if game is completed
            is_completed = competition.get("status", {}).get("type", {}).get(
                "completed", False
            )

            game = Game(
                id=game_id,
                week=week,
                season=season,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                date=date,
                is_completed=is_completed,
            )

            # Add scores if completed
            if is_completed:
                game.home_score = int(home_competitor.get("score", 0))
                game.away_score = int(away_competitor.get("score", 0))

            return game

        except Exception as e:
            self.logger.warning(f"Failed to parse game details: {e}")
            return None

    def _parse_scoreboard_game(self, event: dict) -> Optional[Game]:
        """
        Parse a game from scoreboard data.

        Args:
            event: Event dictionary from scoreboard

        Returns:
            Game object or None if parsing fails
        """
        try:
            game_id = event.get("id", "")
            date_str = event.get("date", "")
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

            season = event.get("season", {}).get("year", 2025)
            week = event.get("week", {}).get("number", 1)

            competitions = event.get("competitions", [])
            if not competitions:
                return None

            competition = competitions[0]
            competitors = competition.get("competitors", [])

            if len(competitors) != 2:
                return None

            home_competitor = next(
                (c for c in competitors if c.get("homeAway") == "home"), None
            )
            away_competitor = next(
                (c for c in competitors if c.get("homeAway") == "away"), None
            )

            if not home_competitor or not away_competitor:
                return None

            is_completed = competition.get("status", {}).get("type", {}).get(
                "completed", False
            )

            game = Game(
                id=game_id,
                week=week,
                season=season,
                home_team_id=home_competitor.get("id", ""),
                away_team_id=away_competitor.get("id", ""),
                date=date,
                is_completed=is_completed,
                home_score=int(home_competitor.get("score", 0))
                if is_completed
                else None,
                away_score=int(away_competitor.get("score", 0))
                if is_completed
                else None,
                last_updated=datetime.now(),
            )

            return game

        except Exception as e:
            self.logger.warning(f"Failed to parse scoreboard game: {e}")
            return None

    def _make_request(
        self, url: str, params: Optional[dict] = None, timeout: int = 10
    ) -> dict:
        """
        Make HTTP request with error handling and retries.

        Args:
            url: Full URL to request
            params: Optional query parameters
            timeout: Request timeout in seconds

        Returns:
            JSON response as dictionary

        Raises:
            ESPNAPIError: If request fails after retries
        """
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise ESPNAPIError(f"Request timeout for {url}")
        except requests.exceptions.HTTPError as e:
            raise ESPNAPIError(f"HTTP error {e.response.status_code}: {e}")
        except requests.exceptions.RequestException as e:
            raise ESPNAPIError(f"Request failed: {e}")
        except ValueError as e:
            raise ESPNAPIError(f"Invalid JSON response: {e}")
