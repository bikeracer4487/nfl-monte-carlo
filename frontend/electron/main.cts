import { app, BrowserWindow, Menu, dialog } from 'electron';
import path from 'path';
import { spawn, ChildProcess } from 'child_process';
import fs from 'fs';

// Important: Disable node integration and enable context isolation for security
// and to prevent conflicts with global 'module' or 'exports'.
let mainWindow: BrowserWindow | null;
let pythonProcess: ChildProcess | null = null;

function createWindow() {
  const isDev = !app.isPackaged;

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    title: "NFL Monte Carlo Simulation",
    backgroundColor: "#121212", // Dark theme background
  });

  Menu.setApplicationMenu(null);

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startPythonBackend() {
  const isDev = !app.isPackaged;

  if (isDev) {
    // Navigate from dist-electron/main.js to project root
    // dist-electron -> frontend -> root
    const rootDir = path.join(__dirname, '../../'); 
    const backendPath = path.join(rootDir, 'backend/api/server.py');
    
    console.log('Project Root:', rootDir);
    console.log('Backend Script:', backendPath);
    
    // Determine python executable
    let pythonExecutable = process.platform === 'win32' ? 'python' : 'python3';
    
    // Kill any existing python processes started by us (cleanup)
    // Note: This is harder to do robustly without PID tracking, but we'll rely on the
    // 'will-quit' handler for cleanup. The user might need to manually kill zombie processes
    // if the app crashed previously.

    const possiblePaths = process.platform === 'win32' ? [
        path.join(rootDir, 'venv', 'Scripts', 'python.exe'),
        path.join(rootDir, '.venv', 'Scripts', 'python.exe'),
    ] : [
        path.join(rootDir, 'venv', 'bin', 'python'),
        path.join(rootDir, '.venv', 'bin', 'python'),
    ];

    let found = false;
    for (const p of possiblePaths) {
        if (fs.existsSync(p)) {
            pythonExecutable = p;
            found = true;
            break;
        }
    }

    if (!found) {
        console.log('Virtual environment not found. Checked paths:', possiblePaths);
        console.log(`Falling back to system python: ${pythonExecutable}`);
    }

    console.log(`Starting Python backend with: ${pythonExecutable}`);
    
    // Check if port 8000 is in use (basic check, better would be to find an open port)
    // For now, we just launch and let it fail if bound, but we can catch the error in the logs.

    const backendPort = process.env.PORT || '8000';

    pythonProcess = spawn(pythonExecutable, [backendPath], {
      cwd: rootDir,
      stdio: 'inherit', // Pipe output to console
      env: {
        ...process.env,
        PORT: backendPort,
        PYTHONUNBUFFERED: '1' // Force stdout flush for better logging
      }
    });

    pythonProcess.on('error', (err) => {
      console.error('Failed to start Python backend:', err);
    });
    
    pythonProcess.on('exit', (code, signal) => {
        console.log(`Python backend exited with code ${code} and signal ${signal}`);
    });
  } else {
    // Production logic (executable)
    const possibleNames = [
        'nfl_api_server.exe',
        'nfl_api_server'
    ];
    
    let binaryPath = '';
    
    // 1. Check process.resourcesPath (where extraResources are placed)
    for (const name of possibleNames) {
        const p = path.join(process.resourcesPath, name);
        if (fs.existsSync(p)) {
            binaryPath = p;
            break;
        }
    }

    // 2. Fallback: check adjacent to executable (dev builds sometimes)
    if (!binaryPath) {
        for (const name of possibleNames) {
             const p = path.join(path.dirname(app.getPath('exe')), name);
             if (fs.existsSync(p)) {
                 binaryPath = p;
                 break;
             }
        }
    }
    
    if (binaryPath) {
        console.log(`Starting production Python backend: ${binaryPath}`);
        const backendPort = process.env.PORT || '8000';
        
        pythonProcess = spawn(binaryPath, [], {
            stdio: 'inherit',
            env: {
                ...process.env,
                PORT: backendPort,
                PYTHONUNBUFFERED: '1'
            }
        });
        
         pythonProcess.on('error', (err) => {
          console.error('Failed to start Python backend:', err);
        });
        
        pythonProcess.on('exit', (code, signal) => {
            console.log(`Python backend exited with code ${code} and signal ${signal}`);
        });

    } else {
        console.error('Could not find Python backend executable.');
        console.error('Checked resources path:', process.resourcesPath);
        dialog.showErrorBox(
          'Backend Not Found',
          'The packaged Python backend executable was not found. Please rerun the backend build step before packaging the Electron app.'
        );
        app.quit();
    }
  }
}

app.on('ready', () => {
  startPythonBackend();
  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on('will-quit', () => {
  if (pythonProcess) {
    console.log('Killing Python backend...');
    pythonProcess.kill();
  }
});
