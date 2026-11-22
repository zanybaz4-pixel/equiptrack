@echo off
setlocal
echo Starting EquipTrack on this laptop...
wsl.exe --distribution Ubuntu-24.04 --user root --cd "%~dp0." -- bash scripts/local-demo.sh
if errorlevel 1 (
    echo EquipTrack could not start. Share the message above with Codex.
    pause
)
endlocal
