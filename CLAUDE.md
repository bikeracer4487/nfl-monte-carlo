# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Desktop application using Monte Carlo simulations to estimate NFL playoff probabilities using unbiased 50/50 coin flips for remaining games. Built with Python 3.11+, PySide6 (Qt), NumPy, and Numba. Currently through Phase 4 (data layer, simulation engine, tiebreaker logic, and GUI foundation complete).

## Quick Commands

```bash
# Run GUI application
python main.py

# Run Phase 1 demo (data layer)
python demo_phase1.py

# Run Phase 2 demo (Monte Carlo simulation)
python demo_phase2.py

# Testing
pytest                           # All tests
pytest --cov=src                 # With coverage
pytest -m "not api"              # Skip API tests (faster)
pytest tests/test_tiebreakers.py # Specific module

# Code quality
black src/ tests/                # Format code
flake8 src/ tests/               # Lint
```

## Architecture Overview

### Layer Responsibilities

**Data Layer** (`src/data/`)
- ESPN API integration for schedule and game results
- Aggressive JSON-based caching to minimize API calls
- Dataclass models: `Team`, `Game`, `Standing`
- Override system for "what if" scenarios

**Simulation Engine** (`src/simulation/`)
- Monte Carlo simulation using NumPy vectorization (~1,000 sims/sec with tiebreakers)
- Treats all remaining games as unbiased 50/50 coin flips
- Poisson-based score generation for point differential tiebreakers
- Implements 11 of 12 NFL tiebreaker rules (skipped TD differential)
- Playoff seeding (1-7 seeds per conference)

**GUI Layer** (`src/gui/`)
- PySide6 (Qt) with modern dark theme
- Qt Model/View architecture for efficient table rendering
- QThread-based background processing for data refresh and simulations
- Three main views: Standings, Simulation Results, Schedule Editor
- Custom font loading (Inter font family)
- Card-based layouts with vertical scrolling

**Utilities** (`src/utils/`)
- Environment-based configuration (`.env` → `Config` class)
- Centralized logging with configurable levels

### Data Flow

1. **Initial Load**: CacheManager → Load cached teams/schedule → Populate GUI
2. **Data Refresh**: ESPNAPIClient (background thread) → Update cache → Refresh views
3. **Simulation**: Treat each remaining matchup as 50/50 → NumPy vectorized random outcomes → Calculate standings with tiebreakers → Aggregate statistics
4. **Overrides**: User edits game → Store in `Game.override_*` fields → Simulations use overrides when active

## Critical Design Patterns

### Caching Strategy

The `CacheManager` is central to the app's offline capability and API quota management:

```python
# Cache files in data/ directory (gitignored):
data/schedule_2025.json       # Fetch once per season
data/results_current.json     # Update 2-3x per week
data/teams.json               # Fetch once per season
data/user_overrides.json      # User's "what if" scenarios
```

**Always use `force_refresh=False` by default** to respect caching. Force refresh only on explicit user action.

### Override System

Games support dual-value pattern for "what if" scenarios:

```python
# Game model has both actual and override fields
game.home_score              # Actual score
game.override_home_score     # User override
game.is_overridden          # Flag to use overrides

# Use helper methods to get effective values
home_score, away_score = game.get_effective_scores()
```

**When implementing features**: Always respect overrides by using `get_effective_*()` methods.

### Qt Model/View for Performance

GUI tables use Qt's Model/View pattern for efficient rendering:

```python
# standings_view.py uses StandingsModel (QAbstractTableModel)
# - Separates data from presentation
# - Only creates widgets for visible rows (performance)
# - Supports sorting without duplicating data

# When adding new table views, follow this pattern:
# 1. Create model inheriting QAbstractTableModel
# 2. Implement data(), rowCount(), columnCount(), headerData()
# 3. Use QTableView to display model
```

### Background Threading Pattern

Long-running operations use QThread to prevent UI blocking:

```python
# Pattern used in main_window.py for data refresh:
worker = DataRefreshWorker(...)  # QObject with run() method
thread = QThread()
worker.moveToThread(thread)

# Connect signals: started, finished, progress, error
thread.started.connect(worker.run)
worker.finished.connect(self.on_complete)
worker.progress.connect(self.update_status)

thread.start()
```

**Use this pattern for**: Simulations, API calls, heavy computations

## Tiebreaker Logic (Phase 3)

