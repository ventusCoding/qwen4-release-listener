@echo off
chcp 65001 >nul
title Qwen4 Release Listener
where py >nul 2>nul
if %errorlevel%==0 (py -3 -I "%~dp0qwen4_listener.py") else (python -I "%~dp0qwen4_listener.py")
pause
