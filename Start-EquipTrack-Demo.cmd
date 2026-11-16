@echo off
setlocal
set "LAN_ADDRESS=192.168.1.20"
echo Starting EquipTrack on the host laptop...
wsl.exe --distribution Ubuntu-24.04 --user root --cd "%~dp0." -- bash scripts/lan-demo.sh "%LAN_ADDRESS%"
if errorlevel 1 (
    echo EquipTrack could not start. Share the message above with Codex.
    pause
)
endlocal