The `tiebreakers.py` module implements NFL's complex tiebreaker rules. This is the **most intricate part of the codebase**.

### Key Functions

- `seed_conference_playoffs()`: Main entry point for playoff seeding (1-7 per conference)
- `determine_division_winners()`: Determines division winners with tiebreakers
- `apply_division_tiebreaker()`: 2-team same-division ties
- `apply_multi_team_division_tiebreaker()`: 3+ team same-division ties
- `apply_wild_card_tiebreaker()`: Wild card spot resolution

### Tiebreaker Order (11 rules implemented)

1. Head-to-head record
2. Division record
3. Common games record (minimum 4)
4. Conference record
5. Strength of victory (win % of beaten teams)
6. Strength of schedule (win % of all opponents)
7. Best combined ranking in points scored/allowed (conference)
8. Best combined ranking in points scored/allowed (all teams)
9. Best net points in common games
10. Best net points in all games
11. ~~Best net touchdowns in all games~~ (SKIPPED - rule 11)
12. Coin toss (random)

**When debugging playoff seeding issues**: Check tiebreaker.py logic carefully. Use test cases in `test_tiebreakers.py` as examples.

## Performance Targets

- **10,000 simulations**: < 10 seconds (currently ~10 sec with full tiebreakers)
- **Initial app load**: < 2 seconds
- **Data refresh**: 3-5 seconds (ESPN API latency)
- **GUI responsiveness**: Never block main thread (use QThread)

**Optimization approach**: NumPy vectorization first, then Numba JIT if needed. Profile before optimizing.

## Testing Strategy

### Markers

```python
@pytest.mark.api       # Real API calls (slow, requires keys)
@pytest.mark.slow      # Long-running tests
@pytest.mark.unit      # Fast unit tests
@pytest.mark.integration  # Cross-module tests
```

### Coverage Requirements

- Minimum 80% coverage (`pytest.ini`: `--cov-fail-under=80`)
- Current coverage: ~97% for simulation modules

### Key Test Files

- `test_tiebreakers.py`: Critical - validates all 11 tiebreaker rules
- `test_monte_carlo.py`: Validates simulation accuracy and performance
- `conftest.py`: Shared fixtures (mock teams, games, standings)

**When adding features**: Write tests first, especially for tiebreaker logic changes.

## Configuration & Environment

### Required Environment Variables (.env)

```bash
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
```

### Config Class Usage

```python
from src.utils.config import Config

config = Config.load()
config.CACHE_DIRECTORY        # pathlib.Path to data/ directory
config.ESPN_API_BASE_URL      # ESPN API endpoint
```

## Common Workflows

### Adding a New View to GUI

1. Create view class in `src/gui/` inheriting from `QWidget`
2. If table-based, create model class in `src/gui/models/` inheriting from `QAbstractTableModel`
3. Add tab in `main_window.py`:
   ```python
   self.new_view = NewView()
   self.tabs.addTab(self.new_view, "View Name")
   ```
4. Apply styling from `styles.py` (DARK_THEME constant)
5. Use vertical layouts with `QVBoxLayout` to avoid horizontal scrolling

### Running Simulations

```python
from src.simulation.monte_carlo import simulate_season

result = simulate_season(
    games=games,           # List[Game]
    teams=teams,           # List[Team]
    num_simulations=10000,
    random_seed=None,      # Set for reproducibility
    remove_vig=True        # Remove bookmaker's margin
)

# Access results
stats = result.get_team_stats(team_id)
playoff_prob = stats.playoff_probability
avg_wins = stats.average_wins
seed_probs = stats.seed_probabilities  # Dict[int, float]
```

### Modifying Tiebreaker Logic

**WARNING**: Tiebreaker changes are high-risk. Follow this process:

1. Read NFL official rules: https://www.nfl.com/standings/tie-breaking-procedures
2. Add test case to `test_tiebreakers.py` demonstrating the scenario
3. Modify logic in `tiebreakers.py`
4. Run full test suite: `pytest tests/test_tiebreakers.py -v`
5. Validate against historical NFL scenarios (2024 season data)

## GUI Styling & Layout

### Modern Dark Theme

