# NFL Monte Carlo Simulation

A modern desktop application that uses Monte Carlo simulations to estimate NFL team playoff probabilities based on Vegas odds-weighted game outcomes.

## Architecture

This application uses a hybrid architecture:
- **Backend**: Python (FastAPI) for heavy computation, data management, and Monte Carlo simulations (NumPy/Numba).
- **Frontend**: Electron + React + TypeScript for a modern, responsive user interface.

## Project Status

**Phase 1-3: Complete ✅** - Data Foundation, Simulation Engine, Tiebreaker Logic
**Phase 4: In Progress 🔄** - Modern GUI (Electron + React)

## Features

- **Monte Carlo Simulations**: Run thousands of season simulations to estimate playoff probabilities
- **Vegas Odds Integration**: Weight game outcomes by current betting lines
- **Interactive UI**:
  - **Standings**: View current NFL standings with advanced stats
  - **Schedule**: View and edit schedule with manual overrides
  - **Simulation**: Run simulations and view detailed probability breakdowns
- **Cross-Platform**: Runs on Windows and macOS

## Quick Start

### Prerequisites
- Node.js (v18+)
- Python (v3.11+)

### 1. Setup Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Setup Frontend

```bash
cd frontend
npm install
```

### 3. Run Application

**Development Mode:**

Terminal 1 (Backend):
```bash
cd backend
source venv/bin/activate
python api/server.py
```

Terminal 2 (Frontend):
```bash
cd frontend
npm start
```
(This runs both the Vite dev server and the Electron app)

## Project Structure

```
nfl-monte-carlo/
├── backend/            # Python Backend
│   ├── api/            # FastAPI server
│   ├── src/            # Core logic (Data, Simulation)
│   └── tests/          # Python tests
├── frontend/           # Electron + React Frontend
│   ├── electron/       # Electron main process
│   ├── src/            # React UI components
│   └── ...
└── ...
```

## Documentation

- [API Setup Guide](docs/API_SETUP.md) - How to get API keys
- [Development Guide](docs/DEVELOPMENT.md) - Development workflow
- [Project Plan](PROJECT_PLAN.md) - Complete implementation plan
