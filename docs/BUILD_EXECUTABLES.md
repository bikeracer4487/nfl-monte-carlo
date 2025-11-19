# Building Production Executables

This guide explains how to produce **single-file, dependency-free executables** for the PySide6 desktop application using PyInstaller. The resulting binaries embed the Python interpreter, standard library, third-party packages (NumPy, Numba, PySide6, etc.), fonts, and application code so end users only need to download a single artifact per platform.

- **Windows output**: `NFLMonteCarlo.exe`
- **macOS output**: `NFLMonteCarlo.app` (bundle) + `Contents/MacOS/NFLMonteCarlo` single-file binary suitable for CLI distribution

> **Important**: PyInstaller does not support true cross-compilation. Build the Windows executable on Windows and the macOS bundle on a Mac (Ventura or newer recommended).

---

## 1. Shared Build Preparation

All commands below assume you start in the repository root (`/Users/douglas.mason/Documents/GitHub/nfl-monte-carlo` on macOS or the equivalent path on Windows) and that you have Python 3.11+ available.

1. **Create a clean build environment**
   ```bash
   cd /Users/douglas.mason/Documents/GitHub/nfl-monte-carlo
   python3.11 -m venv .venv-build
   source .venv-build/bin/activate      # Windows: .\.venv-build\Scripts\activate
   python -m pip install --upgrade pip setuptools wheel
   ```

2. **Install runtime dependencies plus PyInstaller tooling**
   ```bash
   pip install -r backend/requirements.txt
   pip install pyinstaller==6.11.0 pyinstaller-hooks-contrib==2025.5
   ```

3. **(Optional but recommended) Run the GUI smoke test before packaging**
   ```bash
   cd backend
   python main.py
   cd ..
   ```

4. **(Optional) Override cache location for production builds**  
   By default the app writes caches to a `data/` folder next to the executable. To prefer per-user storage, create a `.env` before running PyInstaller:
   ```bash
   cat <<'EOF' > backend/.env
   CACHE_DIRECTORY=%LOCALAPPDATA%/NFLMonteCarlo/data   # Windows
   # CACHE_DIRECTORY=$HOME/Library/Application Support/NFLMonteCarlo/data  # macOS
   EOF
   ```
   Adjust the path for the target OS, then delete or edit the file once the build is complete.

---

## 2. Windows 10/11 Single-File Executable

1. Launch **PowerShell** (x64) and activate the build virtual environment:
   ```powershell
   Set-Location C:\path\to\nfl-monte-carlo
   .\.venv-build\Scripts\Activate.ps1
   ```

2. Change into the backend directory so PyInstaller can find `main.py` and the `src/` package:
   ```powershell
   Set-Location .\backend
   ```

3. Run PyInstaller with single-file and GUI-friendly flags. Use `;` when mapping data on Windows:
   ```powershell
   pyinstaller `
     --noconfirm `
     --clean `
     --onefile `
     --windowed `
     --name NFLMonteCarlo `
     --icon "..\final_icon.png" `
     --paths .\src `
     --collect-all numba `
     --collect-all numpy `
     --add-data "src\gui\fonts;src/gui/fonts" `
     --add-data "..\final_icon.png;." `
     main.py
   ```
   **What the flags do**
   - `--onefile`: pack everything into `NFLMonteCarlo.exe`
   - `--windowed`: hide the console when the GUI launches
   - `--paths .\src`: ensures relative imports resolve without hacking `sys.path`
   - `--collect-all numba/numpy`: pulls in dynamic extensions those packages load at runtime
   - `--add-data`: bundles the Inter font files so Qt can load them from the PyInstaller temp directory

4. When the command finishes you will have:
   ```
   backend/dist/NFLMonteCarlo.exe      # deliver this file
   backend/build/                      # intermediate files (safe to delete)
   backend/NFLMonteCarlo.spec          # auto-generated spec (commit if you want reproducible builds)
   ```