The GUI uses a comprehensive dark theme (`src/gui/styles.py`):
- Dark backgrounds (#121212, #1E1E1E, #252525)
- Modern blue accent (#2196F3)
- NFL official colors for secondary accents
- Custom Inter Variable font family
- Card-based layouts with drop shadows

### Layout Best Practices

- **Use vertical layouts** (`QVBoxLayout`) to avoid horizontal scrolling
- Division view: 8 cards stacked vertically (not 2x4 grid)
- Conference view: AFC and NFC stacked vertically (not side-by-side)
- Always disable horizontal scrollbar: `scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)`
- Set reasonable `setMaximumHeight()` on tables to prevent excessive expansion

## Development Phases (for Context)

- **Phase 1 ✅**: Data foundation & API integration
- **Phase 2 ✅**: Monte Carlo simulation engine
- **Phase 3 ✅**: NFL tiebreaker logic
- **Phase 4 ✅**: GUI foundation (Standings, Simulation, Schedule views with modern dark theme)
- **Phase 5** (Next): Simulation integration with GUI
- **Phase 6**: Schedule editor & override system
- **Phase 7**: Polish & theming (light mode, team logos)
- **Phase 8**: Distribution (PyInstaller executables)

## Important Gotchas

1. **Always use absolute paths** when working with cache files (not relative)
2. **Respect overrides**: Use `game.get_effective_*()` methods, not direct attribute access
3. **ESPN API is unofficial**: Can break without notice. Cache aggressively.
4. **Qt threading**: Never update GUI from worker threads. Use signals/slots.
5. **Tiebreaker coin toss**: Uses Python's random, so set seed for reproducible tests
6. **Win percentage calculation**: Ties count as 0.5 wins (see `Standing.win_percentage`)
7. **Test isolation**: Clear cache between tests to avoid state pollution
8. **NumPy random state**: Simulations use np.random. Set seed for reproducibility.
9. **GUI layouts**: Prefer vertical scrolling over horizontal. Use `QVBoxLayout` for card-based views.
10. **Font loading**: Custom fonts loaded in `main.py` before creating QApplication

## Documentation Resources

- PROJECT_PLAN.md: Complete 8-phase implementation roadmap
- docs/API_SETUP.md: How to get The Odds API key
- docs/DEVELOPMENT.md: Setup and testing guide
- NFL Tiebreaker Rules: https://www.nfl.com/standings/tie-breaking-procedures

## Code Style Conventions

- **Dataclasses** for models (Team, Game, Standing, SimulationResult)
- **Type hints** on all function signatures
- **Docstrings** on all public functions (Google style)
- **Black** for code formatting (line length: 88)
- **Import order**: stdlib → third-party → local (relative imports within src/)
- **Logging**: Use module-level logger via `setup_logger(__name__)`
- **Qt imports**: Use PySide6.QtWidgets, PySide6.QtCore, PySide6.QtGui
- **No emojis** in code or commits unless explicitly requested by user

## Documentation Practices

### Maintain DEVELOPMENT_NOTES.md

Keep a detailed internal documentation file (`DEVELOPMENT_NOTES.md`) that captures:

**Key Design Decisions**
- Architectural choices and rationale
- Why certain approaches were chosen over alternatives
- Trade-offs considered and made
- Performance optimization decisions

**Implementation Details**
- Complex algorithm explanations (especially tiebreakers)
- Integration patterns between layers
- Threading and concurrency approaches
- Caching strategies and invalidation logic

**Setup and Configuration**
- Environment setup steps
- API key configuration
- Development environment requirements
- Common setup issues and solutions

**Usage Guidelines**
- How to run different components
- Testing strategies for specific features
- Debugging tips for complex scenarios
- Performance profiling approaches

**Evolution and Changes**
- Date-stamped entries for major changes
- Migration notes when refactoring
- Deprecated patterns and replacements
- Lessons learned from issues

**Future Improvements**
- Known limitations and workarounds
- Technical debt items
- Performance enhancement opportunities
- Feature ideas and architectural improvements

### Documentation Workflow

1. **Document as you build** - Add entries during development, not after
2. **Be specific** - Include code examples, file references, line numbers
3. **Explain the "why"** - Context gets lost over time; capture reasoning
4. **Keep it organized** - Use clear sections and date stamps
5. **Link to code** - Reference specific files, commits, or pull requests

### Use for Public Documentation

DEVELOPMENT_NOTES.md serves as the source material for:
- README.md updates
- User-facing documentation
- Architecture diagrams
- Setup guides

**Workflow**: Internal notes → Refined and simplified → Public README

This ensures public documentation is accurate, comprehensive, and maintains context without exposing internal implementation details unnecessarily.
