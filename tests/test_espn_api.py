"""
Tests for ESPN API client.

Note: These are placeholder tests. Real API tests are marked with @pytest.mark.api
and can be run with: pytest -m api
"""

import pytest
import requests
import requests_mock

from src.data.espn_api import ESPNAPIClient, ESPNAPIError


class TestESPNAPIClient:
    """Tests for ESPN API Client."""

    @pytest.fixture
    def espn_client(self):
        """Create ESPN API client."""
        return ESPNAPIClient(
            base_url="https://site.api.espn.com/apis/site/v2",
            core_api_url="https://sports.core.api.espn.com/v2",
        )

    @pytest.mark.api
    def test_fetch_teams_real_api(self, espn_client):
        """
        Test real API call to fetch teams.

        Run with: pytest -m api
        """
        teams = espn_client.fetch_teams()
        assert len(teams) == 32
        assert all(team.conference in ["AFC", "NFC"] for team in teams)
        assert all(
            team.division in ["North", "South", "East", "West"] for team in teams
        )

    @pytest.mark.api
    def test_fetch_schedule_real_api(self, espn_client):
        """
        Test real API call to fetch schedule.

        Run with: pytest -m api
        """
        games = espn_client.fetch_schedule(season=2025)
        # Should have 272 regular season games
        assert len(games) > 250
        assert all(1 <= game.week <= 18 for game in games)

    def test_request_timeout(self, espn_client):
        """Test timeout handling."""
        with requests_mock.Mocker() as m:
            m.get(requests_mock.ANY, exc=requests.exceptions.Timeout)

            with pytest.raises(ESPNAPIError, match="timeout"):
                espn_client._make_request("https://example.com")

    def test_request_http_error(self, espn_client):
        """Test HTTP error handling."""
        with requests_mock.Mocker() as m:
            m.get(requests_mock.ANY, status_code=500)

            with pytest.raises(ESPNAPIError, match="HTTP error"):
                espn_client._make_request("https://example.com")
