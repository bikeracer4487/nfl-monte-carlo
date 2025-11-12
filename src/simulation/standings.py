"""
Standings calculator for NFL teams.

Calculates win-loss records, division/conference records, and sorts standings.
Phase 3 includes tiebreaker data: head-to-head records, strength metrics.
"""

from typing import Dict, List, Tuple
from collections import defaultdict

from ..data.models import Team, Game, Standing
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


def calculate_standings(games: List[Game], teams: List[Team]) -> Dict[str, Standing]:
    """
    Calculate standings for all teams based on game results.

    Processes completed and simulated games to build win-loss records,
    division records, conference records, and points scored/allowed.

    Args:
        games: List of all games (completed and simulated)
        teams: List of all teams

    Returns:
        Dictionary mapping team_id to Standing object

    Example:
        >>> standings = calculate_standings(games, teams)
        >>> chiefs_standing = standings["12"]
        >>> print(f"Record: {chiefs_standing.wins}-{chiefs_standing.losses}")
        Record: 13-4
    """
    # Initialize standings for all teams
    standings = {}
    team_dict = {team.id: team for team in teams}

    for team in teams:
        standings[team.id] = Standing(
            team_id=team.id,
            wins=0,
            losses=0,
            ties=0,
            division_wins=0,
            division_losses=0,
            division_ties=0,
            conference_wins=0,
            conference_losses=0,
            conference_ties=0,
            points_for=0,
            points_against=0,
        )

    # Process each game
    for game in games:
        # Skip games without results
        if not game.is_completed and game.get_winner() == "tie":
            continue

        home_team = team_dict.get(game.home_team_id)
        away_team = team_dict.get(game.away_team_id)

        if not home_team or not away_team:
            logger.warning(
                f"Game {game.id}: Missing team data "
                f"(home: {game.home_team_id}, away: {game.away_team_id})"
            )
            continue

        # Update standings based on game outcome
        update_standing_from_game(
            standings[game.home_team_id],
            standings[game.away_team_id],
            game,
            home_team,
            away_team,
        )

    # Populate tiebreaker data (Phase 3)
    populate_head_to_head_records(standings, games)
    populate_strength_metrics(standings, games)

    return standings


def update_standing_from_game(
    home_standing: Standing,
    away_standing: Standing,
    game: Game,
    home_team: Team,
    away_team: Team,
) -> None:
    """
    Update two team standings based on a single game result.

    Handles overall record, division record, conference record, and points.

    Args:
        home_standing: Standing object for home team
        away_standing: Standing object for away team
        game: Game object with result
        home_team: Team object for home team
        away_team: Team object for away team
    """
    winner = game.get_winner()

    # Determine if division/conference game
    is_div_game = is_division_game(home_team, away_team)
    is_conf_game = is_conference_game(home_team, away_team)

    if winner == "home":
        # Home team wins
        home_standing.wins += 1
        away_standing.losses += 1

        if is_div_game:
            home_standing.division_wins += 1
            away_standing.division_losses += 1

        if is_conf_game:
            home_standing.conference_wins += 1
            away_standing.conference_losses += 1

    elif winner == "away":
        # Away team wins
        away_standing.wins += 1
        home_standing.losses += 1

        if is_div_game:
            away_standing.division_wins += 1
            home_standing.division_losses += 1

        if is_conf_game:
            away_standing.conference_wins += 1
            home_standing.conference_losses += 1

    elif winner == "tie":
        # Tie game (rare but possible)
        home_standing.ties += 1
        away_standing.ties += 1

        if is_div_game:
            home_standing.division_ties += 1
            away_standing.division_ties += 1

        if is_conf_game:
            home_standing.conference_ties += 1
            away_standing.conference_ties += 1

    # Update points (only for completed games with scores)
    if game.is_completed and game.home_score is not None and game.away_score is not None:
        home_standing.points_for += game.home_score
        home_standing.points_against += game.away_score
        away_standing.points_for += game.away_score
        away_standing.points_against += game.home_score


