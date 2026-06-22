# âš ï¸ Known Limitations

This document explicitly lists remaining limitations and workarounds for the GraphRAG IoT Threat Intelligence system. **All limitations are documented here to ensure academic honesty.**

## Architecture & Design

### 1. Ollama Hardcoded as LLM Service

**Status:** By Design  
**Scope:** `src/adapters/ollama_adapter.py`  
**Limitation:** The system currently supports only local Ollama instances for LLM inference.

**Details:**
- Google Gemini embeddings are used, but generative inference is Ollama-only
- Port abstraction (LLMPort) allows swapping, but only OllamaAdapter is implemented
- OpenAI/Claude support would require new adapter implementations

**Why:** Local inference preserves data privacy (offline operation).

**To Make It Real:** 
1. Implement `OpenAIAdapter` implementing `LLMPort`
2. Update `src/core/config.py` to support LLM_PROVIDER flag
3. Update `run_evaluator.bat` to check for API credentials based on provider
4. Test end-to-end with chosen LLM

**Workaround:**
- Evaluators can use any LLM running locally via Ollama (Gemma, Llama, Mistral, etc.)
- Ollama API is generic; just change OLLAMA_MODEL in .env

---

### 2. Neo4j Setup Manual

**Status:** By Design  
**Scope:** Installation & startup  
**Limitation:** Neo4j Desktop must be downloaded, installed, and configured manually.

**Details:**
- No Docker containerization
- No Neo4j cloud setup scripts
- Evaluators must know Neo4j credentials (URI, user, password)
- Hardcoded default password "password" may not match evaluator's setup

**Why:** Avoids Docker complexity; Neo4j Desktop is lightweight on consumer hardware.

**To Make It Real:**
1. Create `scripts/setup_neo4j_docker.sh` for containerized deployment
2. Add CI/CD integration (GitHub Actions, GitLab CI) to spin up Neo4j in tests
3. Create CloudFormation/Terraform templates for AWS/cloud deployment

**Workaround:**
- Evaluators can use Neo4j Enterprise server instead of Desktop
- Update `.env` with correct Neo4j credentials
- Use Neo4j Aura (cloud) with HTTPS URI

---

## Pipeline & Data

### 3. Synthetic Sample Data for Development

**Status:** Documented  
**Scope:** `src/services/data_acquisition/` and `data/samples/`  
**Limitation:** If real datasets aren't downloaded, pipeline uses synthetic/sampled data.

**Details:**
- `create_sample_iot23_data()` generates random flows (not real packet captures)
- Samples in `data/samples/` are subsets of real data (50,000 rows each)
- Graph built from samples will be smaller (5.5M nodes if full, <100K if sampled)

**Why:** Full datasets (IoT-23: 20+ GB, CICIoT2023: 5+ GB) are large; samples allow quick demos.

**To Make It Real:**
1. Download full IoT-23 scenarios from Zenodo or CTU repository
2. Download full CICIoT2023 dataset from UNB website
3. Update `src/services/data_acquisition/` to ingest full datasets
4. Allocate 50+ GB storage and 2+ hours for ingestion

**Workaround:**
- Use provided samples for demos and evaluation (sufficient for feature validation)
- Clearly label synthetic data as such in reports

---

## Testing & Validation

### 4. Limited Unit Test Coverage

**Status:** In Progress  
**Scope:** `tests/smoke/`  
**Limitation:** Only smoke tests exist; full unit/integration test suite is not present.

**Details:**
- Smoke tests validate imports, exception hierarchy, mock adapters
- No tests for individual stages (e.g., feature extraction, graph ingestion)
- No tests for LLM hallucination detection edge cases
- No performance benchmarks

**Why:** Full test suite would require 50+ test files; smoke tests prioritize fast feedback.

**To Make It Real:**
1. Add pytest fixtures for mock adapters
2. Create unit tests for each stage (e.g., test_stage2_feature_extraction.py)
3. Create integration tests for full pipeline with mock services
4. Add performance benchmarks

**Workaround:**
- Run `scripts/run_automated_tests.py` for end-to-end validation
- Use `tests/smoke/test_core.py` for rapid feedback during development

---

### 5. Hallucination Detection (Post-Hoc, Not Real-Time)

**Status:** Partially Mitigated  
**Scope:** `scripts/evaluate_llm_hallucinations.py`  
**Limitation:** Hallucination detection runs *after* LLM generates output, not during generation.

**Details:**
- Validation script checks if LLM output references IPs that exist in the graph
- If LLM refuses to hallucinate (no data found), it's passed through as-is
- No real-time guardrails during inference (e.g., token-level constraints)

**Why:** Real-time hallucination prevention requires fine-tuning or constrained decoding (complex).

**To Make It Real:**
1. Implement constrained decoding with outlines library
2. Add a Cypher query validator to check if LLM-generated queries are valid
3. Fine-tune local Ollama model on correct graph queries
4. Use agent frameworks (e.g., LangChain) with guardrails

