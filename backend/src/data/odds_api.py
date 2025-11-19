"""
The Odds API client for fetching NFL betting odds.

Provides interface to The Odds API for current NFL moneyline odds.
"""

from datetime import datetime
from typing import Optional

import requests

from ..utils.logger import setup_logger


class OddsAPIError(Exception):
    """Custom exception for Odds API errors."""

    pass


class QuotaExceededError(OddsAPIError):
    """Raised when API quota is exceeded."""

    pass


class OddsAPIClient:
    """Client for The Odds API."""

    def __init__(self, api_key: str, base_url: str):
        """
        Initialize Odds API client.

        Args:
            api_key: The Odds API key
            base_url: Base URL for The Odds API
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.logger = setup_logger(__name__)
        self.requests_remaining: Optional[int] = None

    def fetch_nfl_odds(
        self, bookmaker: str = "draftkings", region: str = "us"
    ) -> dict[str, dict]:
        """
        Fetch current NFL moneyline odds.

        Args:
            bookmaker: Preferred bookmaker (default: "draftkings")
                      Options: draftkings, fanduel, betmgm, etc.
            region: Region for odds (default: "us")

        Returns:
            Dictionary mapping game identifiers to odds:
            {
                "away_team_vs_home_team": {
                    "home_team": "Kansas City Chiefs",
                    "away_team": "Buffalo Bills",
                    "home_odds": -150,
                    "away_odds": 130,
                    "commence_time": datetime(...),
                    "bookmaker": "draftkings"
                }
            }

        Raises:
            OddsAPIError: If API call fails
            QuotaExceededError: If API quota exceeded
        """
        if not self.api_key or self.api_key == "your_api_key_here":
            raise OddsAPIError("Odds API key not configured")

        self.logger.info(f"Fetching NFL odds from {bookmaker}")

        endpoint = f"{self.base_url}/sports/americanfootball_nfl/odds"
        params = {
            "apiKey": self.api_key,
            "regions": region,
            "markets": "h2h",  # head-to-head (moneyline)
            "oddsFormat": "american",
        }

        try:
            response_data = self._make_request(endpoint, params)

            if not response_data:
                self.logger.info("No NFL games found with odds")
                return {}

            odds_dict = {}
            for game in response_data:
                try:
                    parsed_odds = self._parse_game_odds(game, bookmaker)
                    if parsed_odds:
                        game_key = f"{parsed_odds['away_team']}_vs_{parsed_odds['home_team']}"
                        odds_dict[game_key] = parsed_odds
                except Exception as e:
                    self.logger.warning(f"Failed to parse game odds: {e}")
                    continue

            self.logger.info(f"Successfully fetched odds for {len(odds_dict)} games")
            self.logger.info(f"API requests remaining: {self.requests_remaining}")

            return odds_dict

        except requests.RequestException as e:
            raise OddsAPIError(f"Failed to fetch odds: {e}") from e

    def get_requests_remaining(self) -> Optional[int]:
        """
        Get remaining API requests in current quota period.

        Returns:
            Number of requests remaining, or None if unknown
        """
        return self.requests_remaining

    def _parse_game_odds(
        self, game: dict, preferred_bookmaker: str
    ) -> Optional[dict]:
        """
        Parse odds for a single game.

        Args:
            game: Game dictionary from API response
            preferred_bookmaker: Preferred bookmaker to use

        Returns:
            Parsed odds dictionary or None if parsing fails
        """
        try:
            home_team = game.get("home_team", "")
            away_team = game.get("away_team", "")
            commence_time_str = game.get("commence_time", "")

            if not home_team or not away_team:
                return None

            commence_time = datetime.fromisoformat(
                commence_time_str.replace("Z", "+00:00")
            )

            # Find odds from preferred bookmaker
            bookmakers = game.get("bookmakers", [])
            target_bookmaker = None

            for bookmaker in bookmakers:
                if bookmaker.get("key") == preferred_bookmaker:
                    target_bookmaker = bookmaker
                    break

            # Fallback to first bookmaker if preferred not found
            if not target_bookmaker and bookmakers:
                target_bookmaker = bookmakers[0]
                self.logger.debug(
                    f"Preferred bookmaker '{preferred_bookmaker}' not found, "
                    f"using '{target_bookmaker.get('key')}'"
                )

            if not target_bookmaker:
                return None

            # Extract moneyline odds
            markets = target_bookmaker.get("markets", [])
            h2h_market = next((m for m in markets if m.get("key") == "h2h"), None)

            if not h2h_market:
                return None

            outcomes = h2h_market.get("outcomes", [])
            if len(outcomes) != 2:
                return None

            # Match outcomes to teams
            home_outcome = next(
                (o for o in outcomes if o.get("name") == home_team), None
            )
            away_outcome = next(
                (o for o in outcomes if o.get("name") == away_team), None
            )

            if not home_outcome or not away_outcome:
                return None

            return {
                "home_team": home_team,
                "away_team": away_team,
                "home_odds": home_outcome.get("price"),
                "away_odds": away_outcome.get("price"),
                "commence_time": commence_time,
                "bookmaker": target_bookmaker.get("key"),
                "last_update": datetime.now(),
            }

        except Exception as e:
            self.logger.warning(f"Failed to parse game odds: {e}")
            return None

    def _make_request(
        self, endpoint: str, params: Optional[dict] = None, timeout: int = 10
    ) -> list:
        """
        Make HTTP request with error handling.

        Args:
            endpoint: API endpoint URL
            params: Query parameters
            timeout: Request timeout in seconds

        Returns:
            JSON response as list

        Raises:
            OddsAPIError: If request fails
            QuotaExceededError: If quota exceeded
        """
        try:
            response = self.session.get(endpoint, params=params, timeout=timeout)

            # Check for quota exceeded
            if response.status_code == 429:
                raise QuotaExceededError("API quota exceeded")

            # Check for other errors
            if response.status_code == 401:
                raise OddsAPIError("Invalid API key")

            response.raise_for_status()

            # Extract requests remaining from headers
            requests_remaining = response.headers.get("x-requests-remaining")
            if requests_remaining:
                try:
                    self.requests_remaining = int(requests_remaining)
                except ValueError:
                    pass

            return response.json()

        except requests.exceptions.Timeout:
            raise OddsAPIError(f"Request timeout for {endpoint}")
        except QuotaExceededError:
            raise
        except requests.exceptions.HTTPError as e:
            raise OddsAPIError(f"HTTP error {e.response.status_code}: {e}")
        except requests.exceptions.RequestException as e:
            raise OddsAPIError(f"Request failed: {e}")
        except ValueError as e:
            raise OddsAPIError(f"Invalid JSON response: {e}")
