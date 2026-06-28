# CircuitSentry v1.0.0

A lightweight Windows overlay app that shows live CPU and GPU temperature and usage.

![CircuitSentry](assets/circuitsentry.png)

The window can be dragged anywhere, hidden to the tray, and configured with a right-click menu.

---

## 🎯 Quick start for users

CircuitSentry is designed to be simple: download the executable, get the support files, and run it.

### Run in 3 easy steps

1. Download `CircuitSentry.exe`.
2. Download [LibreHardwareMonitor.zip](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases)
   - Extract the .zip file
   - You only need `HidSharp.dll` and `LibreHardwareMonitorLib.dll` from the extracted folder
   - Put all 3 files into same folder where it contains the app and the two support DLLs
      ```text
      CircuitSentryUserFolder/
      ├── CircuitSentry.exe
      ├── LibreHardwareMonitorLib.dll
      └── HidSharp.dll
      ```
3. Double-click `CircuitSentry.exe`.

That’s it. The app will open and start showing your CPU and GPU stats.

---

## 🛠️ For developers

### Run from source

1. Install Python 3.
2. Install dependencies:

   ```bash
   pip install pythonnet pystray pillow tendo pytest pytest-cov
   ```

3. Download the DLL support files and place them in the project folder.
4. Run:

   ```bash
   python circuitsentry.py
   ```

### Run tests

This project does not include the `.venv` folder in source control. Create and activate a local virtual environment before running tests.

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install pythonnet pystray pillow tendo pytest pytest-cov
python -m pytest --cov=. --cov-report=term-missing
```

### GitHub Actions CI

A GitHub Actions workflow is included at `.github/workflows/ci.yml`. It runs on Windows and executes the same test command on push and pull request.

### Build a Windows executable

```bash
python -m PyInstaller circuitsentry.py --onefile --noconsole --icon=assets/circuitsentry.ico --name=CircuitSentry.exe --add-data "assets/circuitsentry.ico;assets"
```

After building, copy `LibreHardwareMonitorLib.dll` and `HidSharp.dll` into the same folder as `CircuitSentry.exe` before running.

---

## ⚠️ Notes

- Only one instance of CircuitSentry can run at a time.
- The app depends on LibreHardwareMonitor sensor support.
- `.dll` files are excluded from this repository via `.gitignore`.
- There is now an option to install an elevated startup task so the app can start with the privileges needed to read CPU temperature on startup.
