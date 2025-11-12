# NFL Monte Carlo Simulation

A desktop application that uses Monte Carlo simulations to estimate NFL team playoff probabilities based on Vegas odds-weighted game outcomes.

## Project Status

**Phase 1: Complete ✅** - Data Foundation & API Integration

## Features (Planned)

- **Monte Carlo Simulations**: Run thousands of season simulations to estimate playoff probabilities
- **Vegas Odds Integration**: Weight game outcomes by current betting lines
- **Multiple Views**:
  - Simulation results (playoff odds, division odds, #1 seed odds)
  - Current NFL standings
  - Schedule editor with manual overrides
- **"What If" Scenarios**: Override any game outcome to explore different scenarios
- **Light/Dark Mode**: Toggle between themes
- **Cross-Platform**: Windows and macOS executables

## Technology Stack

- **Language**: Python 3.11+
- **GUI**: PySide6 (Qt for Python)
- **Computation**: NumPy + Numba for performance
- **APIs**:
  - ESPN API (game results, schedule, teams)
  - The Odds API (betting lines)

## Phase 1: Data Foundation ✅

Phase 1 is complete! The data layer is fully functional:

- ✅ ESPN API wrapper for fetching schedule, results, and teams
- ✅ The Odds API wrapper for fetching betting lines
- ✅ Comprehensive caching system to minimize API calls
- ✅ Data models for teams, games, and standings
- ✅ Configuration management
- ✅ Test suite with >80% coverage
- ✅ Complete documentation

## Quick Start

### 1. Setup

```bash
# Clone repository
git clone <your-repo-url>
cd nfl-monte-carlo

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ODDS_API_KEY (optional)
```

### 2. Get API Key (Optional)

To fetch betting odds:
1. Sign up at https://the-odds-api.com/ (free tier: 500 calls/month)
2. Get your API key
3. Add to `.env`: `ODDS_API_KEY=your_key_here`

ESPN API requires no setup - it's free and open!

### 3. Run Demo

```bash
python demo_phase1.py
```

This will:
- Fetch NFL teams and 2025 schedule from ESPN
- Cache data locally
- Fetch current odds (if configured)
- Display team organization and schedule summary

### 4. Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Skip API tests (faster)
pytest -m "not api"
```

## Project Structure

```
nfl-monte-carlo/
├── src/
│   ├── data/           # Data layer (ESPN API, Odds API, caching)
│   ├── utils/          # Utilities (logging, config)
│   ├── gui/            # GUI components (Phase 4+)
│   └── simulation/     # Monte Carlo engine (Phase 2+)
├── tests/              # Comprehensive test suite
├── data/               # Cache directory (gitignored)
├── docs/               # Documentation
└── resources/          # Team logos, fonts (Phase 6+)
```

## Development Roadmap

### Phase 2: Monte Carlo Simulation Engine (Next)
- Implement basic simulation algorithm
- Convert odds to probabilities
- Calculate simple standings

### Phase 3: NFL Tiebreaker Logic
- Implement all 12 tiebreaker rules
- Handle multi-team ties
- Validate against historical data

### Phase 4: GUI Foundation
- Create main window with PySide6
- Implement standings table view
- Add navigation controls

### Phase 5: Simulation Integration
- Connect simulation to GUI
- Add progress bar and controls
- Display results

### Phase 6: Schedule Editor & Overrides
- Implement schedule editing
- Add override system
- Handle refresh conflicts

### Phase 7: Polish & Theming
- Implement dark mode
- Add team logos and branding
- Final polish

### Phase 8: Distribution
- Create Windows/macOS executables
- Code signing (optional)
- Release packages

## Documentation

- [API Setup Guide](docs/API_SETUP.md) - How to get API keys
- [Development Guide](docs/DEVELOPMENT.md) - Development workflow
- [Project Plan](PROJECT_PLAN.md) - Complete implementation plan

## Contributing

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for development setup and workflow.

## License

TBD

## Acknowledgments

- ESPN for providing free NFL data
- The Odds API for betting lines
- NFL for the game we love