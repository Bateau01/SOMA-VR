@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Launch-SOMA-VR.ps1" -StopOnly
set "somaStopResult=%errorlevel%"
if not "%somaStopResult%"=="0" pause
exit /b %somaStopResult%