def is_division_game(team1: Team, team2: Team) -> bool:
    """
    Check if two teams are in the same division.

    Args:
        team1: First team
        team2: Second team

    Returns:
        True if teams are division opponents

    Example:
        >>> chiefs = Team(conference="AFC", division="West", ...)
        >>> raiders = Team(conference="AFC", division="West", ...)
        >>> is_division_game(chiefs, raiders)
        True
    """
    return team1.conference == team2.conference and team1.division == team2.division


def is_conference_game(team1: Team, team2: Team) -> bool:
    """
    Check if two teams are in the same conference.

    Args:
        team1: First team
        team2: Second team

    Returns:
        True if teams are conference opponents

    Example:
        >>> chiefs = Team(conference="AFC", division="West", ...)
        >>> patriots = Team(conference="AFC", division="East", ...)
        >>> is_conference_game(chiefs, patriots)
        True
    """
    return team1.conference == team2.conference


def sort_standings_simple(standings: List[Standing]) -> List[Standing]:
    """
    Sort standings by win percentage (Phase 2: no tiebreakers).

    In Phase 3, this will be replaced with full NFL tiebreaker logic.

    Args:
        standings: List of Standing objects to sort

    Returns:
        Sorted list of standings (best record first)

    Note:
        Ties in win percentage are not resolved. Phase 3 will add:
        - Head-to-head record
        - Division record
        - Conference record
        - Strength of victory
        - Strength of schedule
        - And 7 more tiebreaker levels
    """
    return sorted(standings, key=lambda s: s.win_percentage, reverse=True)


def get_division_standings(
    standings: Dict[str, Standing], teams: List[Team], conference: str, division: str
) -> List[Standing]:
    """
    Get standings for a specific division, sorted by record.

    Args:
        standings: Dictionary of all standings
        teams: List of all teams
        conference: Conference name ("AFC" or "NFC")
        division: Division name ("North", "South", "East", "West")

    Returns:
        Sorted list of standings for the division

    Example:
        >>> standings_dict = calculate_standings(games, teams)
        >>> afc_west = get_division_standings(standings_dict, teams, "AFC", "West")
        >>> for standing in afc_west:
        ...     print(f"{standing.team_id}: {standing.wins}-{standing.losses}")
    """
    # Get teams in this division
    div_teams = [
        t for t in teams if t.conference == conference and t.division == division
    ]

    # Get standings for these teams
    div_standings = [standings[t.id] for t in div_teams]

    # Sort by win percentage
    return sort_standings_simple(div_standings)


def get_conference_standings(
    standings: Dict[str, Standing], teams: List[Team], conference: str
) -> List[Standing]:
    """
    Get standings for a specific conference, sorted by record.

    Args:
        standings: Dictionary of all standings
        teams: List of all teams
        conference: Conference name ("AFC" or "NFC")

    Returns:
        Sorted list of standings for the conference

    Example:
        >>> standings_dict = calculate_standings(games, teams)
        >>> afc = get_conference_standings(standings_dict, teams, "AFC")
        >>> print(f"Top AFC team: {afc[0].team_id}")
    """
    # Get teams in this conference
    conf_teams = [t for t in teams if t.conference == conference]

    # Get standings for these teams
    conf_standings = [standings[t.id] for t in conf_teams]

    # Sort by win percentage
    return sort_standings_simple(conf_standings)


