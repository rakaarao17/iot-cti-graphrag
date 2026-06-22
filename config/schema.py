"""
Knowledge Graph Schema Definitions.
Defines node labels, relationship types, properties, and MITRE ATT&CK mappings
for the IoT Cyber Threat Intelligence Knowledge Graph.
"""

# ── Node Labels ─────────────────────────────────────────────────────────────

NODE_LABELS = {
    "Device":          "An IoT device identified by IP address",
    "Flow":            "A single network flow/connection between devices",
    "AttackType":      "A specific attack classification label",
    "AttackCategory":  "High-level attack category grouping",
    "Protocol":        "Network protocol (TCP, UDP, ICMP)",
    "Port":            "Network port number",
    "MITRETechnique":  "MITRE ATT&CK technique reference",
    "Dataset":         "Source dataset metadata",
}

# ── Relationship Types ──────────────────────────────────────────────────────

RELATIONSHIP_TYPES = {
    "INITIATES":          ("Device", "Flow",           "Device initiates a network flow"),
    "TARGETS":            ("Flow",   "Device",         "Flow targets a destination device"),
    "CLASSIFIED_AS":      ("Flow",   "AttackType",     "Flow is classified as an attack type"),
    "BELONGS_TO":         ("AttackType", "AttackCategory", "Attack type belongs to a category"),
    "MAPS_TO":            ("AttackType", "MITRETechnique", "Attack type maps to MITRE technique"),
    "USES":               ("Flow",   "Protocol",       "Flow uses a network protocol"),
    "ON_PORT":            ("Flow",   "Port",            "Flow communicates on a port"),
    "COMMUNICATES_WITH":  ("Device", "Device",          "Aggregated device-to-device communication"),
    "IN_DATASET":         ("Device", "Dataset",         "Device appears in a dataset"),
}

# ── Node Property Schemas ───────────────────────────────────────────────────

NODE_PROPERTIES = {
    "Device": {
        "ip":           "str  — IP address (unique key)",
        "role":         "str  — 'source', 'target', or 'both'",
        "dataset":      "str  — originating dataset name",
        "first_seen":   "float — earliest timestamp",
        "last_seen":    "float — latest timestamp",
        "flow_count":   "int  — total flows involving this device",
        "embedding":    "list — vector embedding (384-dim)",
    },
    "Flow": {
        "uid":          "str   — unique flow identifier",
        "timestamp":    "float — flow start time (epoch)",
        "duration":     "float — flow duration in seconds",
        "orig_bytes":   "int   — bytes from originator",
        "resp_bytes":   "int   — bytes from responder",
        "orig_pkts":    "int   — packets from originator",
        "resp_pkts":    "int   — packets from responder",
        "conn_state":   "str   — connection state (e.g., SF, S0, REJ)",
        "service":      "str   — application service (http, dns, etc.)",
        "label":        "str   — attack label",
        "dataset":      "str   — originating dataset",
    },
    "AttackType": {
        "name":         "str  — attack type name (unique key)",
        "description":  "str  — human-readable description",
        "severity":     "str  — low / medium / high / critical",
        "count":        "int  — total flows with this label",
        "embedding":    "list — vector embedding (384-dim)",
    },
    "AttackCategory": {
        "name":         "str  — category name (unique key)",
        "severity":     "str  — overall severity level",
        "description":  "str  — category description",
    },
    "Protocol": {
        "name":         "str  — protocol name: TCP, UDP, ICMP (unique key)",
    },
    "Port": {
        "number":       "int  — port number (unique key)",
        "service_name": "str  — well-known service name if any",
    },
    "MITRETechnique": {
        "technique_id": "str  — e.g., T1498 (unique key)",
        "name":         "str  — technique name",
        "tactic":       "str  — tactic phase (e.g., Impact, Discovery)",
        "description":  "str  — detailed description",
        "url":          "str  — MITRE ATT&CK reference URL",
        "embedding":    "list — vector embedding (384-dim)",
    },
    "Dataset": {
        "name":         "str  — dataset name (unique key)",
        "version":      "str  — version string",
        "source":       "str  — source URL or organization",
        "description":  "str  — dataset description",
    },
}

# ── Attack Label Taxonomy ───────────────────────────────────────────────────
# Maps raw labels from both datasets to unified (category, attack_type) tuples

