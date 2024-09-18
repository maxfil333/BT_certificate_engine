@echo off
cd /d "%~dp0"

if exist .venv (
    call .venv\Scripts\activate
) else (
    call venv\Scripts\activate
)

python main.py >> script_log.txt 2>&1
