"""
Tests for The Odds API client.

Note: These are placeholder tests. Real API tests require a valid API key.
"""

import pytest
import requests_mock

from src.data.odds_api import OddsAPIClient, OddsAPIError, QuotaExceededError


class TestOddsAPIClient:
    """Tests for Odds API Client."""

    @pytest.fixture
    def odds_client(self):
        """Create Odds API client."""
        return OddsAPIClient(
            api_key="test_key", base_url="https://api.the-odds-api.com/v4"
        )

    def test_fetch_nfl_odds_missing_api_key(self):
        """Test error when API key not provided."""
        client = OddsAPIClient(api_key="", base_url="https://api.test.com")

        with pytest.raises(OddsAPIError, match="not configured"):
            client.fetch_nfl_odds()

    def test_fetch_nfl_odds_quota_exceeded(self, odds_client):
        """Test handling of quota exceeded (429 status)."""
        with requests_mock.Mocker() as m:
            m.get(requests_mock.ANY, status_code=429)

            with pytest.raises(QuotaExceededError, match="quota exceeded"):
                odds_client.fetch_nfl_odds()

    def test_fetch_nfl_odds_invalid_api_key(self, odds_client):
        """Test handling of invalid API key."""
        with requests_mock.Mocker() as m:
            m.get(requests_mock.ANY, status_code=401)

            with pytest.raises(OddsAPIError, match="Invalid API key"):
                odds_client.fetch_nfl_odds()

    def test_get_requests_remaining(self, odds_client):
        """Test parsing of requests remaining header."""
        assert odds_client.get_requests_remaining() is None  # Initially None

    @pytest.mark.api
    def test_fetch_nfl_odds_real_api(self):
        """
        Test real API call (requires valid API key in .env).

        Run with: pytest -m api
        """
        import os
        from dotenv import load_dotenv

        load_dotenv()

        api_key = os.getenv("ODDS_API_KEY")
        if not api_key or api_key == "your_api_key_here":
            pytest.skip("Valid ODDS_API_KEY not configured")

        client = OddsAPIClient(
            api_key=api_key, base_url="https://api.the-odds-api.com/v4"
        )

        odds = client.fetch_nfl_odds()
        # May be empty if no games scheduled
        assert isinstance(odds, dict)
        assert client.get_requests_remaining() is not None