ATTACK_CATEGORY_MAP = {
    # ── Benign ──
    "Benign":           "Benign",
    "benign":           "Benign",
    # ── DDoS ──
    "DDoS":             "DDoS",
    "DDoS-ACK_Fragmentation":   "DDoS",
    "DDoS-UDP_Flood":           "DDoS",
    "DDoS-SlowLoris":           "DDoS",
    "DDoS-ICMP_Flood":          "DDoS",
    "DDoS-RSTFINFlood":         "DDoS",
    "DDoS-PSHACK_Flood":        "DDoS",
    "DDoS-HTTP_Flood":          "DDoS",
    "DDoS-SYN_Flood":           "DDoS",
    "DDoS-SynonymousIP_Flood":  "DDoS",
    "DDoS-TCP_Flood":           "DDoS",
    "DDoS-UDP_Fragmentation":   "DDoS",
    "DDoS-ICMP_Fragmentation":  "DDoS",
    # ── DoS ──
    "DoS":              "DoS",
    "DoS-UDP_Flood":    "DoS",
    "DoS-TCP_Flood":    "DoS",
    "DoS-SYN_Flood":    "DoS",
    "DoS-HTTP_Flood":   "DoS",
    # ── Reconnaissance ──
    "Recon":            "Reconnaissance",
    "PortScan":         "Reconnaissance",
    "Recon-PingSweep":  "Reconnaissance",
    "Recon-OSScan":     "Reconnaissance",
    "Recon-PortScan":   "Reconnaissance",
    "Recon-HostDiscovery": "Reconnaissance",
    # ── Brute Force ──
    "BruteForce":       "BruteForce",
    "BruteForce-SSH":   "BruteForce",
    "BruteForce-HTTP":  "BruteForce",
    # ── Spoofing ──
    "Spoofing":         "Spoofing",
    "Spoofing-ARP":     "Spoofing",
    "Spoofing-DNS":     "Spoofing",
    # ── Mirai ──
    "Mirai":            "Mirai",
    "Mirai-greeth_flood":  "Mirai",
    "Mirai-greip_flood":   "Mirai",
    "Mirai-udpplain":      "Mirai",
    # ── Web Attacks ──
    "Web":              "WebAttack",
    "Web-XSS":          "WebAttack",
    "Web-SQLi":         "WebAttack",
    "Web-BrowserHijacking": "WebAttack",
    # ── C&C ──
    "C&C":              "CommandAndControl",
    "C&C-FileDownload": "CommandAndControl",
    "C&C-HeartBeat":    "CommandAndControl",
    "C&C-HeartBeat-Attack":  "CommandAndControl",
    "C&C-HeartBeat-FileDownload": "CommandAndControl",
    "C&C-Mirai":        "CommandAndControl",
    "C&C-Torii":        "CommandAndControl",
    # ── IoT-23 Specific ──
    "PartOfAHorizontalPortScan":  "Reconnaissance",
    "Okiru":            "Mirai",
    "Torii":            "CommandAndControl",
    "FileDownload":     "CommandAndControl",
    "Attack":           "Unknown",
}

# ── Attack Category Metadata ────────────────────────────────────────────────

ATTACK_CATEGORIES = {
    "Benign": {
        "severity": "none",
        "description": "Normal, legitimate network traffic from IoT devices.",
    },
    "DDoS": {
        "severity": "critical",
        "description": "Distributed Denial of Service — volumetric attacks flooding targets with traffic from multiple sources to overwhelm network resources.",
    },
    "DoS": {
        "severity": "high",
        "description": "Denial of Service — attacks from a single source aimed at disrupting service availability.",
    },
    "Reconnaissance": {
        "severity": "medium",
        "description": "Network scanning and probing to discover hosts, open ports, and running services before launching targeted attacks.",
    },
    "BruteForce": {
        "severity": "high",
        "description": "Automated credential guessing attacks against authentication services (SSH, HTTP, Telnet).",
    },
    "Spoofing": {
        "severity": "high",
        "description": "Identity falsification attacks (ARP spoofing, DNS spoofing) to intercept or redirect network traffic.",
    },
    "Mirai": {
        "severity": "critical",
        "description": "Mirai botnet family — IoT malware that recruits devices into botnets for large-scale DDoS attacks.",
    },
    "WebAttack": {
        "severity": "high",
        "description": "Web application attacks including XSS, SQL injection, and browser hijacking.",
    },
    "CommandAndControl": {
        "severity": "critical",
        "description": "Command & Control communications — infected devices connecting to attacker infrastructure for instructions and data exfiltration.",
    },
    "Unknown": {
        "severity": "medium",
        "description": "Unclassified malicious traffic that does not fit into known categories.",
    },
}

# ── MITRE ATT&CK Mappings ──────────────────────────────────────────────────

