# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Desktop application using Monte Carlo simulations to estimate NFL playoff probabilities using unbiased 50/50 coin flips for remaining games.
**Architecture**: Hybrid Electron + React frontend with Python (FastAPI/NumPy) backend.

## Quick Commands

```bash
# Setup (First time)
python -m venv venv
.\venv\Scripts\activate      # Windows
source venv/bin/activate     # Mac/Linux
pip install -r backend/requirements.txt
cd frontend && npm install

# Development (Run entire app)
cd frontend
npm start           # Starts React dev server, Electron, and Python backend automatically

# Backend-only Dev
cd backend
uvicorn api.server:app --reload

# Testing
pytest                           # All tests
pytest --cov=src                 # With coverage
pytest -m "not api"              # Skip API tests (faster)

# Code quality
black backend/src/ tests/        # Format code
flake8 backend/src/ tests/       # Lint
```

## Architecture Overview

### Layer Responsibilities

**Backend** (`backend/`)
- **API**: FastAPI server (`api/server.py`)
- **Data Layer** (`src/data/`): ESPN API integration, JSON caching
- **Simulation Engine** (`src/simulation/`): Monte Carlo simulations (NumPy/Numba)
- **Models**: Dataclasses for Teams, Games, Standings

**Frontend** (`frontend/`)
- **Electron**: Main process, backend orchestration (`electron/main.cts`)
- **React**: UI components, routing, state management
- **Styling**: Tailwind CSS
- **API Client**: `lib/api.ts` for communicating with Python backend

### Data Flow

1. **App Start**: Electron launches; spawns Python backend process.
2. **Data Load**: React queries Backend API (`GET /status`, `GET /teams`, `GET /schedule`).
3. **Simulation**: User triggers sim -> POST `/simulate` -> Backend runs NumPy sim -> Returns results.
4. **Updates**: User edits schedule -> POST `/override` -> Backend updates cache.

## Critical Design Patterns

### Caching Strategy

The `CacheManager` (backend) is central to offline capability:
```python
# Cache files in data/ directory:
data/schedule_2025.json       # Fetch once per season
data/results_current.json     # Update 2-3x per week
data/teams.json               # Fetch once per season
data/user_overrides.json      # User's "what if" scenarios
```

### Build System

- **Backend**: PyInstaller compiles `api/server.py` to a single executable.
- **Frontend**: Electron Builder packages React app and bundles the Backend executable.
- **Production**: Electron detects packaged environment and spawns the bundled backend executable from `resources/`.

## Code Style Conventions

- **Python**: Black formatting, Google-style docstrings, Type hints.
- **TypeScript/React**: Functional components, Hooks, Tailwind CSS classes.
- **Import order**: Stdlib -> 3rd party -> Local.
