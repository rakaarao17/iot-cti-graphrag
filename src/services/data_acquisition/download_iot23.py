"""
Stage 1: Download IoT-23 Dataset (Light version).



The IoT-23 dataset by Stratosphere Lab (CTU Prague) contains 23 scenarios
of IoT malware and benign traffic captured as Zeek conn.log.labeled files.

Light version (~8.7 GB) contains logs without pcap files.
Source: https://zenodo.org/records/4743746
"""

import os
import sys
import hashlib
import requests
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import DATA_RAW_DIR, logger

# -- IoT-23 Scenario URLs ---------------------------------------------------
# These are the individual scenario conn.log.labeled files (Light version)
# Full list from: https://mcfp.felk.cvut.cz/publicDatasets/IoT-23-Dataset/

IOT23_BASE_URL = "https://mcfp.felk.cvut.cz/publicDatasets/IoT-23-Dataset/IndividualScenarios/"

# Representative scenarios covering different malware families
IOT23_SCENARIOS = {
    "CTU-IoT-Malware-Capture-1-1": "Mirai botnet -- Hide and Seek",
    "CTU-IoT-Malware-Capture-3-1": "Muhstik botnet",
    "CTU-IoT-Malware-Capture-7-1": "Linux.Hajime",
    "CTU-IoT-Malware-Capture-8-1": "Hakai botnet",
    "CTU-IoT-Malware-Capture-9-1": "Linux.Mirai / Okiru",
    "CTU-IoT-Malware-Capture-20-1": "Torii botnet",
    "CTU-IoT-Malware-Capture-21-1": "Torii botnet (variant)",
    "CTU-IoT-Malware-Capture-33-1": "Kenjiro / Mirai variant",
    "CTU-IoT-Malware-Capture-34-1": "Mirai variant",
    "CTU-IoT-Malware-Capture-35-1": "Mirai variant",
    "CTU-IoT-Malware-Capture-42-1": "Trojan / Generic",
    "CTU-IoT-Malware-Capture-43-1": "Mirai / Okiru variant",
    "CTU-IoT-Malware-Capture-44-1": "Mirai attack",
    "CTU-IoT-Malware-Capture-48-1": "Mirai variant",
    "CTU-IoT-Malware-Capture-49-1": "Mirai variant",
    "CTU-IoT-Malware-Capture-52-1": "Mirai variant",
    "CTU-IoT-Malware-Capture-54-1": "Mirai variant",
    "CTU-IoT-Malware-Capture-60-1": "Gagfyt / Bashlite",
    # Benign scenarios
    "CTU-Honeypot-Capture-4-1": "Benign -- Philips HUE",
    "CTU-Honeypot-Capture-5-1": "Benign -- Amazon Echo",
    "CTU-Honeypot-Capture-7-1": "Benign -- Somfy Smart Lock",
}

IOT23_OUTPUT_DIR = DATA_RAW_DIR / "iot23"


def download_file(url: str, dest: Path, chunk_size: int = 8192) -> bool:
    """Download a file with progress bar and resume support."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Check if file already exists
    if dest.exists() and dest.stat().st_size > 0:
        logger.info(f"File already exists: {dest.name} ({dest.stat().st_size:,} bytes)")
        return True

    try:
        # Get file size
        head = requests.head(url, allow_redirects=True, timeout=30)
        total_size = int(head.headers.get("content-length", 0))

        # Check for partial download (resume support)
        resume_byte = 0
        headers = {}
        temp_path = dest.with_suffix(dest.suffix + ".partial")
        if temp_path.exists():
            resume_byte = temp_path.stat().st_size
            headers["Range"] = f"bytes={resume_byte}-"
            logger.info(f"Resuming download from byte {resume_byte:,}")

        response = requests.get(url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()

        mode = "ab" if resume_byte > 0 else "wb"
        with open(temp_path, mode) as f:
            with tqdm(
                total=total_size,
                initial=resume_byte,
                unit="B",
                unit_scale=True,
                desc=dest.name[:40],
            ) as pbar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        # Rename to final name
        temp_path.rename(dest)
        logger.info(f"Downloaded: {dest.name}")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed for {url}: {e}")
        return False


def download_iot23_scenario(scenario_name: str) -> bool:
    """Download a single IoT-23 scenario's conn.log.labeled file."""
    # The file path within each scenario
    url = f"{IOT23_BASE_URL}{scenario_name}/bro/conn.log.labeled"
    dest = IOT23_OUTPUT_DIR / scenario_name / "conn.log.labeled"
    return download_file(url, dest)


def download_all_scenarios(max_scenarios: int = None):
    """Download all (or N) IoT-23 scenarios."""
    scenarios = list(IOT23_SCENARIOS.items())
    if max_scenarios:
        scenarios = scenarios[:max_scenarios]

    logger.info(f"Downloading {len(scenarios)} IoT-23 scenarios...")
    IOT23_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = {}
    for name, description in scenarios:
        logger.info(f"\n{'-' * 60}")
        logger.info(f"Scenario: {name}")
        logger.info(f"Type:     {description}")
        logger.info(f"{'-' * 60}")
        success = download_iot23_scenario(name)
        results[name] = success

    # Summary
    success_count = sum(1 for v in results.values() if v)
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Download Complete: {success_count}/{len(results)} scenarios")
    logger.info(f"{'=' * 60}")

    return results


def generate_manual_instructions():
    """Print manual download instructions if automated download fails."""
    print("""
======================================================================
                IoT-23 Dataset - Manual Download Guide               
======================================================================
                                                                    
  Option 1: Zenodo (Full Light Dataset ~8.7 GB)                     
  -----------------------------------------------------------------  
  1. Visit: https://zenodo.org/records/4743746                      
  2. Download the "IoT-23 Light" zip file                           
  3. Extract to: data/raw/iot23/                                    
                                                                    
  Option 2: Kaggle (Preprocessed CSV)                               
  -----------------------------------------------------------------  
  1. Visit: https://www.kaggle.com/datasets/                        
     Search for "IoT-23 dataset"                                    
  2. Download the CSV version                                       
  3. Place in: data/raw/iot23/                                      
                                                                    
  Option 3: Individual Scenarios (Smaller downloads)                
  -----------------------------------------------------------------  
  Base URL: https://mcfp.felk.cvut.cz/publicDatasets/               
            IoT-23-Dataset/IndividualScenarios/                     
  Download: <scenario>/bro/conn.log.labeled                         
                                                                    
======================================================================
""")
    print("Available Scenarios:")
    for name, desc in IOT23_SCENARIOS.items():
        print(f"  - {name:45s} -- {desc}")



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download IoT-23 Dataset")
    parser.add_argument("--scenarios", type=int, default=3, help="Number of scenarios to download (default: 3)")

    parser.add_argument("--manual", action="store_true", help="Print manual download instructions")
    args = parser.parse_args()

    if args.manual:
        generate_manual_instructions()

    else:
        download_all_scenarios(max_scenarios=args.scenarios)
