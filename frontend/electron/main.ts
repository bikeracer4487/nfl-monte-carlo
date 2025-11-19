import { app, BrowserWindow } from 'electron';
import path from 'path';
import { spawn, ChildProcess } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let mainWindow: BrowserWindow | null;
let pythonProcess: ChildProcess | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    title: "NFL Monte Carlo Simulation",
    backgroundColor: "#121212", // Dark theme background
  });

  if (process.env.NODE_ENV === 'development') {
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
  if (process.env.NODE_ENV === 'development') {
    const backendPath = path.join(__dirname, '../../backend/api/server.py');
    console.log('Starting Python backend...', backendPath);
    
    // Spawn python process
    // Assuming python3 is in path and venv is active or requirements are installed
    pythonProcess = spawn('python3', [backendPath], {
      cwd: path.join(__dirname, '../../'),
      stdio: 'inherit' // Pipe output to console
    });

    pythonProcess.on('error', (err) => {
      console.error('Failed to start Python backend:', err);
    });
    
    pythonProcess.on('exit', (code, signal) => {
        console.log(`Python backend exited with code ${code} and signal ${signal}`);
    });
  } else {
    // Production logic (executable)
    // TODO: Implement production path handling
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
