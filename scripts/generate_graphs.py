import sys
from pathlib import Path
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import seaborn as sns
from neo4j import GraphDatabase
import os

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

# Setup Academic Style (Publication Quality)
plt.style.use('default') # Light background
sns.set_theme(style="whitegrid", palette="colorblind", font_scale=1.2)
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

def generate_graphs():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    db_name = os.getenv("NEO4J_DATABASE", "iot")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    print(f"Connecting to Neo4j Database ('{db_name}')...")
    with driver.session(database=db_name) as session:
        # 1. Node Distribution Graph
        print("Generating Node Distribution Graph from Knowledge Graph...")
        node_query = """
        CALL db.labels() YIELD label
        MATCH (n) WHERE label IN labels(n)
        RETURN label, count(n) AS count
        ORDER BY count DESC
        """
        results = session.run(node_query)
        labels = []
        counts = []
        for record in results:
            labels.append(record['label'])
            counts.append(record['count'])
            
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(x=labels, y=counts, palette="viridis", hue=labels, legend=False)
        plt.title("Knowledge Graph Node Distribution", fontsize=16, fontweight='bold', pad=20)
        plt.xlabel("Node Type", fontsize=14)
        plt.ylabel("Count (Log Scale)", fontsize=14)
        plt.yscale("log")
        plt.xticks(rotation=45, ha='right')
        
        # Add data labels
        for p in ax.patches:
            height = p.get_height()
            if height > 0:
                ax.text(p.get_x() + p.get_width()/2., height * 1.2,
                        f'{int(height):,}', ha='center', va='bottom', fontsize=10, rotation=0)

        plt.tight_layout()
        plt.savefig(RESULTS_DIR / "academic_kg_node_distribution.png", dpi=600, bbox_inches='tight')
        plt.close()
        
        # 2. Top Attacks Graph
        print("Generating Top Attacks Graph from Graph Topology...")
        attack_query = """
        MATCH (f:Flow)-[:CLASSIFIED_AS]->(a:AttackType)
        WHERE a.name <> 'Benign'
        RETURN a.name AS attack, count(f) AS count
        ORDER BY count DESC LIMIT 10
        """
        results = session.run(attack_query)
        attacks = []
        acounts = []
        for record in results:
            attacks.append(record['attack'])
            acounts.append(record['count'])
            
        plt.figure(figsize=(12, 7))
        ax = sns.barplot(y=attacks, x=acounts, palette="rocket", hue=attacks, legend=False)
        plt.title("Top 10 Detected Attack Vectors (By Flow Count)", fontsize=16, fontweight='bold', pad=20)
        plt.xlabel("Number of Malicious Network Flows", fontsize=14)
        plt.ylabel("Attack Vector", fontsize=14)
        
        # Add data labels
        for p in ax.patches:
            width = p.get_width()
            if width > 0:
                ax.text(width * 1.05, p.get_y() + p.get_height()/2.,
                        f'{int(width):,}', ha='left', va='center', fontsize=11)

        # Expand xlim to fit labels
        if len(acounts) > 0:
            plt.xlim(0, max(acounts) * 1.25)
            
        plt.tight_layout()
        plt.savefig(RESULTS_DIR / "academic_top_10_attacks.png", dpi=600, bbox_inches='tight')
        plt.close()
        
        # 3. Protocol Usage
        print("Generating Protocol Usage Graph...")
        proto_query = """
        MATCH (f:Flow)
        WHERE f.service IS NOT NULL AND f.service <> '-'
        RETURN f.service AS protocol, count(f) AS count
        ORDER BY count DESC LIMIT 5
        """
        results = session.run(proto_query)
        protos = []
        pcounts = []
        for record in results:
            protos.append(str(record['protocol']))
            pcounts.append(record['count'])
            
        plt.figure(figsize=(8, 8))
        colors = sns.color_palette("muted")[0:len(protos)]
        plt.pie(pcounts, labels=protos, autopct='%1.1f%%', colors=colors, startangle=140, textprops={'fontsize': 12})
        plt.title("Top 5 Network Protocols Used", fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig(RESULTS_DIR / "academic_protocol_distribution.png", dpi=600, bbox_inches='tight')
        plt.close()

    driver.close()
    print("Academic graph generation complete. Saved to results/ folder.")

if __name__ == "__main__":
    generate_graphs()
