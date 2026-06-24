@echo off
echo ========================================================
echo   IoT Cyber Threat Intelligence GraphRAG - DEMO MODE
echo ========================================================
echo.
echo This script will run the entire GraphRAG pipeline using
echo synthetic demo data. Perfect for portfolio demonstrations!
echo.

if not exist "venv\" (
    echo [1/3] Creating Python virtual environment...
    python -m venv venv
)

echo [2/3] Activating environment...
call venv\Scripts\activate
pip install -r requirements.txt -q

echo.
echo [3/3] Running MVP Demo (offline mode - no Neo4j required)...
python scripts\run_mvp.py --skip-neo4j

pause
