import sys
from pathlib import Path
import logging
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
from pydantic import BaseModel

# Add backend directory to path so we can import src
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from src.utils.logger import setup_logger
from src.utils.config import Config
from src.data.cache_manager import CacheManager
from src.data.espn_api import ESPNAPIClient
from src.data.odds_api import OddsAPIClient
from src.data.odds_matching import match_odds_to_games
from src.data.models import Team, Game
from src.simulation.monte_carlo import simulate_season, SimulationResult
from src.simulation.standings import calculate_standings

# Setup logging
logger = setup_logger(__name__)

# Global state
class AppState:
    def __init__(self):
        self.config = Config.load()
        self.cache_manager = CacheManager(self.config.CACHE_DIRECTORY)
        self.espn_client = ESPNAPIClient(
            base_url=self.config.ESPN_API_BASE_URL,
            core_api_url=self.config.ESPN_API_BASE_URL # Assuming same base for now
        )
        self.odds_client = OddsAPIClient(
            api_key=self.config.ODDS_API_KEY,
            base_url="https://api.the-odds-api.com/v4"
        )
        self.teams: List[Team] = []
        self.games: List[Game] = []
        self.simulation_result: Optional[SimulationResult] = None

state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data on startup."""
    logger.info("Loading data...")
    
    # Load teams
    state.teams = state.cache_manager.load_teams()
    if not state.teams:
        try:
            state.teams = state.espn_client.fetch_teams()
            state.cache_manager.save_teams(state.teams)
        except Exception as e:
            logger.error(f"Failed to load teams: {e}")
            state.teams = []

    # Load schedule
    state.games = state.cache_manager.load_schedule()
    if not state.games:
        try:
            state.games = state.espn_client.fetch_schedule()
            state.cache_manager.save_schedule(state.games)
        except Exception as e:
            logger.error(f"Failed to load schedule: {e}")
            state.games = []
            
    # Load odds
    odds_data = state.cache_manager.load_odds()
    if not odds_data and state.config.ODDS_API_KEY:
        try:
            logger.info("Fetching odds from API...")
            odds_data = state.odds_client.fetch_nfl_odds()
            if odds_data:
                state.cache_manager.save_odds(odds_data)
        except Exception as e:
            logger.error(f"Failed to fetch odds: {e}")
    
    # Match odds to games
    if odds_data and state.games:
        matched_count, unmatched_games, _ = match_odds_to_games(
            state.games, state.teams, odds_data
        )
        if unmatched_games:
            logger.info(
                "Odds API covered %d matchups; %d upcoming games had no odds data (showing first 5): %s",
                matched_count,
                len(unmatched_games),
                unmatched_games[:5],
            )
            
    # Load overrides
    overrides = state.cache_manager.load_overrides()
    if overrides:
        # Apply overrides to games
        game_map = {g.id: g for g in state.games}
        for game_id, override_data in overrides.items():
            if game_id in game_map:
                game = game_map[game_id]
                game.is_overridden = True
                game.override_home_score = override_data.get("home_score")
                game.override_away_score = override_data.get("away_score")
                game.override_home_moneyline = override_data.get("home_moneyline")
                game.override_away_moneyline = override_data.get("away_moneyline")
                # Add other override fields as needed

    logger.info(f"Loaded {len(state.teams)} teams and {len(state.games)} games")
    yield
    # Clean up resources if needed

app = FastAPI(title="NFL Monte Carlo API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/status")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok", 
        "message": "NFL Monte Carlo Backend is running",
        "teams_loaded": len(state.teams),
        "games_loaded": len(state.games)
    }

@app.get("/standings")
async def get_standings():
    """Get current standings based on actual results."""
    if not state.teams or not state.games:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    standings = calculate_standings(state.games, state.teams)
    
    # Convert to list for JSON response
    standings_list = []
    for team_id, standing in standings.items():
        team = next((t for t in state.teams if t.id == team_id), None)
        standings_list.append({
            "team_id": team_id,
            "team_name": team.name if team else "Unknown",
            "wins": standing.wins,
            "losses": standing.losses,
            "ties": standing.ties,
            "win_percentage": standing.win_percentage,
            "division_wins": standing.division_wins,
            "division_losses": standing.division_losses,
            "division_ties": standing.division_ties,
            "conference_wins": standing.conference_wins,
            "conference_losses": standing.conference_losses,
            "conference_ties": standing.conference_ties,
            "points_for": standing.points_for,
            "points_against": standing.points_against,
            "net_points": standing.net_points,
        })
        
    return standings_list

@app.get("/teams")
async def get_teams():
    """Get all teams."""
    if not state.teams:
        raise HTTPException(status_code=503, detail="Data not loaded")
    return [state.cache_manager._serialize_team(t) for t in state.teams]

@app.get("/schedule")
async def get_schedule(week: Optional[int] = None):
    """Get schedule, optionally filtered by week."""
    if not state.games:
        raise HTTPException(status_code=503, detail="Data not loaded")
        
    games = state.games
    if week is not None:
        games = [g for g in games if g.week == week]
        
    # Serialize games
    return [state.cache_manager._serialize_game(g) for g in games]

class SimulateRequest(BaseModel):
    num_simulations: int = 10000
    random_seed: Optional[int] = None
    remove_vig: bool = True
    use_odds: bool = True

@app.post("/simulate")
async def run_simulation(request: SimulateRequest, background_tasks: BackgroundTasks):
    """Run Monte Carlo simulation."""
    if not state.teams or not state.games:
        raise HTTPException(status_code=503, detail="Data not loaded")

    # Run simulation synchronously for now (it's fast enough for <10k)
    # For larger sims, we might want to offload to a thread/process
    try:
        result = simulate_season(
            games=state.games,
            teams=state.teams,
            num_simulations=request.num_simulations,
            random_seed=request.random_seed,
            remove_vig=request.remove_vig,
            use_odds=request.use_odds
        )
        state.simulation_result = result
        
        # Serialize result
        response = {
            "num_simulations": result.num_simulations,
            "execution_time": result.execution_time_seconds,
            "team_stats": {}
        }
        
        for team_id, stats in result.team_stats.items():
            response["team_stats"][team_id] = {
                "playoff_probability": stats.playoff_probability,
                "division_win_probability": stats.division_win_probability,
                "first_seed_probability": stats.first_seed_probability,
                "average_wins": stats.average_wins,
                "seed_probabilities": stats.seed_probabilities
            }
            
        return response
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class OverrideRequest(BaseModel):
    game_id: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    home_moneyline: Optional[int] = None
    away_moneyline: Optional[int] = None
    is_overridden: bool = True

@app.post("/override")
async def set_override(request: OverrideRequest):
    """Set override for a game."""
    game = next((g for g in state.games if g.id == request.game_id), None)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    game.is_overridden = request.is_overridden
    if request.is_overridden:
        game.override_home_score = request.home_score
        game.override_away_score = request.away_score
        game.override_home_moneyline = request.home_moneyline
        game.override_away_moneyline = request.away_moneyline
    
    # Save overrides to cache
    overrides = state.cache_manager.load_overrides()
    if request.is_overridden:
        overrides[request.game_id] = {
            "home_score": request.home_score,
            "away_score": request.away_score,
            "home_moneyline": request.home_moneyline,
            "away_moneyline": request.away_moneyline
        }
    else:
        overrides.pop(request.game_id, None)
        
    state.cache_manager.save_overrides(overrides)
    
    return {"status": "success", "game": state.cache_manager._serialize_game(game)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
