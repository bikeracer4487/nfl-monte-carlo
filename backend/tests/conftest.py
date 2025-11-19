"""
Pytest configuration and fixtures for NFL Monte Carlo tests.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.data.models import Team, Game, Standing
from src.data.cache_manager import CacheManager


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def cache_manager(temp_cache_dir):
    """Create a CacheManager instance with temp directory."""
    return CacheManager(temp_cache_dir)


@pytest.fixture
def sample_team():
    """Create a sample Team object for testing."""
    return Team(
        id="1",
        abbreviation="ATL",
        name="Atlanta Falcons",
        display_name="Falcons",
        location="Atlanta",
        conference="NFC",
        division="South",
        color="#A71930",
        logo_url="https://example.com/atl_logo.png",
    )


@pytest.fixture
def sample_team_2():
    """Create a second sample Team object."""
    return Team(
        id="2",
        abbreviation="BUF",
        name="Buffalo Bills",
        display_name="Bills",
        location="Buffalo",
        conference="AFC",
        division="East",
    )


@pytest.fixture
def sample_game():
    """Create a sample Game object for testing."""
    return Game(
        id="401234567",
        week=1,
        season=2025,
        home_team_id="1",
        away_team_id="2",
        date=datetime(2025, 9, 7, 13, 0),
        is_completed=False,
    )


@pytest.fixture
def sample_completed_game():
    """Create a sample completed Game object."""
    return Game(
        id="401234568",
        week=1,
        season=2025,
        home_team_id="1",
        away_team_id="2",
        date=datetime(2025, 9, 7, 13, 0),
        is_completed=True,
        home_score=24,
        away_score=17,
        last_updated=datetime.now(),
    )


@pytest.fixture
def sample_tie_game():
    """Create a sample tie game."""
    return Game(
        id="401234569",
        week=1,
        season=2025,
        home_team_id="1",
        away_team_id="2",
        date=datetime(2025, 9, 7, 13, 0),
        is_completed=True,
        home_score=21,
        away_score=21,
    )


@pytest.fixture
def sample_standing():
    """Create a sample Standing object."""
    return Standing(
        team_id="1",
        wins=10,
        losses=5,
        ties=2,
        division_wins=4,
        division_losses=2,
        conference_wins=7,
        conference_losses=5,
        points_for=350,
        points_against=300,
    )


@pytest.fixture
def mock_espn_schedule_response():
    """Mock ESPN API schedule response."""
    return {
        "items": [
            {"$ref": "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/401234567"}
        ],
        "count": 1,
        "pageIndex": 1,
        "pageSize": 1000,
        "pageCount": 1,
    }


@pytest.fixture
def mock_espn_game_detail():
    """Mock ESPN API game detail response."""
    return {
        "id": "401234567",
        "date": "2025-09-07T17:00:00Z",
        "name": "Buffalo Bills at Atlanta Falcons",
        "season": {"year": 2025, "type": 2},
        "week": {"number": 1},
        "competitions": [
            {
                "id": "401234567",
                "date": "2025-09-07T17:00:00Z",
                "competitors": [
                    {
                        "id": "1",
                        "team": {"$ref": "https://api.espn.com/teams/1"},
                        "homeAway": "home",
                        "score": None,
                    },
                    {
                        "id": "2",
                        "team": {"$ref": "https://api.espn.com/teams/2"},
                        "homeAway": "away",
                        "score": None,
                    },
                ],
                "status": {"type": {"completed": False}},
            }
        ],
    }