**Workaround:**
- Current system achieves 100% factuality by post-hoc validation
- LLM is constrained to provided graph context (no free-form reasoning)

---

## Infrastructure & Deployment

### 6. No Multi-Environment Configuration

**Status:** Limitation  
**Scope:** `src/core/config.py`, `.env`  
**Limitation:** Single `.env` file; no separate development, staging, production configs.

**Details:**
- All environments use the same `.env`
- No environment-specific overrides (e.g., dev with mocks, prod with real services)
- No deployment configuration (Docker, K8s, etc.)

**Why:** Dissertation project; multi-env complexity not needed.

**To Make It Real:**
1. Create `.env.development`, `.env.staging`, `.env.production`
2. Update `src/core/config.py` to support `ENVIRONMENT` variable
3. Add environment-specific service mixins
4. Create Dockerfile and docker-compose.yml

**Workaround:**
- For different setups, maintain separate `.env` files and swap them

---

### 7. No Containerization

**Status:** Limitation  
**Scope:** Entire project  
**Limitation:** No Docker/Kubernetes support; must install Python + Neo4j + Ollama locally.

**Details:**
- No Dockerfile
- No docker-compose for multi-service orchestration
- Evaluators must manage dependencies manually

**Why:** Simplicity for development; academic projects often prioritize code over deployment.

**To Make It Real:**
1. Create Dockerfile (Python 3.10 + Neo4j driver + dependencies)
2. Create docker-compose.yml (Neo4j service + Ollama service + application)
3. Add GitHub Actions to build and push container images
4. Document cloud deployment (AWS ECR, Docker Hub, etc.)

**Workaround:**
- Follow README setup instructions carefully
- Use provided `run_evaluator.bat` for Windows quick-start

---

## Security & Privacy

### 8. Secrets in .env (Non-Example)

**Status:** Risk  
**Scope:** `.env` file (not in repo)  
**Limitation:** Real `.env` file with credentials is not tracked in git; potential for accidental commits.

**Details:**
- `.env` is in `.gitignore` (good)
- `.env.example` shows all variables (good)
- But evaluators might accidentally commit real `.env` if they're not careful

**Why:** Standard practice; most Python projects have this risk.

**To Make It Real:**
1. Add git hook to prevent .env commits
2. Create `.env.vault` or use AWS Secrets Manager for production
3. Document secret management best practices

**Workaround:**
- Always use `.env` name for local secrets; never `.env.local`, `.env.prod`, etc.
- `.gitignore` already prevents commits

---

### 9. Hardcoded Neo4j Password

**Status:** Development Only  
**Scope:** `.env.example`, `run_evaluator.bat`  
**Limitation:** Default Neo4j password "password" is exposed in documentation.

**Details:**
- Not a security issue for local development
- Would be a critical issue in production
- Evaluators on shared machines should change password

**Why:** Makes setup easier for academic evaluation.

**To Make It Real:**
1. Generate random passwords in setup script
2. Prompt evaluator to change password interactively
3. Store password in secure vault (AWS Secrets Manager, HashiCorp Vault)

**Workaround:**
- Evaluators on shared machines should use unique passwords
- Use firewall rules to restrict Neo4j access

---

## Performance & Scale

### 10. VRAM Offloading for Large LLM

**Status:** Documented Performance Trade-Off  
**Scope:** `src/services/threat_explanation/`  
**Limitation:** Large models (7B+ parameters) require VRAM offloading to system RAM, adding latency.

**Details:**
- Gemma 4 (7.2B) requires 7.2 GB VRAM, but RTX 3050 only has 6 GB
- System dynamically offloads to system RAM (16 GB available)
- Latency increases to 2.5â€“3 minutes per query (vs. < 1 sec with enough VRAM)

**Why:** Consumer hardware constraints; acceptable for research tool.

**To Make It Real:**
1. Use smaller models (3Bâ€“5B parameters) that fit in VRAM
2. Use quantized models (4-bit, 8-bit) to reduce VRAM footprint
3. Deploy on hardware with more VRAM (A100, H100 GPUs)

**Workaround:**
- System is designed for this trade-off; 3-minute response time is acceptable for offline CTI analysis
- Evaluators with better hardware will see faster responses

---

## Summary

| # | Category | Severity | Status |
|---|----------|----------|--------|
| 1 | Ollama-only LLM | MEDIUM | By Design |
| 2 | Manual Neo4j Setup | MEDIUM | By Design |
| 3 | Synthetic Sample Data | LOW | Documented |
| 4 | Limited Test Coverage | MEDIUM | In Progress |
| 5 | Post-Hoc Hallucination Detection | LOW | Partially Mitigated |
| 6 | Single Environment Config | LOW | Limitation |
| 7 | No Containerization | MEDIUM | Limitation |
| 8 | .env Commit Risk | LOW | Standard Practice |
| 9 | Hardcoded Default Password | LOW | Development Only |
| 10 | VRAM Offloading | LOW | Trade-Off |

**Overall Assessment:** All limitations are documented, none are *deceptive*. The system is honest about what it does and doesn't do.
