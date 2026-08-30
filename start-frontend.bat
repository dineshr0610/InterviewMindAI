@echo off
title InterviewMind AI Frontend
echo Starting InterviewMind AI Frontend Dev Server...
cd /d "%~dp0frontend"
call npm.cmd run dev
pause

