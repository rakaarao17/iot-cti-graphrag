import pandas as pd
from pathlib import Path

RESULTS_DIR = Path("results")
DATA_FILE = Path("data/processed/unified_features.csv")

def export_metrics():
    print("Loading network dataset for deep academic analysis...")
    df = pd.read_csv(DATA_FILE)
    
    print("Generating Academic Threat Metrics...")
    
    # 1. High-Level Attack Protocol Matrix
    print("Generating High-Level Attack Protocol Matrix...")
    attack_proto = df.groupby(['label', 'protocol']).agg({
        'orig_bytes': 'sum',
        'resp_bytes': 'sum',
        'duration': 'mean'
    }).reset_index().rename(columns={
        'label': 'Attack_Type',
        'protocol': 'Transport_Protocol',
        'orig_bytes': 'Total_Bytes_Sent',
        'resp_bytes': 'Total_Bytes_Received',
        'duration': 'Average_Duration_Seconds'
    })
    # Add flow count
    flow_counts = df.groupby(['label', 'protocol']).size().reset_index(name='Flow_Count')
    flow_counts = flow_counts.rename(columns={'label': 'Attack_Type', 'protocol': 'Transport_Protocol'})
    attack_proto = pd.merge(attack_proto, flow_counts, on=['Attack_Type', 'Transport_Protocol'])
    attack_proto.sort_values('Flow_Count', ascending=False, inplace=True)
    attack_proto.to_csv(RESULTS_DIR / "academic_attack_protocol_matrix.csv", index=False)
    
    # 2. Botnet vs DDoS/DoS vs Reconnaissance Distribution
    print("Generating Botnet vs Generic Attack Distribution...")
    
    def categorize_attack(label):
        label = str(label)
        if label == 'Benign':
            return 'Benign Baseline'
        elif 'Mirai' in label or 'Torii' in label or 'Hajime' in label:
            return 'Botnet Operation (C&C/Propagation)'
        elif 'DDoS' in label or 'DoS' in label:
            return 'Volumetric Availability Attack'
        elif 'Recon' in label or 'Scan' in label:
            return 'Reconnaissance & Discovery'
        else:
            return 'Exploitation & Application Layer'
            
    df['Academic_Category'] = df['label'].apply(categorize_attack)
    category_dist = df.groupby('Academic_Category').agg({
        'label': 'count',
        'orig_bytes': 'sum'
    }).reset_index().rename(columns={
        'label': 'Total_Flows',
        'orig_bytes': 'Total_Bandwidth_Bytes'
    }).sort_values('Total_Flows', ascending=False)
    category_dist.to_csv(RESULTS_DIR / "academic_attack_category_distribution.csv", index=False)
    
    # 3. Time Series Attack Distribution (Approximation by dataset ordering)
    print("Generating Temporal Distribution...")
    df['Attack_Class'] = df['label'].apply(lambda x: 'Benign' if x == 'Benign' else 'Malicious')
    chunk_size = 50000
    temporal = df.groupby(df.index // chunk_size)['Attack_Class'].value_counts().unstack().fillna(0)
    temporal.to_csv(RESULTS_DIR / "academic_temporal_attack_distribution.csv")
    
    print("Academic metrics exported successfully.")

if __name__ == "__main__":
    export_metrics()
