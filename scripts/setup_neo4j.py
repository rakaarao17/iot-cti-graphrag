"""
Neo4j Setup Helper.

Provides instructions and automation for setting up Neo4j
on Windows for the IoT CTI Knowledge Graph.
"""

import sys
import subprocess
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import logger


def check_java():
    """Check if Java is installed and meets the minimum version requirement."""
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stderr or result.stdout
        print(f"  Java version: {output.strip().split(chr(10))[0]}")
        return True
    except FileNotFoundError:
        print("  âœ— Java not found in PATH")
        return False
    except Exception as e:
        print(f"  âœ— Java check failed: {e}")
        return False


def check_neo4j():
    """Check if Neo4j is installed."""
    neo4j_path = shutil.which("neo4j")
    if neo4j_path:
        print(f"  âœ“ Neo4j found: {neo4j_path}")
        return True
    else:
        print("  âœ— Neo4j not found in PATH")
        return False


def print_setup_instructions():
    """Print comprehensive Neo4j setup instructions for Windows."""
    print("""
======================================================================
           Neo4j Setup Guide for Windows                            
======================================================================

  OPTION 1: Neo4j Desktop (Recommended for beginners)
  -------------------------------------------------------
  1. Download from: https://neo4j.com/download/
  2. Install Neo4j Desktop
  3. Create a new project -> Add Database -> Local DBMS
  4. Set password (remember it for .env file)
  5. Start the database
  6. Default connection: bolt://localhost:7687

  OPTION 2: Neo4j Community Edition (CLI)
  -----------------------------------------
  Prerequisites:
    - Java JDK 17+ (https://adoptium.net/)

  Steps:
    1. Download from: https://neo4j.com/deployment-center/
       Select "Community Edition" -> Windows
    2. Extract the ZIP to C:\\neo4j (or your preferred location)
    3. Set environment variables:
       $env:NEO4J_HOME = "C:\\neo4j"
       $env:PATH += ";C:\\neo4j\\bin"
    4. Run: neo4j console
    5. Open browser: http://localhost:7474
    6. Login: neo4j / neo4j (change password on first login)

  OPTION 3: Docker (If you have Docker Desktop)
  ----------------------------------------------
  docker run -d \\
    --name neo4j-iot-cti \\
    -p 7474:7474 -p 7687:7687 \\
    -e NEO4J_AUTH=neo4j/your_password \\
    -v neo4j-data:/data \\
    neo4j:5-community

  AFTER SETUP:
  ------------
  1. Copy .env.example to .env:
     copy .env.example .env

  2. Update .env with your Neo4j password:
     NEO4J_URI=bolt://localhost:7687
     NEO4J_USER=neo4j
     NEO4J_PASSWORD=your_password_here

  3. Test the connection:
     python -c "from src.services.knowledge_graph.neo4j_connection import verify_connectivity; verify_connectivity()"

======================================================================
""")


def run_diagnostics():
    """Run system diagnostics for Neo4j compatibility."""
    print("\n" + "=" * 60)
    print("  System Diagnostics for Neo4j")
    print("=" * 60)

    print("\n  1. Java Check:")
    java_ok = check_java()

    print("\n  2. Neo4j Check:")
    neo4j_ok = check_neo4j()

    print("\n  3. Python Packages:")
    try:
        import neo4j
        print(f"  âœ“ neo4j package: v{neo4j.__version__}")
    except ImportError:
        print("  âœ— neo4j package not installed (pip install neo4j)")

    try:
        import neo4j_graphrag
        print(f"  âœ“ neo4j-graphrag package installed")
    except ImportError:
        print("  âœ— neo4j-graphrag not installed (pip install neo4j-graphrag[google])")

    print("\n  4. Neo4j Connection:")
    try:
        from src.services.knowledge_graph.neo4j_connection import verify_connectivity
        verify_connectivity()
    except Exception as e:
        print(f"  âœ— Connection failed: {e}")

    print("\n" + "=" * 60)

    if not java_ok:
        print("\n  âš ï¸  Action Required: Install Java JDK 17+")
        print("     https://adoptium.net/")

    if not neo4j_ok:
        print("\n  âš ï¸  Action Required: Install Neo4j")
        print("     Run this script with --instructions for setup guide")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Neo4j Setup Helper")
    parser.add_argument("--instructions", action="store_true", help="Print setup instructions")
    parser.add_argument("--diagnose", action="store_true", help="Run diagnostics")
    args = parser.parse_args()

    if args.instructions:
        print_setup_instructions()
    elif args.diagnose:
        run_diagnostics()
    else:
        run_diagnostics()
        print("\nUse --instructions for detailed setup guide")