def populate_head_to_head_records(
    standings: Dict[str, Standing], games: List[Game]
) -> None:
    """
    Populate head-to-head records for all teams in the standings.

    For each team, creates a dictionary of records against every opponent
    they've played: {opponent_id: (wins, losses, ties)}

    Args:
        standings: Dictionary of standings to populate (modified in place)
        games: List of all games to process
    """
    for game in games:
        # Skip games without results
        if not game.is_completed and game.get_winner() == "tie":
            continue

        home_id = game.home_team_id
        away_id = game.away_team_id

        # Skip if teams not in standings
        if home_id not in standings or away_id not in standings:
            continue

        winner = game.get_winner()

        # Initialize head-to-head records if not present
        if away_id not in standings[home_id].head_to_head_records:
            standings[home_id].head_to_head_records[away_id] = (0, 0, 0)
        if home_id not in standings[away_id].head_to_head_records:
            standings[away_id].head_to_head_records[home_id] = (0, 0, 0)

        # Get current records
        home_vs_away = standings[home_id].head_to_head_records[away_id]
        away_vs_home = standings[away_id].head_to_head_records[home_id]

        # Update based on outcome
        if winner == "home":
            standings[home_id].head_to_head_records[away_id] = (
                home_vs_away[0] + 1,  # wins
                home_vs_away[1],  # losses
                home_vs_away[2],  # ties
            )
            standings[away_id].head_to_head_records[home_id] = (
                away_vs_home[0],  # wins
                away_vs_home[1] + 1,  # losses
                away_vs_home[2],  # ties
            )
        elif winner == "away":
            standings[away_id].head_to_head_records[home_id] = (
                away_vs_home[0] + 1,  # wins
                away_vs_home[1],  # losses
                away_vs_home[2],  # ties
            )
            standings[home_id].head_to_head_records[away_id] = (
                home_vs_away[0],  # wins
                home_vs_away[1] + 1,  # losses
                home_vs_away[2],  # ties
            )
        elif winner == "tie":
            standings[home_id].head_to_head_records[away_id] = (
                home_vs_away[0],  # wins
                home_vs_away[1],  # losses
                home_vs_away[2] + 1,  # ties
            )
            standings[away_id].head_to_head_records[home_id] = (
                away_vs_home[0],  # wins
                away_vs_home[1],  # losses
                away_vs_home[2] + 1,  # ties
            )


def populate_strength_metrics(
    standings: Dict[str, Standing], games: List[Game]
) -> None:
    """
    Calculate and populate strength of victory and strength of schedule.

    Strength of Victory (SOV): Combined win percentage of teams this team has beaten
    Strength of Schedule (SOS): Combined win percentage of all opponents

    Args:
        standings: Dictionary of standings to populate (modified in place)
        games: List of all games to process

    Note:
        Must be called after basic standings (W-L records) are calculated,
        as it depends on win percentages.
    """
    # Build opponent lists for each team
    opponents_beaten = defaultdict(list)  # team_id -> list of beaten opponent_ids
    all_opponents = defaultdict(list)  # team_id -> list of all opponent_ids

    for game in games:
        # Skip games without results
        if not game.is_completed and game.get_winner() == "tie":
            continue

        home_id = game.home_team_id
        away_id = game.away_team_id

        # Skip if teams not in standings
        if home_id not in standings or away_id not in standings:
            continue

        winner = game.get_winner()

        # Track all opponents
        all_opponents[home_id].append(away_id)
        all_opponents[away_id].append(home_id)

        # Track beaten opponents
        if winner == "home":
            opponents_beaten[home_id].append(away_id)
        elif winner == "away":
            opponents_beaten[away_id].append(home_id)

    # Calculate strength metrics for each team
    for team_id, standing in standings.items():
        # Strength of Victory
        beaten_opponents = opponents_beaten.get(team_id, [])
        if beaten_opponents:
            total_win_pct = sum(
                standings[opp_id].win_percentage for opp_id in beaten_opponents
            )
            standing.strength_of_victory = total_win_pct / len(beaten_opponents)
        else:
            standing.strength_of_victory = 0.0

        # Strength of Schedule
        all_opps = all_opponents.get(team_id, [])
        if all_opps:
            total_win_pct = sum(
                standings[opp_id].win_percentage for opp_id in all_opps
            )
            standing.strength_of_schedule = total_win_pct / len(all_opps)
        else:
            standing.strength_of_schedule = 0.0
