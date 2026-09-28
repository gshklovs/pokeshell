@echo off
rem pokeshell from cmd, bash, or Claude Code's `!` prefix (put this folder on PATH):  pokeshell holo -r cosmos
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0pokeshell.ps1" %*
