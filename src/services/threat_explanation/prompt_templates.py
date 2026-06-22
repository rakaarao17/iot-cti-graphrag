"""
Stage 6: Prompt Templates for Cyber Threat Explanation.

Curated prompts for different analysis scenarios, designed to extract
maximum value from the Knowledge Graph context.
"""


# -- Device Threat Profile ---------------------------------------------------

DEVICE_THREAT_PROFILE = """## Task: IoT Device Threat Assessment

Analyze the following IoT device and provide a comprehensive threat profile.

### Device Information
{device_context}

### Knowledge Graph Context
{graph_context}

### Required Analysis

1. **Threat Level Assessment** -- Rate as: CRITICAL / HIGH / MEDIUM / LOW / BENIGN
   - Justify the rating based on malicious flow ratio, attack diversity, and communication patterns

2. **Behavioral Analysis**
   - What type of device is this likely to be based on its traffic patterns?
   - Is the traffic pattern consistent with a compromised device, a bot, or legitimate IoT behavior?
   - Describe the communication patterns (who it talks to, volume, timing)

3. **Attack Classification**
   - List all observed attack types with flow counts
   - Map each attack to MITRE ATT&CK techniques
   - Identify the attack kill chain stage(s) this device participates in

4. **Risk Indicators**
   - Identify specific Indicators of Compromise (IoCs)
   - Flag any suspicious patterns (unusual ports, high volume, scanning behavior)

5. **Recommended Actions**
   - Immediate containment steps
   - Investigation priorities
   - Long-term mitigation strategies
"""

# -- Attack Type Explanation -------------------------------------------------

ATTACK_EXPLANATION = """## Task: Cyber Attack Analysis

Explain the following attack type observed in IoT network traffic.

### Attack Information
{attack_context}

### Knowledge Graph Context
{graph_context}

### Required Analysis

1. **Attack Description**
   - What is this attack? How does it work technically?
   - What protocols and ports does it exploit?
   - What is the typical attack vector?

2. **IoT Impact**
   - How does this attack specifically affect IoT devices?
   - What are the consequences for the device, network, and organization?
   - What data or functionality is at risk?

3. **MITRE ATT&CK Mapping**
   - Map to specific MITRE ATT&CK techniques (with IDs)
   - Identify the tactic phase(s)
   - Describe the adversary's likely objectives

4. **Detection Indicators**
   - What network signatures indicate this attack?
   - What flow characteristics are distinctive?
   - What anomalies should trigger alerts?

5. **Mitigation & Defense**
   - Network-level defenses (firewall rules, IDS signatures)
   - Device-level protections (firmware, configuration)
   - Organizational policies and procedures
"""

# -- Incident Summary Report ------------------------------------------------

INCIDENT_SUMMARY = """## Task: Security Incident Report

Generate a formal security incident report based on the evidence from the IoT network knowledge graph.

### Incident Context
{incident_context}

### Knowledge Graph Evidence
{graph_context}

### Report Format

**SECURITY INCIDENT REPORT**
**Date:** {date}
**Classification:** {classification}

1. **Executive Summary**
   - Brief overview of the incident (2-3 sentences max)
   - Key metrics: affected devices, attack types, duration

2. **Timeline**
   - First detection
   - Progression of the attack
   - Duration and scope

3. **Affected Assets**
   - List of compromised or targeted devices (IPs)
   - Services and ports affected
   - Data exposure assessment

4. **Attack Analysis**
   - Attack types identified with MITRE ATT&CK mapping
   - Attack flow and kill chain progression
   - Threat actor TTPs (Tactics, Techniques, Procedures)

5. **Impact Assessment**
   - Severity rating and justification
   - Business impact
   - Data integrity and availability status

6. **Remediation Actions**
   - Immediate response (completed/pending)
   - Short-term containment measures
   - Long-term remediation plan

7. **Recommendations**
   - Security control improvements
   - Monitoring enhancements
   - Policy updates
"""

# -- MITRE ATT&CK Mapping ---------------------------------------------------

