# 🧪 Testing & Evaluation Guide

This guide is designed for academic evaluators and professors to systematically test the **IoT Cyber Threat Intelligence GraphRAG Pipeline**. It explains the role of the database, how to verify the data integrity, and how to execute test cases.

---

## 1. Are the Inherent Scripts Enough?

**Yes.** The `.bat` scripts and Python files included in this project completely automate the **data processing, graph generation, and AI inference** workflows. 

However, because this project processes millions of rows of network traffic, it relies on a highly scalable Graph Database (Neo4j) that cannot run purely in Python memory. 

Therefore, the **only external requirement** is that the evaluator installs [Neo4j Desktop](https://neo4j.com/download/) to act as the local database server. 
Once the Neo4j Desktop server is running in the background, the inherent project scripts take over 100% of the workload.

---

## 2. How Neo4j Works in this Project

Neo4j is an enterprise-grade Graph Database. Unlike traditional SQL tables, Neo4j stores data as **Nodes** (Entities like Devices, IPs, Attacks) and **Relationships** (e.g., `(Device A)-[COMMUNICATES_WITH]->(Device B)`).

### The Architecture:
1. **Data Ingestion (Stage 3):** Our Python scripts read the raw `IoT-23` and `CICIoT2023` CSVs, clean the data using Pandas, and send Cypher queries to Neo4j to construct the massive network graph.
2. **Graph Algorithms (Stage 4):** We run structural algorithms (like `Node2Vec`) directly against Neo4j to calculate the mathematical shape of attack behaviors.
3. **GraphRAG (Stage 5 & 6):** When you ask a question in the CLI, the AI does not guess the answer. It converts your text into a mathematical vector, queries Neo4j for the most semantically relevant subgraph (Graph Retrieval), and uses that exact data to generate an evidence-based report.

---

## 3. How to Test the Project

To verify the integrity and capabilities of the system, we recommend the following testing methodology:

### Test Case A: Automated Pipeline Execution
**Objective:** Verify that the code can successfully orchestrate data ingestion and graph construction without manual intervention.
1. Start the Neo4j Desktop instance (`password: password`).
2. Start Ollama locally (`ollama serve`) and pull the model (`ollama pull gemma4:e2b`). No cloud API key is required.
3. Double-click `run_evaluator.bat`.
4. Press `Y` to build the database from scratch.
5. **Expected Result:** The console will display real-time progress as it inserts millions of nodes, embeds them, and initializes the Vector Store, concluding by automatically launching the Interactive CLI.

### Test Case B: Anti-Hallucination & Evidence Retrieval
**Objective:** Verify that the GraphRAG AI grounds its answers in the factual database rather than inventing information.
1. In the Interactive Analyst CLI, type: `Which devices are exhibiting Mirai botnet behavior, and what protocols are they using?`
2. **Expected Result:** The AI will query the database. Since the provided data sample might not contain Mirai flows, the AI must explicitly state that *no Mirai indicators were found in the current evidence*, proving it relies on the graph rather than hallucinating an attack.

### Test Case C: Cyber Threat Summarization
**Objective:** Verify the AI can analyze graph topology and summarize network behaviors.
1. In the Interactive Analyst CLI, type: `Summarize the most common attack types targeting port 80.`
2. **Expected Result:** The system will search Neo4j for flows targeting port 80, identify the `AttackType` nodes connected to those flows, and generate a structured intelligence report detailing those specific threats.

### Test Case D: Manual Graph Verification (Optional)
**Objective:** Visually confirm the data exists in Neo4j.
1. Open Neo4j Desktop and launch the Neo4j Browser.
2. Run the query: `MATCH (n) RETURN count(n)`
3. **Expected Result:** You will see a massive count of nodes, proving the data was successfully ingested by the Python scripts.
4. Run the query: `MATCH (a:AttackType) RETURN a.name LIMIT 10`
5. **Expected Result:** You will see specific malware and attack classifications extracted from the academic datasets.
