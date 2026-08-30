@echo off
title InterviewMind AI Backend
echo Starting InterviewMind AI Backend Server...
cd /d "%~dp0backend"
if exist "..\.venv\Scripts\uvicorn.exe" (
    ..\.venv\Scripts\uvicorn.exe main:app --reload --port 8000
) else (
    uvicorn main:app --reload --port 8000
)
pause