MITRE_MAPPING = """## Task: MITRE ATT&CK Framework Analysis

Map the observed IoT network behaviors to the MITRE ATT&CK framework.

### Observed Behaviors
{behavior_context}

### Knowledge Graph Context
{graph_context}

### Required Analysis

For each observed behavior/attack:

1. **Technique Mapping**
   - Primary MITRE ATT&CK technique ID and name
   - Sub-techniques if applicable
   - Tactic phase (Reconnaissance, Initial Access, Execution, etc.)

2. **Evidence**
   - Specific network flows supporting the mapping
   - Traffic characteristics matching the technique
   - Confidence level of the mapping (High/Medium/Low)

3. **Kill Chain Position**
   - Where does this fit in the Cyber Kill Chain?
   - What are the likely preceding and following stages?

4. **Detection Opportunities**
   - What data sources can detect this technique?
   - Recommended detection rules or signatures
   - SIEM/SOAR integration points

Present the results as a table:
| Technique ID | Name | Tactic | Evidence | Confidence |
"""

# -- Dataset Comparison ------------------------------------------------------

DATASET_COMPARISON = """## Task: IoT Dataset Comparative Analysis

Compare the attack patterns and network characteristics between the IoT-23 and CICIoT2023 datasets.

### Comparison Data
{comparison_context}

### Knowledge Graph Context
{graph_context}

### Required Analysis

1. **Dataset Overview**
   - Compare scale (total flows, unique devices, attack types)
   - Compare time periods and capture methodologies
   - Compare device types and network topologies

2. **Attack Distribution Comparison**
   - Which attack types are common to both datasets?
   - Which are unique to each dataset?
   - Compare severity distributions

3. **Attack Evolution Insights**
   - How have IoT attack patterns evolved between the datasets?
   - Are there new attack types in the newer dataset?
   - Have existing attacks become more sophisticated?

4. **Threat Landscape Assessment**
   - What does the combined data tell us about the IoT threat landscape?
   - What are the most persistent threats?
   - What emerging threats should organizations prepare for?

5. **Research Implications**
   - How do the datasets complement each other for ML/AI research?
   - What gaps exist that future datasets should address?
"""

# -- Free-form Investigation -------------------------------------------------

INVESTIGATION_PROMPT = """## Task: Cyber Threat Intelligence Investigation

Investigate the following topic using evidence from the IoT network knowledge graph.

### Investigation Query
{query}

### Knowledge Graph Evidence
{graph_context}

### Instructions

As a senior threat intelligence analyst, provide:

1. **Key Findings** -- The most important discoveries from the data
2. **Technical Analysis** -- Deep-dive into the technical aspects
3. **Threat Assessment** -- Risk level, potential impact, actor motivation
4. **Evidence Chain** -- Specific data points supporting your conclusions
5. **Actionable Intelligence** -- What should defenders do with this information?
6. **Confidence Assessment** -- How confident are you in each finding?

Be specific, reference actual data from the knowledge graph, and distinguish between
facts (from the data) and inferences (your analysis).
"""


def get_template(template_name: str) -> str:
    """Get a prompt template by name."""
    templates = {
        "device_profile": DEVICE_THREAT_PROFILE,
        "attack_explanation": ATTACK_EXPLANATION,
        "incident_summary": INCIDENT_SUMMARY,
        "mitre_mapping": MITRE_MAPPING,
        "dataset_comparison": DATASET_COMPARISON,
        "investigation": INVESTIGATION_PROMPT,
    }
    return templates.get(template_name, INVESTIGATION_PROMPT)


def list_templates() -> list:
    """List all available prompt templates."""
    return [
        {"name": "device_profile", "description": "Comprehensive IoT device threat assessment"},
        {"name": "attack_explanation", "description": "Detailed attack type analysis with MITRE mapping"},
        {"name": "incident_summary", "description": "Formal security incident report"},
        {"name": "mitre_mapping", "description": "MITRE ATT&CK framework mapping"},
        {"name": "dataset_comparison", "description": "IoT-23 vs CICIoT2023 comparative analysis"},
        {"name": "investigation", "description": "Free-form threat intelligence investigation"},
    ]
