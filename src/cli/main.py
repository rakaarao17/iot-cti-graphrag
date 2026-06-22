"""
Main CLI Entrypoint.
"""
import sys
import time
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config.settings import logger
from src.services.threat_explanation.explainer import ThreatExplainer

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    C_INFO = Fore.CYAN
    C_WARN = Fore.YELLOW
    C_ERR = Fore.RED
    C_SUCCESS = Fore.GREEN
    C_BOLD = Style.BRIGHT
    C_RESET = Style.RESET_ALL
except ImportError:
    C_INFO = C_WARN = C_ERR = C_SUCCESS = C_BOLD = C_RESET = ""

def print_header():
    print(f"\n{C_INFO}{C_BOLD}" + "=" * 70)
    print(f"    IoT Cyber Threat Intelligence -- Interactive Analyst")
    print("=" * 70 + f"{C_RESET}")
    print(f"""
  Commands:
    device <ip>          -- Analyze a specific device
    attack <type>        -- Explain an attack type
    report               -- Generate incident report
    mitre                -- MITRE ATT&CK mapping
    compare              -- Dataset comparison
    investigate <query>  -- Free-form investigation
    help                 -- Show this help
    quit                 -- Exit
    """)

def run_query(explainer, user_input: str):
    parts = user_input.split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""
    
    start_time = time.time()
    
    try:
        if command == "device":
            if not arg:
                return "Usage: device <ip_address>"
            result = explainer.explain_device(arg)
            return f"\n{C_SUCCESS}{result['analysis']}{C_RESET}"
        elif command == "attack":
            if not arg:
                return "Usage: attack <attack_type>"
            result = explainer.explain_attack(arg)
            return f"\n{C_SUCCESS}{result['analysis']}{C_RESET}"
        elif command == "report":
            result = explainer.generate_incident_report(arg or None)
            return f"\n{C_SUCCESS}{result['report']}{C_RESET}"
        elif command == "mitre":
            result = explainer.map_to_mitre(arg or None)
            return f"\n{C_SUCCESS}{result['mapping']}{C_RESET}"
        elif command == "compare":
            result = explainer.compare_datasets()
            return f"\n{C_SUCCESS}{result['analysis']}{C_RESET}"
        elif command in ("investigate", "ask", "query"):
            if not arg:
                return "Usage: investigate <question>"
            result = explainer.investigate(arg)
            return f"\n{C_SUCCESS}{result['analysis']}{C_RESET}"
        elif command == "help":
            return (f"  {C_BOLD}device <ip>{C_RESET}     -- Analyze a specific IoT device\n"
                    f"  {C_BOLD}attack <type>{C_RESET}   -- Explain an attack type\n"
                    f"  {C_BOLD}report{C_RESET}          -- Generate incident report\n"
                    f"  {C_BOLD}mitre{C_RESET}           -- MITRE ATT&CK mapping\n"
                    f"  {C_BOLD}compare{C_RESET}         -- Compare IoT-23 vs CICIoT2023\n"
                    f"  {C_BOLD}investigate <q>{C_RESET} -- Free-form investigation")
        else:
            # Treat as free-form query
            result = explainer.investigate(user_input)
            return f"\n{C_SUCCESS}{result['analysis']}{C_RESET}"
    finally:
        if command != "help":
            elapsed = time.time() - start_time
            print(f"\n{C_WARN}  Response Generated in: {elapsed:.2f} seconds{C_RESET}")

def interactive_session(auto_demo: bool = False):
    """Run an interactive threat analysis session."""
    explainer = ThreatExplainer()
    print_header()

    if auto_demo:
        demo_queries = [
            "investigate Which devices are exhibiting Mirai botnet behavior, and what protocols are they using?",
            "mitre",
        ]
        for q in demo_queries:
            print(f"\n{C_BOLD} Analyst > {C_INFO}{q}{C_RESET}")
            print(run_query(explainer, q))
            time.sleep(2)

    while True:
        try:
            user_input = input(f"\n{C_BOLD} Analyst > {C_RESET}").strip()
            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print(f"{C_INFO}Goodbye! Stay secure. {C_RESET}")
                break
                
            response = run_query(explainer, user_input)
            print(response)

        except KeyboardInterrupt:
            print(f"\n{C_INFO}Goodbye! Stay secure. {C_RESET}")
            break
        except Exception as e:
            print(f"\n{C_ERR}  Error: {e}{C_RESET}")
            logger.error(f"Interactive session error: {e}", exc_info=True)


if __name__ == "__main__":
    interactive_session()