5. **Smoke test**
   ```powershell
   .\dist\NFLMonteCarlo.exe
   ```
   The app should create a fresh `data` folder next to the executable (or the directory you set in `.env`) on first launch.

---

## 3. macOS (Apple Silicon + Intel) Universal Bundle

> Apple requires that GUI apps be delivered as `.app` bundles. PyInstaller still builds a single self-extracting binary inside the bundle, so distribution remains "single download". The `--onefile` flag speeds up launches by packaging dependencies into that binary.

1. Open **Terminal** and activate the build environment:
   ```bash
   cd /Users/douglas.mason/Documents/GitHub/nfl-monte-carlo
   source .venv-build/bin/activate
   cd backend
   ```

2. Build a universal (arm64 + x86_64) app bundle:
   ```bash
   pyinstaller \
     --noconfirm \
     --clean \
     --onefile \
     --windowed \
     --name NFLMonteCarlo \
     --icon "../icon.icns" \
     --osx-bundle-identifier "com.nflmontecarlo.simulator" \
     --target-arch universal2 \
     --collect-all numba \
     --collect-all numpy \
     --add-data "src/gui/fonts:src/gui/fonts" \
     --add-data "../final_icon.png:." \
     main.py
   ```
   - `--target-arch universal2` requires Xcode command line tools. If you only need an Apple Silicon build, omit the flag; PyInstaller will target the host CPU.
   - `--osx-bundle-identifier` populates the bundle metadata so signing/notarization works later.

3. Results:
   ```
   backend/dist/NFLMonteCarlo.app                 # drag-and-drop app bundle
   backend/dist/NFLMonteCarlo                     # CLI-friendly single binary (inside the .app)
   backend/build/
   backend/NFLMonteCarlo.spec
   ```

4. **Smoke test**
   ```bash
   open dist/NFLMonteCarlo.app
   ```
   or run the single-file binary directly:
   ```bash
   dist/NFLMonteCarlo
   ```

5. **(Optional) Strip quarantine & sign**
   ```bash
   xattr -cr dist/NFLMonteCarlo.app
   codesign --deep --force --sign - dist/NFLMonteCarlo.app
   ```
   Replace `-` with your Developer ID to satisfy Gatekeeper before distributing publicly.

---

## 4. Post-Build Checklist

- ✅ Launch the executable/bundle once to ensure fonts render and the cache directory is created.
- ✅ Verify the simulated season controls work and that API calls succeed without needing Python installed.
- ✅ Zip the artifact before sharing (`Compress "NFLMonteCarlo.app"` on macOS, `Compress-Archive` or 7-Zip on Windows) so browsers keep the file intact.
- ✅ If you created a temporary `.env` for cache redirection, either bake the desired values into version control or delete the file to avoid leaking local paths.

---

## 5. Troubleshooting

- **`ModuleNotFoundError` for PySide6 plugins**  
  Make sure you ran `pip install pyinstaller-hooks-contrib` before building; PyInstaller relies on those hooks to bundle Qt plugins.

- **`Failed to execute script main`**  
  Run with `pyinstaller --log-level DEBUG ...` and inspect `dist/NFLMonteCarlo.exe --debug all` to see which dependency is missing. Most issues are resolved by adding `--collect-all <package>` or `--hidden-import <module>`.

- **Fonts missing in the packaged app**  
  Double-check the `--add-data` mapping. On macOS the separator must be a colon (`:`); on Windows it must be a semicolon (`;`).

- **macOS says the app is damaged or untrusted**  
  Remove the quarantine bit with `xattr -cr dist/NFLMonteCarlo.app`, or codesign/notarize the bundle when distributing to non-developers.

- **Large file size**  
  PyInstaller’s single-file mode always extracts to a temp directory at launch. Use `pyinstaller --onedir ...` during development for faster iterations, but keep `--onefile` + `--windowed` for production drops.

---

Following the steps above ensures Windows and macOS users receive a single, double-clickable artifact that contains Python, native extensions, Qt plugins, fonts, and the simulation engine without installing any external runtimes.

