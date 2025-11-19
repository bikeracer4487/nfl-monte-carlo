# NFL Monte Carlo Simulation

A modern desktop application that uses Monte Carlo simulations to estimate NFL team playoff probabilities by treating every remaining matchup as an unbiased 50/50 coin flip.

## Architecture

This application uses a hybrid architecture:
- **Backend**: Python (FastAPI) for heavy computation, data management, and Monte Carlo simulations (NumPy/Numba).
- **Frontend**: Electron + React + TypeScript for a modern, responsive user interface.

## Project Status

**Phase 1-3: Complete ✅** - Data Foundation, Simulation Engine, Tiebreaker Logic
**Phase 4: In Progress 🔄** - Modern GUI (Electron + React)

## Features

- **Monte Carlo Simulations**: Run thousands of season simulations to estimate playoff probabilities
- **Unbiased Outcomes**: All remaining games are simulated as fair 50/50 coin flips for consistent projections
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

**Important:** Create the virtual environment in the **project root** directory, not inside `backend/`.

```bash
# From project root:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 2. Setup Frontend

```bash
cd frontend
npm install
```

### 3. Run Application

**Development Mode:**

Run the following command in the `frontend` directory:

```bash
cd frontend
npm start
```
This single command will:
1. Start the Vite development server (frontend)
2. **Automatically launch the Python backend** (using the venv detected in root)
3. Launch the Electron application

**Troubleshooting:**
- If you see port errors (e.g., `[winerror 10048]`), ensure no other instances of the backend are running.
- The backend logs will appear in the Electron console window.

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
