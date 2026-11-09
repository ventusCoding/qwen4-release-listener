@echo off
chcp 65001 >nul
title Qwen4 release preview
where py >nul 2>nul
if %errorlevel%==0 (py -3 -I "%~dp0qwen4_listener.py" --celebrate) else (python -I "%~dp0qwen4_listener.py" --celebrate)
