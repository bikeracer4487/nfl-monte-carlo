"""
Data models for the NFL Monte Carlo simulation application.

Defines core data structures for teams, games, and standings.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Team:
    """Represents an NFL team."""

    # Core identifiers
    id: str  # ESPN team ID (e.g., "1" for Atlanta Falcons)
    abbreviation: str  # Team abbreviation (e.g., "ATL")
    name: str  # Full team name (e.g., "Atlanta Falcons")
    display_name: str  # Display name (e.g., "Falcons")
    location: str  # City/location (e.g., "Atlanta")

    # Organization
    conference: str  # "AFC" or "NFC"
    division: str  # "North", "South", "East", "West"

    # Branding (optional, for future phases)
    color: Optional[str] = None  # Primary team color (hex)
    logo_url: Optional[str] = None  # Logo image URL

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.location} {self.display_name}"

    def full_division(self) -> str:
        """Return full division name (e.g., 'NFC North')."""
        return f"{self.conference} {self.division}"


@dataclass
class Game:
    """Represents an NFL game."""

    # Core identifiers
    id: str  # ESPN game ID
    week: int  # Week number (1-18)
    season: int  # Season year (e.g., 2025)

    # Teams
    home_team_id: str  # Home team ESPN ID
    away_team_id: str  # Away team ESPN ID

    # Schedule
    date: datetime  # Game date and time
    is_completed: bool  # Whether game has been played

    # Results (if completed)
    home_score: Optional[int] = None
    away_score: Optional[int] = None

    # Overrides
    is_overridden: bool = False
    override_home_score: Optional[int] = None
    override_away_score: Optional[int] = None

    # Metadata
    last_updated: Optional[datetime] = None

    def get_winner_id(self) -> Optional[str]:
        """
        Return the winning team ID, or None if not completed or tie.

        Returns:
            Winner's team ID, or None for incomplete game or tie
        """
        if not self.is_completed:
            return None

        home = (
            self.override_home_score if self.is_overridden else self.home_score
        )
        away = (
            self.override_away_score if self.is_overridden else self.away_score
        )

        if home is None or away is None:
            return None

        if home > away:
            return self.home_team_id
        elif away > home:
            return self.away_team_id
        else:
            return None  # Tie

    def get_winner(self) -> str:
        """
        Return "home", "away", or "tie" for game outcome.

        Returns:
            "home" if home team won
            "away" if away team won
            "tie" if game tied or not yet completed
        """
        if not self.is_completed:
            return "tie"

        home = (
            self.override_home_score if self.is_overridden else self.home_score
        )
        away = (
            self.override_away_score if self.is_overridden else self.away_score
        )

        if home is None or away is None:
            return "tie"

        if home > away:
            return "home"
        elif away > home:
            return "away"
        else:
            return "tie"

    def get_effective_scores(self) -> tuple[Optional[int], Optional[int]]:
        """
        Return effective scores (override or actual).

        Returns:
            Tuple of (home_score, away_score)
        """
        if self.is_overridden:
            return (self.override_home_score, self.override_away_score)
        return (self.home_score, self.away_score)



@dataclass
class Standing:
    """Represents a team's standings information."""

    # Team reference
    team_id: str

    # Overall record
    wins: int = 0
    losses: int = 0
    ties: int = 0

    # Divisional and conference records
    division_wins: int = 0
    division_losses: int = 0
    division_ties: int = 0

    conference_wins: int = 0
    conference_losses: int = 0
    conference_ties: int = 0

    # Points
    points_for: int = 0
    points_against: int = 0

    # Tiebreaker helpers (will be populated during calculation)
    head_to_head_records: dict[str, tuple[int, int, int]] = field(
        default_factory=dict
    )  # {team_id: (w, l, t)}
    common_games_record: tuple[int, int, int] = (0, 0, 0)  # (w, l, t)
    strength_of_victory: float = 0.0
    strength_of_schedule: float = 0.0

    @property
    def win_percentage(self) -> float:
        """Calculate win percentage (ties count as 0.5 wins)."""
        total_games = self.wins + self.losses + self.ties
        if total_games == 0:
            return 0.0
        return (self.wins + 0.5 * self.ties) / total_games

    @property
    def division_win_percentage(self) -> float:
        """Calculate division win percentage."""
        total = self.division_wins + self.division_losses + self.division_ties
        if total == 0:
            return 0.0
        return (self.division_wins + 0.5 * self.division_ties) / total

    @property
    def conference_win_percentage(self) -> float:
        """Calculate conference win percentage."""
        total = (
            self.conference_wins + self.conference_losses + self.conference_ties
        )
        if total == 0:
            return 0.0
        return (self.conference_wins + 0.5 * self.conference_ties) / total

    @property
    def net_points(self) -> int:
        """Calculate point differential."""
        return self.points_for - self.points_against

    def __str__(self) -> str:
        """Return string representation."""
        return (
            f"Standing(team_id={self.team_id}, "
            f"record={self.wins}-{self.losses}-{self.ties}, "
            f"pct={self.win_percentage:.3f})"
        )
