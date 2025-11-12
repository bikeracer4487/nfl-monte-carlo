#!/usr/bin/env python3
"""
Phase 1 Demonstration Script

This script demonstrates the functionality of Phase 1:
- Loading configuration
- Fetching teams from ESPN
- Fetching schedule from ESPN
- Caching data
- Loading from cache
- Fetching odds from The Odds API (if configured)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

from src.utils.logger import setup_logger
from src.utils.config import Config
from src.data.espn_api import ESPNAPIClient
from src.data.odds_api import OddsAPIClient
from src.data.cache_manager import CacheManager
from src.data.schedule_loader import ScheduleLoader


def main():
    """Run Phase 1 demonstration."""

    # Setup
    load_dotenv()
    logger = setup_logger(__name__)
    logger.info("=" * 60)
    logger.info("NFL Monte Carlo Simulation - Phase 1 Demo")
    logger.info("=" * 60)

    # Load configuration
    logger.info("\n1. Loading configuration...")
    config = Config.load()
    logger.info(f"   Cache directory: {config.CACHE_DIRECTORY}")
    logger.info(f"   ESPN API URL: {config.ESPN_API_BASE_URL}")
    logger.info(f"   Odds API configured: {'Yes' if config.ODDS_API_KEY and config.ODDS_API_KEY != 'your_api_key_here' else 'No'}")

    # Validate configuration
    errors = config.validate()
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"   - {error}")
        return

    # Initialize clients
    logger.info("\n2. Initializing API clients...")
    espn_client = ESPNAPIClient(config.ESPN_API_BASE_URL, config.ESPN_CORE_API_BASE_URL)
    odds_client = OddsAPIClient(config.ODDS_API_KEY, config.ODDS_API_BASE_URL)
    cache_manager = CacheManager(config.CACHE_DIRECTORY)
    schedule_loader = ScheduleLoader(espn_client, cache_manager)

    # Fetch teams
    logger.info("\n3. Fetching NFL teams...")
    try:
        teams = schedule_loader.load_teams(force_refresh=False)
        logger.info(f"   Loaded {len(teams)} teams")
        if teams:
            logger.info(f"   Sample: {teams[0]}")
    except Exception as e:
        logger.error(f"   Error fetching teams: {e}")
        teams = []

    # Display teams by division
    if teams:
        logger.info("\n4. Teams by Conference and Division:")
        for conference in ["AFC", "NFC"]:
            logger.info(f"\n   {conference}:")
            for division in ["North", "South", "East", "West"]:
                div_teams = [
                    t for t in teams if t.conference == conference and t.division == division
                ]
                logger.info(f"      {division}: {', '.join(t.abbreviation for t in div_teams)}")

    # Fetch schedule
    logger.info("\n5. Fetching 2025 NFL schedule...")
    try:
        schedule = schedule_loader.load_schedule(season=2025, force_refresh=False)
        logger.info(f"   Loaded {len(schedule)} games")

        # Display schedule summary
        if schedule:
            logger.info("\n6. Schedule summary:")
            for week in range(1, 19):
                week_games = [g for g in schedule if g.week == week]
                logger.info(f"   Week {week:2d}: {len(week_games):2d} games")

            # Sample games
            logger.info("\n7. Sample games from Week 1:")
            week1_games = [g for g in schedule if g.week == 1][:3]
            for game in week1_games:
                try:
                    home_team = next(t for t in teams if t.id == game.home_team_id)
                    away_team = next(t for t in teams if t.id == game.away_team_id)
                    logger.info(
                        f"   {away_team.abbreviation} @ {home_team.abbreviation} - {game.date.strftime('%Y-%m-%d %I:%M %p')}"
                    )
                except StopIteration:
                    logger.warning(f"   Could not find teams for game {game.id}")
    except Exception as e:
        logger.error(f"   Error fetching schedule: {e}")
        schedule = []

    # Fetch odds (if API key configured)
    if config.ODDS_API_KEY and config.ODDS_API_KEY != "your_api_key_here":
        logger.info("\n8. Fetching current NFL odds...")
        try:
            odds = odds_client.fetch_nfl_odds()
            logger.info(f"   Fetched odds for {len(odds)} games")
            if odds_client.get_requests_remaining():
                logger.info(f"   API requests remaining: {odds_client.get_requests_remaining()}")

            # Display sample odds
            if odds:
                sample_game = list(odds.values())[0]
                logger.info(f"\n   Sample odds:")
                logger.info(f"      {sample_game['away_team']} @ {sample_game['home_team']}")
                logger.info(f"      Home: {sample_game['home_odds']}")
                logger.info(f"      Away: {sample_game['away_odds']}")
                logger.info(f"      Bookmaker: {sample_game['bookmaker']}")
        except Exception as e:
            logger.error(f"   Error fetching odds: {e}")
    else:
        logger.info("\n8. Skipping odds fetch (no API key configured)")
        logger.info("   To enable: Get free API key from https://the-odds-api.com/")
        logger.info("   Then add to .env: ODDS_API_KEY=your_key_here")

    # Cache information
    logger.info("\n9. Cache information:")
    cache_info = cache_manager.get_cache_info()
    for cache_type, info in cache_info.items():
        if info["exists"]:
            logger.info(f"   {cache_type}: Cached {info['age_seconds']:.0f}s ago")
        else:
            logger.info(f"   {cache_type}: Not cached")

    logger.info("\n" + "=" * 60)
    logger.info("Phase 1 demonstration complete!")
    logger.info("=" * 60 + "\n")

    # Summary
    logger.info("Next steps:")
    logger.info("  - Run tests: pytest")
    logger.info("  - Check coverage: pytest --cov=src --cov-report=html")
    logger.info("  - Proceed to Phase 2: Monte Carlo Simulation Engine")


if __name__ == "__main__":
    main()
