# Building Production Executables

This guide explains how to produce **production-ready executables** for the NFL Monte Carlo application. The application consists of two parts:
1.  **Python Backend**: A FastAPI server compiled into a single executable using PyInstaller.
2.  **Electron Frontend**: A React application bundled with Electron, which manages the backend process.

The final output is a single installer or executable (depending on platform) that contains everything needed to run the app.

---

## Prerequisites

-   **Node.js** (v18+)
-   **Python** (v3.11+)
-   **Git**

## 1. Build Environment Setup

### Backend Setup
Create a virtual environment and install dependencies:

```bash
# In project root
python -m venv venv
# Activate it:
# Windows: .\venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r backend/requirements.txt
pip install pyinstaller
```

### Frontend Setup
Install Node.js dependencies:

```bash
cd frontend
npm install
cd ..
```

---

## 2. Build Process

The build process is a two-step operation: first build the backend, then build the frontend which bundles the backend.

### Step 1: Build Python Backend

This step compiles the Python code into a standalone executable.

**Windows:**
```powershell
# From project root, with venv activated
pyinstaller backend/api.spec
```
*Output:* `dist/nfl_api_server.exe`

**macOS:**
```bash
# From project root, with venv activated
pyinstaller backend/api.spec
```
*Output:* `dist/nfl_api_server`

### Step 2: Build Electron Application

This step packages the React app and bundles the Python executable created in Step 1.

**Windows:**
```powershell
cd frontend
npm run electron:build
```
*Output:* `frontend/dist/NFL Monte Carlo Setup X.X.X.exe` (Installer) and `frontend/dist/win-unpacked/`

**macOS:**
```bash
cd frontend
npm run electron:build
```
*Output:* `frontend/dist/NFL Monte Carlo-X.X.X.dmg`

---

## 3. How It Works

1.  **PyInstaller** analyzes `backend/api/server.py` and bundles it along with all Python dependencies (NumPy, Numba, FastAPI, etc.) into a single executable.
2.  **Electron Builder** (configured in `frontend/package.json`) takes this executable from the repository-level `dist/` folder and places it into the `resources` directory of the final Electron app.
3.  **At Runtime**: The Electron main process (`main.cjs`) detects it is in production mode, locates the Python executable in `process.resourcesPath`, and spawns it as a child process.

## 4. Troubleshooting

### Backend Build Fails
-   Ensure all dependencies are installed in your venv.
-   Check `backend/build/nfl_api_server/warn-nfl_api_server.txt` for missing imports.
-   Try running the generated executable manually: `.\backend\dist\nfl_api_server.exe` to see if it starts successfully.

### Frontend Build Fails
-   Ensure the backend executable exists at `../dist/nfl_api_server.exe` (Windows) or `../dist/nfl_api_server` (Mac) before running `npm run electron:build`.
-   Check for permission issues.

### App Starts but "Backend not found"
-   Check the application logs (console) if possible.
-   Ensure the `extraResources` configuration in `package.json` matches the actual filename of your Python executable.
