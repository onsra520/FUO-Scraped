@echo off
echo ============================================================
echo   FUO Scraper Web Application
echo ============================================================
echo Starting server at http://localhost:8211
echo Press Ctrl+C to stop the server
echo ============================================================

REM Activate conda environment and run
call conda activate TresorDeSavoir
python run.py
