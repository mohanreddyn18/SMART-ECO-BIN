@echo off
title SMART ECO BIN - EcoSort AI Launcher
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_project.ps1"
if errorlevel 1 pause
