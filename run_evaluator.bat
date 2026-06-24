@echo off
echo ========================================================
echo   IoT Cyber Threat Intelligence GraphRAG
echo   Professor / Evaluator Setup Script
echo ========================================================

echo [1/3] Creating Python virtual environment...
if not exist "venv\" (
    python -m venv venv
)

echo [2/3] Activating environment and installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt

echo.
echo ========================================================
echo   PIPELINE EXECUTION
echo ========================================================
echo Please ensure you have Neo4j Desktop running with the instance "IoT Cyber KG"
echo and your password set to "password".
echo.
echo Also ensure Ollama is running locally (ollama serve) with the model pulled
echo (ollama pull gemma4:e2b). Copy .env.example to .env if you need to override defaults.
echo No cloud API key is required.
echo.

set /p build_choice="Do you need to build the Graph Database from scratch? (Type Y for Yes, N to skip to Chat): "

if /i "%build_choice%"=="Y" (
    echo.
    echo [4/6] Running Stage 3: Building Knowledge Graph... (This will take time)
    python scripts\run_pipeline.py --stage 3
    
    echo.
    echo [5/6] Running Stage 4: Generating Graph Embeddings...
    python scripts\run_pipeline.py --stage 4
    
    echo.
    echo [6/6] Running Stage 5: Initializing Vector Store...
    python scripts\run_pipeline.py --stage 5
)

echo.
echo ========================================================
echo   STARTING INTERACTIVE THREAT ANALYST...
echo ========================================================
python scripts\run_pipeline.py --interactive

pause
