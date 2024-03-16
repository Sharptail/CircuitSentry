# User Guide (WIP)
Download
- HidSharp.dll from [here]
- LibreHardwareMonitorLib.dll frome [here]
- CircuitSentry.exe from [here]

Put all of them in the same folder and run CircuitSentry.exe

# Developer Guide (WIP)
Run locally with the "play" button on the top right corner when "circuitsentry.py" is opened

Compile with
```
python -m PyInstaller circuitsentry.py --onefile --noconsole --icon=circuitsentry.ico --name=CircuitSentry.exe --add-data "circuitsentry.ico;."
```