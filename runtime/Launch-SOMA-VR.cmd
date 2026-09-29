@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Launch-SOMA-VR.ps1" %*
if errorlevel 1 pause
