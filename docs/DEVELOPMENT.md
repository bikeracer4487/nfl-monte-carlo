# Development Guide

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd nfl-monte-carlo
```

### 2. Create virtual environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements-dev.txt
```

### 4. Configure environment (optional)

Create a `.env` if you want to override defaults such as `LOG_LEVEL` or `CACHE_DIRECTORY`. The application no longer requires any third-party API keys.

### 5. Run tests

```bash
pytest
```

## Project Structure

```
nfl-monte-carlo/
├── src/
│   ├── data/           # Data layer (API, caching, models)
│   ├── utils/          # Utilities (logging, config)
│   ├── gui/            # GUI (Phase 4+)
│   └── simulation/     # Monte Carlo simulation (Phase 2+)
├── tests/              # Test suite
├── data/               # Cache directory
├── docs/               # Documentation
└── resources/          # Logos, fonts, styles (Phase 6+)
```

## Development Workflow

### Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
# or
start htmlcov/index.html  # Windows

# Specific test file
pytest tests/test_models.py

# Specific test
pytest tests/test_models.py::TestTeam::test_team_creation

# Skip slow tests
pytest -m "not slow"
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/
```

### Debugging

Enable debug logging in `.env`:

```
LOG_LEVEL=DEBUG
```

## Simulation Progress & Cancellation

The web UI now uses asynchronous simulation jobs so we can show live progress and allow cancellation:

- Backend orchestrator: `backend/api/simulation_jobs.py`
  - `POST /simulation-jobs` starts a job and returns `job_id`, status, and initial progress (0%).
  - `GET /simulation-jobs/{job_id}` returns current progress (`0-100`), status (`pending`, `running`, `completed`, `cancelled`, `error`), and the serialized `SimulationResult` once complete.
  - `DELETE /simulation-jobs/{job_id}` signals cancellation via a threading event. `simulate_season()` accepts a `cancel_callback` and raises `SimulationCancelledError` so jobs stop cleanly.
  - Only one job may run at a time; new requests while another job is active receive HTTP `409`.

- Frontend workflow: `frontend/src/pages/Simulation.tsx`
  - Clicking “Run Simulation” calls `startSimulationJob()` and begins polling every second via `getSimulationJob()`.
  - A progress bar and status text display percentage complete and automatically switch from “seconds” to “minutes” messaging when `num_simulations >= 100_000`.
  - The “Cancel” button issues `cancelSimulationJob()`. When cancellation completes, the UI surfaces the cancelled state; otherwise, successful runs display the results table using `job.result`.

When adding new clients (CLI, GUI, etc.), prefer this job API so every surface gets consistent progress reporting and cancellation semantics.

## Phase 1 Progress

### Completed ✅

- [x] Project structure created
- [x] Dependencies configured
- [x] Logger utility implemented
- [x] Configuration manager implemented
- [x] Data models created (Team, Game, Standing)
- [x] ESPN API wrapper implemented
- [x] Cache manager implemented
- [x] Schedule loader implemented
- [x] Unit tests written
- [x] Documentation complete

### Testing

Run the demo script to verify Phase 1 functionality:

```bash
python demo_phase1.py
```

## Next Steps

After completing Phase 1, proceed to:

**Phase 2**: Monte Carlo Simulation Engine
- Implement basic simulation algorithm
- Simulate remaining games as unbiased coin flips
- Calculate standings

**Phase 3**: NFL Tiebreaker Logic
- Implement all 12 tiebreaker rules
- Handle multi-team ties
- Validate against historical data

**Phase 4**: GUI Foundation
- Create main window with PySide6
- Implement standings table view
- Add navigation controls

## Troubleshooting

### Import errors

Make sure you're running from the project root:
```bash
python -m pytest  # Instead of just pytest
```

### Virtual environment not activated

```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### Cache permission errors

Delete and recreate cache directory:
```bash
rm -rf data/*.json
```

## Contributing

1. Create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass
4. Run code formatting (black)
5. Submit pull request

## Resources

- [PySide6 Documentation](https://doc.qt.io/qtforpython-6/)
- [NFL Tiebreaker Rules](https://operations.nfl.com/the-rules/nfl-tie-breaking-procedures/)
