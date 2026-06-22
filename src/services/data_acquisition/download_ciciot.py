"""
Stage 1: Download CICIoT2023 Dataset.


The CICIoT2023 dataset from Canadian Institute for Cybersecurity (UNB)
contains network traffic from 105 real IoT devices with 33 attack types
in 7 categories: DDoS, DoS, Recon, Web, BruteForce, Spoofing, Mirai.

Source: https://www.unb.ca/cic/datasets/iotdataset-2023.html
Also available on Kaggle.
"""

import os
import sys
import random
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import DATA_RAW_DIR, logger

CICIOT_OUTPUT_DIR = DATA_RAW_DIR / "ciciot2023"


def generate_manual_instructions():
    """Print manual download instructions for CICIoT2023."""
    print("""
======================================================================
              CICIoT2023 Dataset - Manual Download Guide             
======================================================================
                                                                    
  Option 1: Official UNB CIC Website                                
  -----------------------------------------------------------------  
  1. Visit: https://www.unb.ca/cic/datasets/iotdataset-2023.html    
  2. Fill out the download form                                     
  3. Download the CSV files                                         
  4. Extract to: data/raw/ciciot2023/                               
                                                                    
  Option 2: Kaggle                                                  
  -----------------------------------------------------------------  
  1. Visit: https://www.kaggle.com/datasets/                        
     Search for "CICIoT2023"                                       
  2. Download the dataset                                           
  3. Extract CSV files to: data/raw/ciciot2023/                     
                                                                    
  Expected File Structure:                                          
  data/raw/ciciot2023/                                              
    |-- part-00000.csv (or similar naming)                          
    |-- part-00001.csv                                              
    `-- ...                                                         
                                                                    
  The CSV files should contain columns like:                        
    flow_duration, Header_Length, Protocol Type, Duration,           
    Rate, Srate, Drate, fin_flag_number, syn_flag_number, ...       
    label (attack type label)                                       
                                                                    
======================================================================
""")


# -- CICIoT2023 Feature Columns ---------------------------------------------

CICIOT_FEATURES = [
    "flow_duration", "Header_Length", "Protocol Type", "Duration",
    "Rate", "Srate", "Drate", "fin_flag_number", "syn_flag_number",
    "rst_flag_number", "psh_flag_number", "ack_flag_number",
    "ece_flag_number", "cwr_flag_number", "ack_count", "syn_count",
    "fin_count", "urg_count", "rst_count", "HTTP", "HTTPS", "DNS",
    "Telnet", "SMTP", "SSH", "IRC", "TCP", "UDP", "DHCP", "ARP",
    "ICMP", "IPv", "LLC", "Tot sum", "Min", "Max", "AVG", "Std",
    "Tot size", "IAT", "Number", "Magnitue", "Radius", "Covariance",
    "Variance", "Weight",
]

CICIOT_ATTACK_TYPES = [
    # DDoS
    "DDoS-ACK_Fragmentation", "DDoS-UDP_Flood", "DDoS-SlowLoris",
    "DDoS-ICMP_Flood", "DDoS-RSTFINFlood", "DDoS-PSHACK_Flood",
    "DDoS-HTTP_Flood", "DDoS-SYN_Flood", "DDoS-SynonymousIP_Flood",
    "DDoS-TCP_Flood", "DDoS-UDP_Fragmentation", "DDoS-ICMP_Fragmentation",
    # DoS
    "DoS-UDP_Flood", "DoS-TCP_Flood", "DoS-SYN_Flood", "DoS-HTTP_Flood",
    # Recon
    "Recon-PingSweep", "Recon-OSScan", "Recon-PortScan", "Recon-HostDiscovery",
    # Web
    "Web-XSS", "Web-SQLi", "Web-BrowserHijacking",
    # BruteForce
    "BruteForce-SSH", "BruteForce-HTTP",
    # Spoofing
    "Spoofing-ARP", "Spoofing-DNS",
    # Mirai
    "Mirai-greeth_flood", "Mirai-greip_flood", "Mirai-udpplain",
    # Benign
    "BenignTraffic",
]



def verify_ciciot_data(data_dir: Path = None) -> bool:
    """Verify that CICIoT2023 data files exist and are valid."""
    data_dir = data_dir or CICIOT_OUTPUT_DIR

    if not data_dir.exists():
        logger.warning(f"CICIoT2023 data directory not found: {data_dir}")
        return False

    csv_files = list(data_dir.glob("*.csv"))
    if not csv_files:
        logger.warning(f"No CSV files found in: {data_dir}")
        return False

    total_rows = 0
    for f in csv_files:
        try:
            # Just read the first few rows to verify format
            df = pd.read_csv(f, nrows=5)
            total_rows += len(pd.read_csv(f, usecols=[0]))  # Count rows efficiently
            logger.info(f"  [OK] {f.name}: {len(df.columns)} columns")
        except Exception as e:
            logger.error(f"  [FAIL] {f.name}: {e}")
            return False

    logger.info(f"CICIoT2023 data verified: {len(csv_files)} files, ~{total_rows:,} total rows")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download / Setup CICIoT2023 Dataset")

    parser.add_argument("--manual", action="store_true", help="Print manual download instructions")
    parser.add_argument("--verify", action="store_true", help="Verify existing data files")
    args = parser.parse_args()

    if args.manual:
        generate_manual_instructions()

    elif args.verify:
        verify_ciciot_data()
    else:
        generate_manual_instructions()