MITRE_ATTACK_MAP = {
    "DDoS": {
        "technique_id": "T1498",
        "name": "Network Denial of Service",
        "tactic": "Impact",
        "description": "Adversaries may perform Network Denial of Service (DoS) attacks to degrade or block the availability of targeted resources to users. Network DoS can be performed by exhausting the network bandwidth services rely on.",
        "url": "https://attack.mitre.org/techniques/T1498/",
    },
    "DoS": {
        "technique_id": "T1499",
        "name": "Endpoint Denial of Service",
        "tactic": "Impact",
        "description": "Adversaries may perform Endpoint Denial of Service (DoS) attacks to degrade or block the availability of services to users by exhausting system resources.",
        "url": "https://attack.mitre.org/techniques/T1499/",
    },
    "Reconnaissance": {
        "technique_id": "T1046",
        "name": "Network Service Scanning",
        "tactic": "Discovery",
        "description": "Adversaries may attempt to get a listing of services running on remote hosts and local network infrastructure devices, including those that may be vulnerable to remote software exploitation.",
        "url": "https://attack.mitre.org/techniques/T1046/",
    },
    "BruteForce": {
        "technique_id": "T1110",
        "name": "Brute Force",
        "tactic": "Credential Access",
        "description": "Adversaries may use brute force techniques to gain access to accounts when passwords are unknown or when password hashes are obtained.",
        "url": "https://attack.mitre.org/techniques/T1110/",
    },
    "Spoofing": {
        "technique_id": "T1557",
        "name": "Adversary-in-the-Middle",
        "tactic": "Credential Access, Collection",
        "description": "Adversaries may attempt to position themselves between two or more networked devices to support follow-on behaviors such as network sniffing or transmitted data manipulation.",
        "url": "https://attack.mitre.org/techniques/T1557/",
    },
    "Mirai": {
        "technique_id": "T1584",
        "name": "Compromise Infrastructure",
        "tactic": "Resource Development",
        "description": "Adversaries may compromise third-party infrastructure that can be used during targeting. IoT botnets like Mirai compromise vulnerable devices to build attack infrastructure.",
        "url": "https://attack.mitre.org/techniques/T1584/",
    },
    "WebAttack": {
        "technique_id": "T1190",
        "name": "Exploit Public-Facing Application",
        "tactic": "Initial Access",
        "description": "Adversaries may attempt to take advantage of a weakness in an Internet-facing computer or program using software, data, or commands in order to cause unintended or unanticipated behavior.",
        "url": "https://attack.mitre.org/techniques/T1190/",
    },
    "CommandAndControl": {
        "technique_id": "T1071",
        "name": "Application Layer Protocol",
        "tactic": "Command and Control",
        "description": "Adversaries may communicate using OSI application layer protocols to avoid detection/network filtering by blending in with existing traffic.",
        "url": "https://attack.mitre.org/techniques/T1071/",
    },
    "Unknown": {
        "technique_id": "T1595",
        "name": "Active Scanning",
        "tactic": "Reconnaissance",
        "description": "Adversaries may execute active reconnaissance scans to gather information that can be used during targeting.",
        "url": "https://attack.mitre.org/techniques/T1595/",
    },
}

# ── Well-Known Ports ────────────────────────────────────────────────────────

WELL_KNOWN_PORTS = {
    20: "FTP-Data", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 67: "DHCP", 68: "DHCP", 80: "HTTP", 110: "POP3",
    123: "NTP", 143: "IMAP", 161: "SNMP", 443: "HTTPS", 445: "SMB",
    993: "IMAPS", 995: "POP3S", 1883: "MQTT", 3306: "MySQL",
    5432: "PostgreSQL", 5683: "CoAP", 6379: "Redis", 8080: "HTTP-Alt",
    8443: "HTTPS-Alt", 8883: "MQTT-TLS", 27017: "MongoDB",
}

# ── Unified Feature Schema ──────────────────────────────────────────────────
# The columns that the feature engineering stage produces

UNIFIED_FEATURE_COLUMNS = [
    "uid",              # Unique flow identifier
    "timestamp",        # Unix epoch timestamp
    "src_ip",           # Source IP address
    "src_port",         # Source port number
    "dst_ip",           # Destination IP address
    "dst_port",         # Destination port number
    "protocol",         # TCP, UDP, ICMP
    "service",          # Application-layer service
    "duration",         # Flow duration (seconds)
    "orig_bytes",       # Bytes from originator
    "resp_bytes",       # Bytes from responder
    "orig_pkts",        # Packets from originator
    "resp_pkts",        # Packets from responder
    "conn_state",       # Connection state code
    "label",            # Attack type label (detailed)
    "attack_category",  # High-level attack category
    "dataset",          # Source dataset name
    # Derived features
    "bytes_ratio",      # orig_bytes / (orig_bytes + resp_bytes)
    "packet_ratio",     # orig_pkts / (orig_pkts + resp_pkts)
    "bytes_per_pkt",    # total_bytes / total_pkts
    "duration_cat",     # short (<1s), medium (1-60s), long (>60s)
    "port_category",    # well-known, registered, dynamic
]
