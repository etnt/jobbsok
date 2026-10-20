@echo off
chcp 65001 >nul
title JobbSök
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Först körning: installerar det som behövs. Det tar någon minut...
    py -3 -m venv .venv || python -m venv .venv
    if errorlevel 1 (
        echo Kunde inte skapa miljön. Installera Python 3.11 eller nyare från python.org
        pause
        exit /b 1
    )
    ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Installationen misslyckades. Kontakta den som installerade appen.
        pause
        exit /b 1
    )
)

echo Startar JobbSök. Webbläsaren öppnas automatiskt.
echo Stäng detta fönster för att avsluta appen.
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless=false --browser.gatherUsageStats=false
