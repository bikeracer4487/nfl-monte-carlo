"""
Utilities for matching odds data to schedule games.

Provides helper functions to normalize team names, build lookups,
and merge odds results from external APIs into our Game objects.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

from ..utils.logger import setup_logger
from .models import Game, Team

logger = setup_logger(__name__)


def _normalize_team_name(name: Optional[str]) -> str:
    """Normalize team names for fuzzy matching."""

    if not name:
        return ""

    normalized = name.lower()
    replacements = {
        "&": "and",
        "st.": "saint",
        "st ": "saint ",
    }

    for target, replacement in replacements.items():
        normalized = normalized.replace(target, replacement)

    # Remove all non-alphanumeric characters
    normalized = re.sub(r"[^a-z0-9]", "", normalized)
    return normalized


def _build_team_lookup(teams: Iterable[Team]) -> Dict[str, Team]:
    """Build lookup of normalized team aliases to Team objects."""

    lookup: Dict[str, Team] = {}

    for team in teams:
        aliases = {
            team.name,
            team.display_name,
            f"{team.location} {team.display_name}",
            f"{team.location} {team.name}",
            team.abbreviation,
        }

        for alias in aliases:
            normalized = _normalize_team_name(alias)
            if not normalized or normalized in lookup:
                continue
            lookup[normalized] = team

    return lookup


def match_odds_to_games(
    games: List[Game],
    teams: List[Team],
    odds_data: Dict[str, Dict],
    *,
    return_details: bool = False,
) -> Tuple[int, List[str], Optional[List[Dict[str, str]]]]:
    """
    Merge odds data into upcoming games.

    Args:
        games: List of Game objects for the season.
        teams: List of Team objects (used for name normalization).
        odds_data: Dict returned from OddsAPIClient.
        return_details: If True, returns list of matched summaries (for debugging).

    Returns:
        Tuple of:
            matched_count (int): Number of games updated with odds.
            unmatched_games (List[str]): Descriptions of odds entries that couldn't be matched.
            matched_details (Optional[List[Dict]]): Details of matched games (only if return_details=True).
    """

    if not games or not odds_data:
        return 0, [], [] if return_details else None

    team_lookup = _build_team_lookup(teams)

    # Pre-build lookup for upcoming games
    upcoming_games: Dict[Tuple[str, str], List[Game]] = {}
    for game in games:
        if game.is_completed:
            continue
        key = (game.home_team_id, game.away_team_id)
        upcoming_games.setdefault(key, []).append(game)

    matched_count = 0
    unmatched_descriptions: List[str] = []
    matched_details: List[Dict[str, str]] = [] if return_details else []

    for odds_entry in odds_data.values():
        odds_home = odds_entry.get("home_team")
        odds_away = odds_entry.get("away_team")

        normalized_home = _normalize_team_name(odds_home)
        normalized_away = _normalize_team_name(odds_away)

        home_team = team_lookup.get(normalized_home)
        away_team = team_lookup.get(normalized_away)

        if not home_team or not away_team:
            unmatched_descriptions.append(
                f"{odds_away or '?'} @ {odds_home or '?'} (team lookup failed)"
            )
            continue

        key = (home_team.id, away_team.id)
        possible_games = upcoming_games.get(key)

        if not possible_games:
            unmatched_descriptions.append(
                f"{away_team.name} @ {home_team.name} (no scheduled upcoming game)"
            )
            continue

        home_odds = odds_entry.get("home_odds")
        away_odds = odds_entry.get("away_odds")
        bookmaker = odds_entry.get("bookmaker")
        last_update: datetime = odds_entry.get("last_update") or datetime.utcnow()

        for game in possible_games:
            game.home_moneyline = home_odds
            game.away_moneyline = away_odds
            game.odds_source = bookmaker
            game.last_updated = last_update
            matched_count += 1

            if return_details:
                matched_details.append(
                    {
                        "game_id": game.id,
                        "week": str(game.week),
                        "home_team": home_team.name,
                        "away_team": away_team.name,
                        "home_odds": str(home_odds),
                        "away_odds": str(away_odds),
                        "bookmaker": bookmaker or "",
                    }
                )

    if matched_count:
        logger.info("Matched odds for %s games", matched_count)
    else:
        logger.warning("No odds matched to upcoming games")

    if unmatched_descriptions:
        logger.debug(
            "Unmatched odds entries (%d): %s",
            len(unmatched_descriptions),
            unmatched_descriptions[:5],
        )

    if return_details:
        return matched_count, unmatched_descriptions, matched_details

    return matched_count, unmatched_descriptions, None

