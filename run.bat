@echo off

REM Проверка наличия папки .venv
if exist .venv (
    call .venv\Scripts\activate
) else (
    call venv\Scripts\activate
)

python main.py

