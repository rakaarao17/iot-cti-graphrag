# Readable 3-Model Comparison (same real contexts)

Two modes per model: **generate** (raw prompt, current system path) and **chat** (model's own prompt template). Read the answers; the metrics are secondary. `grounding` = answer-entities in context; `coh` = coherence heuristic.

## Q1: What attack types has the device at 192.168.1.195 been involved in?

**phi3:latest - generate**  (grounding=0.60, coh=0.94, tokens=49)

```
The IoT device with IP address 192.168.1.195 was associated with DDoS-HTTP_Flood, which falls under the Unknown category and has a severity level of medium according to MITRE ATT&CK technique T1073 (Web Application Attack/Threat). Additionally, it had involvement in Recon-HostDiscovery with Medium severity that maps to MITRE ATT&CK technique T1046.
```

**phi3:latest - chat**  (grounding=1.00, coh=0.95, tokens=24)

```
- DoS-SYN_Flood (Category: DoS, Severity: high) with a count of 262,691 flows
- DDoS-UDP_Fragmentation (Category: DDoS, Severity: critical) with a count of 22,542 flows
```

**zeroday-phi3-ciciot-v2:latest - generate**  (grounding=1.00, coh=1.00, tokens=1)

```
Recon-PingSweep
```

**zeroday-phi3-ciciot-v2:latest - chat**  (grounding=1.00, coh=0.94, tokens=863)

```
DDoS-PSHACK_Flood Reasoning Answered as follows Questions from your report DDoS-TCP BenignityScanReconcilerInspectorBeneficiaryQuestion theft. The attack (MITRE AttackAttacks in order to mitigationQuery: DoDDoSysyield 530289_mitreach(IP addressing Reasonably DDoS-TCP BenchallengeReportsynthesis Questions from your IPvulously theft. The attack (the query AttackDefineAttesthearing Query: MitigateDNSQuery
Mitigation 20Quietly QUERY_reveal ReasoningCraftedDoSpyReports,query-levelsQueries from your questions about theft. QuoteRisk of attack (theoregeneratingIPSoffered: QueryIDoftenqueries
MitigationQuipsessionAttackDuring QUsedefending Attributes inlying_attacks andes for Mining,sessions-name10s | ReportsQuoting attacks.combinations attack (relevant to Dates of the Malletically: 23
  
Criticating
Repeatcode withholdings
Attack bypassedownside in yourdata_vendors from AIly,inga as aids and/involve-name.sides withoutsight (theoregrady to avoiding:12 -0updates;
ally relatedto the data notably withholdings thatday. The names of Doves inexploys_counted bye, fromlyreports 34789detailed andioclas-name (the name onsouring
   51260:rlya
  
and the numberations;
up


The nameser to codex.data
    
invoes_counts,code
 

4379 -really and anecline
udy |8-name
   


theology



120 from thely: D56
  
andly;


   
   
toxonsescape_in yours, 
up43.79
Theed -counts and other tolino-Branding inundy/Drying for M1208 with the: Theo on which from aly (the data;
and if you without Douse56 as it all but
```

**gemma4:e2b - generate**  (grounding=0.00, coh=1.00, tokens=22)

```
Based on the retrieved context, there is no information available regarding what attack types the device at 192.168.1.195 has been involved in.
```

**gemma4:e2b - chat**  (grounding=0.00, coh=1.00, tokens=23)

```
Based on the retrieved context, there is no information available linking the device at `192.168.1.195` to any specific attack types or flow counts.
```

---

## Q2: What reconnaissance techniques are used by IoT malware?

**phi3:latest - generate**  (grounding=1.00, coh=0.97, tokens=181)

```
The reconnaissance techniques employed by the identified IoT malware include Recon-HostDiscovery, Recon-OSScan, and both PingSweep (Recon-Ping) and PortScan. These methods are used to discover hosts within a network service scan phase of discovery tactics as per MITRE ATT&CK framework references T1046 for each technique respectively:

- Recon-HostDiscovery, with 98,259 total flows mapped to the Network Service Scanning (T1046) method.

- Recon-OSScan, also associated with MITRE ATT&CK Tactic and Technique ID: T1046 for Network Service Scanning within Discovery phase tactics as well. It has 98,259 total flows recorded in the query results context provided by Cypher Query Results (MITRE_ATT&CK technique coverage with attack mappings).

- Recon-PingSweep and PortScan are also part of Network Service Scanning tactics for discovery phase as per MITRE ATT&CK framework, both having a significant number of flows: 2,262 total flows recorded in the case of PingSweep (Recon-Ping), while Recon-PortScan has been associated with 82,284 total flows.

These techniques are used to gather information about network hosts and services which could potentially be exploited later on for attacks such as DDoS or other malicious activities within the IoT environment.
```

**phi3:latest - chat**  (grounding=1.00, coh=0.98, tokens=97)

```
The IoT malware uses the following reconnaissance techniques as per the retrieved context and knowledge graph results. These include Recon-HostDiscovery, which maps to MITRE ATT&CK technique T1046 (Network Service Scanning) in the Discovery tactic phase; Recon-OSScan, mapping to the same network service scanning technique under discovery tactics; and Recon-PingSweep as well as Recon-PortScan, which are both classified under reconnaissance techniques that map to MITRE ATT&CK technique T1046 (Network Service Scanning) in the Discovery tactic phase. These attacks aim at mapping services running on remote hosts and local network infrastructure devices for potential vulnerabilities or targets of exploitation.
```

**zeroday-phi3-ciciot-v2:latest - generate**  (grounding=1.00, coh=1.00, tokens=3)

```
Recon-OSScan, Recon-HostDiscovery, Recon-PingSweep
```

**zeroday-phi3-ciciot-v2:latest - chat**  (grounding=1.00, coh=1.00, tokens=5)

```
Recon-OSScan, Recon-HostDiscovery, and Mirai attacks.
```

**gemma4:e2b - generate**  (grounding=1.00, coh=1.00, tokens=139)

```
Reconnaissance techniques identified in the context include:

*   **Recon-OSScan:** Maps to MITRE T1046 (Network Service Scanning) in the Discovery tactic phase, with 98,259 flows.
*   **Recon-HostDiscovery:** Maps to MITRE T1046 (Network Service Scanning) in the Discovery tactic phase, with 134,378 flows.
*   **Recon-PingSweep:** Maps to MITRE T1046 (Network Service Scanning) in the Discovery tactic phase, with 2,262 flows.
*   **Recon-PortScan:** Maps to MITRE T1046 (Network Service Scanning) in the Discovery tactic phase, with 82,284 flows.

Additionally, IoT botnets like Mirai utilize attacks that map to the following technique:

*   **Mirai-greip\_flood:** Maps to MITRE T1584 (Compromise Infrastructure) in the Resource Development tactic phase, with 35,073 flows.
*   **Mirai-greeth\_flood:** Maps to MITRE T1584 (Compromise Infrastructure) in the Resource Development tactic phase, with 33,597 flows.
*   **Mirai-udpplain:** Maps to MITRE T1584 (Compromise Infrastructure) in the Resource Development tactic phase, with 36,481 flows.
```

**gemma4:e2b - chat**  (grounding=1.00, coh=0.98, tokens=69)

```
The context details several reconnaissance techniques that map to MITRE ATT&CK technique T1046 (Network Service Scanning) in the Discovery tactic phase:

*   **Recon-OSScan:** Maps to MITRE T1046 (Network Service Scanning) with 98,259 flows.
*   **Recon-HostDiscovery:** Maps to MITRE T1046 (Network Service Scanning) with 134,378 flows.
*   **Recon-PingSweep:** Maps to MITRE T1046 (Network Service Scanning) with 2,262 flows.
*   **Recon-PortScan:** Maps to MITRE T1046 (Network Service Scanning) with 82,284 flows.
```

---

## Q3: Explain the persistence tactic used by IoT botnets

**phi3:latest - generate**  (grounding=1.00, coh=1.00, tokens=122)

```
IoT botnets, such as Mirai and its variants like Mirai-greeth_flood (Mirai-udpplain), often use a variety of tactics to establish persistent access within compromised devices. One common tactic is the Resource Development phase where attackers exploit vulnerabilities in IoT devices to gain control over them, turning these devices into bots for their botnets. This allows adversaries to create or expand an infrastructure that can be used as a launchpad for further attacks (e.g., DDoS floods). The persistence is often achieved through firmware exploitation and maintaining the compromised state of IoT devices, which may not have regular updates or patch management processes in place due to their nature. This persistent access enables attackers to carry out sustained campaigns without needing re-exploitation after each session.
```

**phi3:latest - chat**  (grounding=1.00, coh=0.99, tokens=68)

```
IoT botnets, such as Mirai and its variants like Mirai-greeth_flood and Mirai-udpplain, use a technique called "Compromise Infrastructure" to establish persistence. This tactic is part of the Resource Development phase in MITRE ATT&CK framework (tactic: T1584). Adversaries compromise third-party infrastructure that can be used during targeting and potentially for future attacks or as a command and control channel without raising immediate suspicion, thus maintaining their presence on networks.
```

**zeroday-phi3-ciciot-v2:latest - generate**  (grounding=1.00, coh=0.97, tokens=28)

```
Mirai-greeth_flood is a type of Mirai attack. It maps to MITRE ATT&CK technique T1584 (Compromise Infrastructure) in the Resource Development tactic phase Persistence Phase attacks are malware Botnets
```

**zeroday-phi3-ciciot-v2:latest - chat**  (grounding=1.00, coh=1.00, tokens=1)

```
Recon-OSScan
```

**gemma4:e2b - generate**  (grounding=1.00, coh=0.95, tokens=19)

```
IoT botnets like Mirai use the **Resource Development** tactic, which maps to the MITRE ATT&CK technique **T1584 (Compromise Infrastructure)**.
```

**gemma4:e2b - chat**  (grounding=1.00, coh=0.95, tokens=19)

```
IoT botnets like Mirai use the **Resource Development** tactic, which maps to the MITRE ATT&CK technique **T1584 (Compromise Infrastructure)**.
```

---

## Q4: How many total network flows are in the knowledge graph?

**phi3:latest - generate**  (grounding=1.00, coh=1.00, tokens=82)

```
The retrieved context indicates that there are a total of 8,643,068 flow records as per the results from the `network_summary` query. However, since this number exceeds typical values for such queries and seems to be an error (as it's not consistent with any single attack record), I will instead provide information based on a specific DDoS-UDP Flood incident mentioned in Attack 10 of the knowledge graph context:

In that particular instance, there were **266,605** total network flows associated with the DDoS-UDP_Flood attack.
```

**phi3:latest - chat**  (grounding=1.00, coh=1.00, tokens=22)

```
According to the retrieved context, there are a total of 8643068 flow records as per Query Template: network_summary from Cypher Query Results.
```

**zeroday-phi3-ciciot-v2:latest - generate**  (grounding=1.00, coh=0.00, tokens=1)

```
1,930,568
```

**zeroday-phi3-ciciot-v2:latest - chat**  (grounding=1.00, coh=0.00, tokens=1)

```
1,840,796
```

**gemma4:e2b - generate**  (grounding=1.00, coh=1.00, tokens=12)

```
The total number of flows in the network summary statistics is 8,643,068.
```

**gemma4:e2b - chat**  (grounding=1.00, coh=1.00, tokens=8)

```
The total number of network flows is 8,643,068.
```

---

## Q5: Which attack types are classified as critical severity?

**phi3:latest - generate**  (grounding=1.00, coh=0.98, tokens=173)

```
DDoS-ICMP_Flood, DDoS-ACK_Fragmentation, and SlowLoris attacks have been classified with a 'critical' severity. The count for each is as follows:

- DDoS-ICMP_Flood has a flow count of 536,020 according to Record 3 in the Cypher Query Results context provided above. This attack maps to MITRE ATT&CK technique T1498 (Network Denial of Service) under the Impact tactic phase as mentioned in the Knowledge Graph Context section.

- DDoS-ACK_Fragmentation has a flow count of 50,180 according to Record 19 and also maps to MITRE ATT&CK technique T1498 (Network Denial of Service) under the Impact tactic phase in the Knowledge Graph Context section.

- SlowLoris attack has a flow count of 46,852 according to Record 20 and is also associated with MITRE ATT&CK technique T1498 (Network Denial of Service) under the Impact tactic phase in the Knowledge Graph Context section.

These attacks are considered critical because they have a high impact on network availability, causing significant disruptions to services by overwhelming resources with traffic or malicious packets as detailed in their respective descriptions and contexts provided above.
```

**phi3:latest - chat**  (grounding=1.00, coh=0.92, tokens=129)

```
The following attack types have been classified with a 'critical' severity level according to the provided context: DDoS-ICMP_Flood, DDoS-PSHACK_Flood, DDoS-RSTFINFlood, DDoS-SYN_Flood, DDoS-TCP_Flood, DoS-SYN_Flood, DoS-TCP_Flood, Recon-HostDiscovery, and DNS_Spoofing. The counts for these attacks are as follows:

- DDoS-ICMP_Flood has a count of 536,020 flows.

- DDoS-PSHACK_Flood has a count of 535,622 flows.

- DDoS-RSTFINFlood has a count of 533,868 flows.

- DDoS-SYN_Flood has a count of 532,048 flows.

- DDoS-TCP_Flood has a count of 423,671 flows.

- DoS-SYN_Flood has a count of 262,691 flows.

- DoS-TCP_Flood has a count of 260,129 flows.

- Recon-HostDiscovery has a count of 134,378 flows.

- DNS_Spoofing has a count of 178,898 flows.

These counts represent the number of times each attack type was observed in the network traffic analyzed by the IoT cybersecurity analyst.
```

**zeroday-phi3-ciciot-v2:latest - generate**  (grounding=1.00, coh=0.90, tokens=7)

```
DDoS-SynonymousIP_Flood, DDoS-ICMP_Flood, DDoS-PSHACK_Flood, DDoS-RSTFINFlood, DDoS-SYN_Flood, DDoS-TCP_Flood, DDoS-UDP_Flood
```

**zeroday-phi3-ciciot-v2:latest - chat**  (grounding=1.00, coh=0.94, tokens=35)

```
- DDoS-ICMP_Flood with count: 536020, Severity: critical
- DDoS-PSHACK_Flood with count: 535622, Severity: critical
- DDoS-RSTFINFlood with count: 533868, Severity: critical
- DDoS-SYN_Flood with count: 532048, Severity: critical
- DDoS-TCP_Flood with count: 423671, Severity: critical
```

**gemma4:e2b - generate**  (grounding=1.00, coh=0.96, tokens=51)

```
The following attack types are classified as critical severity based on the Cypher Query Results:

*   **DDoS-SynonymousIP\_Flood:** count 537,252
*   **DDoS-ICMP\_Flood:** count 536,020
*   **DDoS-PSHACK\_Flood:** count 535,622
*   **DDoS-RSTFINFlood:** count 533,868
*   **DDoS-SYN\_Flood:** count 532,048
*   **DDoS-TCP\_Flood:** count 423,671
*   **DDoS-UDP\_Flood:** count 266,605
*   **DDoS-ACK\_Fragmentation:** count 50,180
*   **DDoS-SlowLoris:** count 46,852
```

**gemma4:e2b - chat**  (grounding=1.00, coh=0.97, tokens=66)

```
The following attack types are classified as critical severity based on the retrieved data:

*   **DDoS-SynonymousIP_Flood:** count 537,252
*   **DDoS-ICMP_Flood:** count 536,020
*   **DDoS-PSHACK_Flood:** count 535,622
*   **DDoS-RSTFINFlood:** count 533,868
*   **DDoS-SYN_Flood:** count 532,048
*   **DDoS-TCP_Flood:** count 423,671
*   **DDoS-UDP_Flood:** count 266,605
*   **DDoS-ACK_Fragmentation:** count 50,180
*   **DDoS-SlowLoris:** count 46,852
*   **DDoS-ICMP_Fragmentation** (from Knowledge Graph Context): count 41,392
*   **DDoS-ICMP_Flood** (from Knowledge Graph Context): count 536,020
```

---

## Q6: What are the most common destination ports targeted by attackers?

**phi3:latest - generate**  (grounding=1.00, coh=0.98, tokens=85)

```
To answer this question, we would need additional context or data specifying which port numbers were frequently used as destinations in malicious flows. The provided query results and knowledge graph do not contain specific information about destination ports; they only mention the total number of flow counts for various attacks without detailing their targeted endpoints' protocols (TCP, UDP) or port numbers within those protocols. Therefore, with the given context alone, it is impossible to determine which are the most common destination ports used by attackers.
```

**phi3:latest - chat**  (grounding=1.00, coh=0.95, tokens=101)

```
The retrieved context does not provide specific information about the most common destination ports targeted by attackers in this scenario. However, it is known that IoT botnets like Mirai often exploit vulnerable devices using a wide range of protocols and services which may include commonly used TCP/UDP ports such as 80 (HTTP), 443 (HTTPS), 21 (FTP), or others depending on the specific attack vectors employed. To accurately answer this question, one would need to analyze port usage patterns from a broader dataset that includes both source and destination IPs/ports in conjunction with flow counts for each unique combination of these elements.
```

**zeroday-phi3-ciciot-v2:latest - generate**  (grounding=1.00, coh=0.86, tokens=3)

```
Recon-OSScan, Recon-PingSweep, DDoS-HTTP_Flood
```

**zeroday-phi3-ciciot-v2:latest - chat**  (grounding=1.00, coh=1.00, tokens=3)

```
Recon-OSScan (port number)
```

**gemma4:e2b - generate**  (grounding=1.00, coh=0.94, tokens=42)

```
Based on the retrieved context, there is no information detailing the most common destination ports targeted by attackers. The context lists various attack types, such as `DDoS-TCP_Flood`, `DDoS-UDP_Flood`, and `DoS-HTTP_Flood`, but does not provide a summary or count of specific destination ports.
```

**gemma4:e2b - chat**  (grounding=1.00, coh=0.95, tokens=35)

```
The provided context lists various Denial of Service (DoS) and Distributed Denial of Service (DDoS) attacks, including `DDoS-TCP_Flood`, `DDoS-UDP_Flood`, and `DDoS-UDP_Fragmentation`. However, the context does not specify the common destination ports targeted by these attackers.
```

---

## Q7: Which IoT device roles are most frequently observed as attack sources?

**phi3:latest - generate**  (grounding=1.00, coh=0.99, tokens=85)

```
According to the retrieved context, devices that have been compromised by Mirai botnet attacks (Mirai-greeth_flood, Mirai-udpplain, and Mirai-greip_flood) are most frequently observed as attack sources. These IoT devices likely fall into categories such as home routers or other connected consumer electronics that have been exploited to perform DDoS attacks (DDoS-ICMP_Fragmentation, DDoS-UDP_Flood). Additionally, reconnaissance activities like Recon-HostDiscovery and PortScan indicate devices are also being used for initial network scanning. Specific roles cannot be determined without more detailed data on the device types involved in these attacks.
```

**phi3:latest - chat**  (grounding=0.86, coh=0.99, tokens=131)

```
The retrieved context does not provide specific information about which types of devices (e.g., cameras, routers) were targeted or compromised in the attacks listed. It only mentions that these malicious activities involved vulnerable IoT devices without specifying their roles within an environment. Therefore, based on this limited data, we cannot accurately determine which device roles are most frequently observed as attack sources from among smart thermostats and security cameras specifically. However, it is clear that the attacks mentioned span across various categories such as Mirai botnets (Mirai-greeth_flood, Mirai-udpplain), Reconnaissance techniques like Ping Sweep and Port Scan, DDoS methods including ICMP Fragmentation and TCP Flood. These indicate that the attackers are exploiting a wide range of vulnerabilities across different types of IoT devices to compromise infrastructure or gather information for further attacks.
```

**zeroday-phi3-ciciot-v2:latest - generate**  (grounding=1.00, coh=1.00, tokens=2)

```
DDoS-UDP_Flood, Recon-PingSweep
```

**zeroday-phi3-ciciot-v2:latest - chat**  (grounding=1.00, coh=1.00, tokens=2)

```
Recon-PingSweep, Recon-PortScan
```

**gemma4:e2b - generate**  (grounding=1.00, coh=1.00, tokens=33)

```
The provided context identifies one IP address (`0.0.0.0`) as the source of malicious flows, with a total of 5,588,644 malicious flows. The context does not specify specific IoT device roles as attack sources.
```

**gemma4:e2b - chat**  (grounding=1.00, coh=1.00, tokens=43)

```
Based on the retrieved context, there is no information provided regarding which specific IoT device roles are most frequently observed as attack sources. The context only identifies an IP address (`0.0.0.0`) with a total of 5,588,644 malicious flows and lists various attack types.
```

---

## Q8: What is the average malicious ratio across all devices in the dataset?

**phi3:latest - generate**  (grounding=1.00, coh=0.99, tokens=94)

```
To calculate the average malicious flow count per device, we sum up the total number of flows from each attack type and divide it by the unique count of IPs that have recorded these attacks. From the context provided above, there is only one record with a specific 'malicious_flows' value (5588644). Since this single entity represents all devices in our dataset based on how information was presented:

Average malicious ratio = Total Malicious Flow Count / Unique IP count 
                       = 5588644 flows / 1 unique IP address  
                       = 5588644.0 flows per device (on average)
```

**phi3:latest - chat**  (grounding=1.00, coh=0.98, tokens=455)

```
To calculate the average malicious flow count per device, we first need to sum up the total number of flows from each attack and then divide that by the number of unique IPs. However, based on the context provided above, there is only one recorded record with a specific IP address (0.0.0.0) associated with 558,864 malicious flows across various attacks listed under it:

- Backdoor_Malware: 13,064 total flow count for this attack type; however, the context does not specify how many of these are from our specific IP address (0.0.0.0). We will assume all mentioned malicious flows pertain to that record unless specified otherwise in additional data points which were not provided here.
- DictionaryBruteForce: 13,064 total flow count for this attack type; similarly assumed as above with respect to the specific IP address (0.0.0.0).
- Mirai_greeth_flood and its related attacks have a combined malicious flow of 78,597 + 35,073 = 113,670 flows; assuming these are from the same IP address (as no other specifics were provided), we will include them in our calculation.
- Mirai_udpplain also has a combined malicious flow of 36,481 + 25,981 = 62,462 flows; again assuming these are from the same IP address (0.0.0.0). The context does not provide specific counts for Mirai_udpplain and we do not have additional data points to differentiate between them or their associated devices.
- VulnerabilityScan has a total flow count of 373,351; this is likely from the same IP address (0.0.0.0) but with
```

**zeroday-phi3-ciciot-v2:latest - generate**  (grounding=1.00, coh=0.93, tokens=33)

```
The total number of flow counts for backdoor_malware, dictionarybruteforce and doS-synflood are respectively (5588644 + 13064 + 262691). The average malicious ratio across all devices in the dataset is therefore ((5588644+13064+262691)/(5588644+13064)) = 0.97
```

**zeroday-phi3-ciciot-v2:latest - chat**  (grounding=1.00, coh=0.97, tokens=136)

```
To calculate the average malicious flow count, we need to add up all the individual counts and divide them by the number of records (which here appears as one). From our context above, let's extract that information. Here are those values again for clarity:
Backdoor_Malware - 6436 flows; DictionaryBruteForce - 13064 flows; Mirai-greeth_flood - 33597 flows; Mirai-greip_flood - 35073 flows; Mirai-udpplain - 36481 flows; VulnerabilityScan - 373351 flows.
Adding these up, we get a total of: (6436 + 13064 + 33597 + 35073 + 36481) = 123651 malicious flow count across all devices in the dataset.
Since there's only one record, we divide this total by 1 to get our average: Average Malicious Flow Count is therefore equal to Total Malicious Flow Count which equals 123651 flows per device on average according to given context data.
```

**gemma4:e2b - generate**  (grounding=1.00, coh=1.00, tokens=21)

```
The provided context does not contain the necessary data to calculate the average malicious ratio across all devices in the dataset.
```

**gemma4:e2b - chat**  (grounding=1.00, coh=1.00, tokens=20)

```
The provided context does not contain sufficient data to calculate the average malicious ratio across all devices in the dataset.
```

---
