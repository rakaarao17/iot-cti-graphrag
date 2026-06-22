@echo off
REM Start Neo4j Enterprise 2026.05.0 for IoT CTI thesis project
REM Run this once per session before running any Python scripts.

set JAVA_HOME=C:\Users\Rakesh\.Neo4jDesktop2\Cache\runtime\zulu21.48.17-ca-jre21.0.10-win_x64
set NEO4J_ACCEPT_LICENSE_AGREEMENT=yes

echo [OK] JAVA_HOME set to bundled Zulu JRE 21
echo [OK] NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
echo.
echo Starting Neo4j Enterprise 2026.05.0...
echo Bolt endpoint will be: bolt://localhost:7687
echo Press Ctrl+C to stop Neo4j.
echo.

"C:\Users\Rakesh\.Neo4jDesktop2\Data\dbmss\dbms-f28e472a-2365-45cb-b3af-7e1c91078575\bin\neo4j.bat" console
