@echo off
title InterviewMind AI Backend
echo Starting InterviewMind AI Backend Server...
cd /d "%~dp0backend"
uvicorn main:app --reload --port 8000
pause
