# GraphRAG IoT Threat Intelligence — Roadmap

This roadmap outlines the path from a portfolio demonstration to a production-ready enterprise security tool.

## Bucket: Immediate (High impact, low effort)
1. **One-Click Demo Mode (`run_demo.bat`)**
   - *Why:* Evaluators and recruiters need a frictionless way to experience the pipeline without setting up datasets.
   - *Status:* **IMPLEMENTED**. Added a batch script that sets up the environment and runs the pipeline with sample data.
2. **Colorized CLI Output (`colorama`)**
   - *Why:* Visual polish is critical for screenshots and screencasts in a portfolio.
   - *Status:* **IMPLEMENTED**. Upgraded `src/cli/main.py` with `colorama` for a professional, hacker-themed terminal UI.
3. **Automated Demo Query (`--auto-demo`)**
   - *Why:* Auto-typing a complex query like "Which devices are exhibiting Mirai botnet behavior" immediately demonstrates the value proposition.
   - *Status:* **IMPLEMENTED**. Passed via `scripts/run_pipeline.py --auto-demo` into the CLI.

## Bucket: Short-term (Medium effort, high value)
- **Conversation History Memory**
  - *Goal:* Allow analysts to ask follow-up questions without repeating context.
  - *Stub integration:* Update `OllamaClient.generate()` to maintain a rolling buffer of previous prompts and responses.
- **REST API Port**
  - *Goal:* Decouple from the CLI to support a web dashboard.
  - *Stub integration:* Add `src/ports/api_port.py` using FastAPI to expose `ThreatExplainer` endpoints.

## Bucket: Medium-term (High effort, strategic value)
- **Real-time Stream Ingestion**
  - *Goal:* Ingest pcap streams or Zeek logs live rather than batch loading CSVs.
  - *Stub integration:* Create `src/services/data_acquisition/kafka_consumer.py`.
- **Local Model Embeddings**
  - *Goal:* Remove the Google API key requirement and run embeddings locally via HuggingFace for full air-gapped security.
  - *Stub integration:* Replace the `get_gemini_embeddings` API call in `src/services/graph_embeddings/embeddings.py` with a local HuggingFace embedding model.

## Bucket: Long-term (Visionary)
- **Multi-Agent Swarm**
  - *Goal:* Deploy specialized autonomous agents (e.g., Malware Analyst, Network Specialist) that converse with each other to generate the incident report.
- **Automated Remediation Hooks**
  - *Goal:* Trigger firewall rules directly from Neo4j triggers when a malicious pattern is embedded.
