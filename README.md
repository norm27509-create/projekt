# ROB RUN Settings Tuner

A small Windows tool that makes dark scenes in ROB RUN easier to see, plus a checklist of performance and visibility settings.

**How it works:** it only changes the Windows display gamma, the same thing your GPU control panel or monitor's brightness setting does. It does not read, modify, or inject into the game, and it doesn't draw an overlay. Your whole screen changes, not just the game.

## Features
- **Gamma, brightness and contrast** sliders with live preview.
- **Presets:** Default, Dark areas / night, Indoors / alleys, Bright day (less glare).
- **Custom profiles** saved to `%APPDATA%\RobRunTuner\profiles.json`.
- **Global hotkeys:** `F9` toggles the profile, `F10` resets to normal (both work while the game is focused).
- **Restores your original display gamma** when you close the tuner.
- **Settings checklist** covering mouse polling rate, drivers, overlays, display mode and more.

## Run
Requires Windows 10/11 and Python 3.10+ (tkinter is included with the python.org installer).

```
python run_tuner.py
```

### Build a standalone .exe (optional)
```
pip install pyinstaller
pyinstaller --onefile --windowed --name RobRunTuner run_tuner.py
```
The exe will be in `dist\RobRunTuner.exe`.

## Troubleshooting
- **Nothing changes in game:** use **Fullscreen** or **Borderless** mode. Some exclusive-fullscreen setups and HDR mode ignore Windows gamma. Turn HDR off while using the tuner.
- **"Windows rejected this ramp":** by default, Windows limits how strong a gamma change can be. Use milder values, or allow a wider range by setting `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ICM` → DWORD `GdiICMGammaRange` = `256`, then restart Windows. Only change this if you're comfortable editing the registry.
- **F9/F10 do nothing:** another app is already using those keys. The status bar will say so.
- **Screen stuck bright after a crash:** start the tuner and press Reset, or sign out and back in.

## Tests
```
python -m unittest discover -s tests
```
