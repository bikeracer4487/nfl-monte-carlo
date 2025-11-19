import sys
from pathlib import Path
import logging
from typing import List, Dict, Any

# Setup path to import src
# current file is in backend/
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))

from src.utils.logger import setup_logger
from src.utils.config import Config
from src.data.cache_manager import CacheManager
from src.data.odds_api import OddsAPIClient
from src.data.odds_matching import match_odds_to_games

logger = setup_logger(__name__)

def main():
    print("Loading configuration...")
    config = Config.load()
    
    if not config.ODDS_API_KEY or config.ODDS_API_KEY == "your_api_key_here":
        print("ERROR: ODDS_API_KEY not configured in .env")
        return

    print(f"API Key found: {config.ODDS_API_KEY[:4]}...{config.ODDS_API_KEY[-4:]}")
    
    cache_manager = CacheManager(config.CACHE_DIRECTORY)
    
    # 1. Load Teams
    print("Loading teams...")
    teams = cache_manager.load_teams()
    if not teams:
        print("Teams not in cache, cannot test matching.")
        return
    print(f"Loaded {len(teams)} teams.")

    # 2. Load Schedule
    print("Loading schedule...")
    games = cache_manager.load_schedule()
    if not games:
        print("Schedule not in cache, cannot test matching.")
        return
    
    # Filter for upcoming games to reduce noise
    upcoming_games = [g for g in games if not g.is_completed]
    print(f"Loaded {len(games)} games ({len(upcoming_games)} upcoming).")

    # 3. Fetch Odds
    client = OddsAPIClient(config.ODDS_API_KEY, "https://api.the-odds-api.com/v4")
    
    print("\nFetching odds from API...")
    try:
        odds_data = client.fetch_nfl_odds()
        print(f"Successfully fetched odds for {len(odds_data)} matchups.")
        
        if not odds_data:
            print("No odds returned. Is it the off-season?")
            # Try loading from cache if API returns nothing, just to check logic
            odds_data = cache_manager.load_odds()
            if odds_data:
                print(f"Loaded {len(odds_data)} odds from cache instead.")
            else:
                print("No odds in cache either.")
                return

        # Print some keys to see naming convention
        print("\nSample Odds Keys (Team Names from API):")
        for k in list(odds_data.keys())[:5]:
            print(f" - {k}")
            entry = odds_data[k]
            print(f"   Home: '{entry.get('home_team')}', Away: '{entry.get('away_team')}'")

        # 4. Test Matching
        print("\nTesting Matching Logic...")
        matched_count, unmatched_games, matched_details = match_odds_to_games(
            games, teams, odds_data, return_details=True
        )

        for detail in matched_details[:30]:
            print(
                f"WEEK {detail['week']}: {detail['away_team']} @ {detail['home_team']} "
                f"(ML: {detail['away_odds']} / {detail['home_odds']})"
            )

        print(f"\nUpdated odds for {matched_count} games")
        print(f"Failed to match {len(unmatched_games)} games (showing first 10):")
        for fail in unmatched_games[:10]:
            print(f" - {fail}")

    except Exception as e:
        print(f"Error fetching odds: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
