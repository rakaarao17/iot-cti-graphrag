import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.services.threat_explanation.explainer import ThreatExplainer
from src.services.threat_explanation.prompt_templates import get_template

def generate():
    explainer = ThreatExplainer()
    
    device_info = {
        'ip': '0.0.0.0',
        'total_flows': 6313366,
        'malicious_flows': 5588644,
        'attack_types': ['VulnerabilityScan', 'DDoS-SynonymousIP_Flood', 'DDoS-ICMP_Flood', 'Mirai-udpplain', 'Mirai-greip_flood', 'MITM-ArpSpoofing', 'BrowserHijacking', 'SqlInjection'],
        'malicious_ratio': 0.885
    }
    
    device_context = "\n".join(f"  {k}: {v}" for k, v in device_info.items())
    
    graph_context = explainer._retrieve_context("DDoS and Mirai botnet attack originating from IP 0.0.0.0", search_type="device")
    
    template = get_template("device_profile")
    prompt = template.format(
        device_context=device_context,
        graph_context=graph_context,
    )
    
    print("Querying Local Gemma 4 LLM...")
    response = explainer.llm.generate(prompt)
    analysis = response
    
    print(analysis)
    
    with open("results/threat_analysis_reports.md", "a") as f:
        f.write("\n\n## Automated Threat Analysis for Master Attacker IP: 0.0.0.0\n")
        f.write(analysis)
        f.write("\n")

if __name__ == "__main__":
    generate()
