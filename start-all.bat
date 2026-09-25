@echo off
title InterviewMind AI Launcher
echo Launching InterviewMind AI Full Project...
start "Backend" "%~dp0start-backend.bat"
start "Frontend" "%~dp0start-frontend.bat"
echo.
echo Both Backend (port 8000) and Frontend (port 3000) are launching!
echo App URL: http://localhost:3000
echo.
