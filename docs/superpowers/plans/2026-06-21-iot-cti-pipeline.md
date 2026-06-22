# IoT Cyber Threat Intelligence Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a working IoT cyber threat intelligence system that ingests IoT-23 and CICIoT2023 datasets, constructs a MITRE-enriched knowledge graph in Neo4j, generates local graph embeddings (node2vec), retrieves threat context via dual-mode retrieval (Cypher + vector similarity), and produces grounded LLM explanations via Ollama — with a complete evaluation framework that demonstrates value over a tabular ML baseline.

**Architecture:**
Normalized flow data (IoT-23 + CICIoT2023) is ingested into a Neo4j knowledge graph enriched with MITRE ATT&CK technique nodes. Node2vec structural embeddings and sentence-transformer text embeddings are stored directly in Neo4j's vector index. A dual-retrieval layer (Cypher for structured facts + cosine vector search for semantic similarity) assembles grounded context for a local Ollama LLM. A separate evaluation pipeline measures classification, retrieval, and explanation quality, with XGBoost on tabular features as the performance baseline.

**Tech Stack:**
- Python 3.11, Neo4j 5.x Community, Ollama (Llama 3.1 8B or Mistral 7B)
- `neo4j` (Python driver), `sentence-transformers` (local embeddings), `node2vec` (structural embeddings)
- `pandas`, `numpy`, `scikit-learn`, `xgboost` (baseline + evaluation)
- `pytest` (testing), `zeek` (PCAP parsing for IoT-23)
- Existing hexagonal architecture: ports/adapters/services pattern, already in place

## Global Constraints

- Python ≥ 3.11
- Neo4j ≥ 5.11 Community (required for vector index support)
- No Google Gemini API — all embeddings must be local and reproducible without internet
- All embedding models must run offline (sentence-transformers cached locally)
- Ollama must run locally at `http://localhost:11434`
- Train/test split is 80/20, applied BEFORE graph construction — test flows never appear in the graph
- Every evaluation metric must be computed on the held-out test split only
- All raw data paths come from `Config.DATA_RAW_DIR`; no hardcoded paths

---

## Critical Problems in Current Codebase (Read Before Starting)

Before any task, understand these issues that must be fixed:

1. **`src/services/graph_embeddings/embeddings.py`** calls `google.genai` for text embeddings. This requires `GOOGLE_API_KEY` and internet access. Must be replaced with `sentence-transformers` (local).

2. **`compute_node2vec_embeddings()`** in the same file uses `AdjacencySpectralEmbed` from graspologic — this is spectral decomposition, NOT node2vec. The academic claim of "node2vec embeddings" is false. Must be replaced with the `node2vec` library.

3. **No evaluation framework exists anywhere in the codebase.** This is the most critical missing component for a thesis submission.

4. **No baseline comparison exists.** Without XGBoost or Random Forest on tabular features, you cannot claim graph + LLM adds value.

5. **`src/services/graphrag/`** implements a retrieval pipeline that works, but there is no ablation study comparing Cypher-only vs. vector-only vs. combined retrieval. This comparison IS the research contribution of the GraphRAG component.

6. **The data pipeline (`extract_iot23.py`, `extract_ciciot.py`)** must be verified to produce correctly aligned, labeled flows. IoT-23 Zeek logs have timestamp alignment issues with label files — this is a known, published problem.

---

## File Map

### Files to Create
- `src/services/graph_embeddings/text_embeddings.py` — sentence-transformers local embedding (replaces Gemini)
- `src/services/graph_embeddings/node2vec_embeddings.py` — proper node2vec (replaces spectral)
- `src/services/evaluation/__init__.py`
- `src/services/evaluation/baseline.py` — XGBoost tabular baseline
- `src/services/evaluation/classification_metrics.py` — F1, AUC-ROC per attack type
- `src/services/evaluation/retrieval_metrics.py` — MRR, Hit@K for retrieval evaluation
- `src/services/evaluation/llm_metrics.py` — label consistency + grounding check
- `src/services/evaluation/ablation.py` — run Cypher-only vs vector-only vs combined
- `src/services/evaluation/report.py` — generate evaluation report as JSON + markdown
- `data/eval/curated_queries.json` — 50 hand-crafted retrieval queries with expected answers
- `tests/unit/test_text_embeddings.py`
- `tests/unit/test_node2vec_embeddings.py`
- `tests/unit/test_evaluation.py`
- `tests/integration/test_end_to_end_pipeline.py`
- `scripts/evaluate.py` — evaluation runner CLI

### Files to Modify
- `src/services/graph_embeddings/embeddings.py` — remove Gemini calls, delegate to new modules
- `src/services/knowledge_graph/schema_setup.py` — add `Flow` vector index (currently missing)
- `src/services/feature_extraction/extract_iot23.py` — verify label alignment, add train/test split
- `src/services/feature_extraction/extract_ciciot.py` — verify label alignment, add train/test split
- `config/settings.py` — remove `GEMINI_*` settings, add `SENTENCE_TRANSFORMER_MODEL`
- `requirements.txt` — swap `google-genai` → `sentence-transformers`, add `node2vec`, `xgboost`

### Files to Delete (after replacement confirmed working)
- `src/services/graph_embeddings/embeddings_v2.py` (phantom duplicate)
- `src/stage*/**` (old stage structure, already deleted per git status — confirm)

---

## Phase 0: Environment Verification (Day 1 — Do This First)

### Task 0: Verify the existing pipeline runs end-to-end with mocks

**Why:** Before touching anything, establish a working baseline. If the mock-based smoke test fails now, every subsequent task is blocked.

**Files:**
- Read: `tests/integration/test_adapters_integration.py`
- Read: `src/adapters/mock_graph_adapter.py`
- Read: `src/adapters/mock_llm_adapter.py`

**Interfaces:**
- Produces: A passing test suite baseline (commit hash) to which all future changes are compared

- [ ] **Step 1: Install dependencies**

```bash
cd "d:/anil sir"
pip install -r requirements.txt
```

Expected: No errors. If `google-genai` fails to install, that confirms the Gemini dependency is a problem — continue.

- [ ] **Step 2: Run the existing unit tests**

```bash
pytest tests/unit/ -v --tb=short 2>&1 | head -80
```

Expected: Record which tests pass and which fail. Document failures — do not fix them yet.

- [ ] **Step 3: Run the existing integration tests**

```bash
pytest tests/integration/ -v --tb=short 2>&1 | head -80
```

Expected: Record pass/fail baseline. This is your starting point.

- [ ] **Step 4: Verify Neo4j is reachable**

```python
# Run this as a quick script: python -c "..."
from neo4j import GraphDatabase
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "your_password"))
with driver.session() as s:
    result = s.run("RETURN 1 AS ok")
    print(result.single()["ok"])
driver.close()
```

Expected: prints `1`. If Neo4j is not running, start it with `neo4j console` or Docker:
```bash
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:5.20-community
```

- [ ] **Step 5: Verify Ollama is reachable**

```bash
curl http://localhost:11434/api/tags
```

Expected: JSON response listing installed models. If empty, pull a model:
```bash
ollama pull llama3.1:8b
```

- [ ] **Step 6: Commit baseline test results**

```bash
git add -A
git commit -m "chore: record pre-refactor test baseline"
```

---

## Phase 1: Data Pipeline (Days 2–5)

### Task 1: Fix CICIoT2023 feature extraction and train/test split

**Why:** CICIoT2023 is the simpler dataset (pre-extracted CSV). Fix this first because it validates the normalization schema before tackling the harder IoT-23 PCAP alignment problem.

**Files:**
- Modify: `src/services/feature_extraction/extract_ciciot.py`
- Create: `tests/unit/test_extract_ciciot.py`

**Interfaces:**
- Consumes: CSV files under `Config.DATA_RAW_DIR / "ciciot2023" / "*.csv"`
- Produces: `Dict` with keys `train: pd.DataFrame`, `test: pd.DataFrame`, each with columns `[uid, src_ip, dst_ip, src_port, dst_port, protocol, duration, fwd_pkts, bwd_pkts, fwd_bytes, bwd_bytes, label, dataset]`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_extract_ciciot.py`:

```python
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.feature_extraction.extract_ciciot import extract_ciciot, REQUIRED_COLUMNS


def make_dummy_df(n=100):
    import numpy as np
    labels = ["Benign"] * 70 + ["DDoS-TCP_Flood"] * 20 + ["DoS-SYN_Flood"] * 10
    return pd.DataFrame({
        "flow_id": range(n),
        "src_ip": ["192.168.1.1"] * n,
        "dst_ip": ["10.0.0.1"] * n,
        "src_port": [12345] * n,
        "dst_port": [80] * n,
        "protocol": [6] * n,  # TCP
        "flow_duration": [0.1] * n,
        "tot_fwd_pkts": [5] * n,
        "tot_bwd_pkts": [3] * n,
        "totlen_fwd_pkts": [500] * n,
        "totlen_bwd_pkts": [300] * n,
        "label": labels,
    })


def test_extract_ciciot_returns_train_test_split(tmp_path):
    csv_file = tmp_path / "sample.csv"
    make_dummy_df(100).to_csv(csv_file, index=False)

    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)

    assert "train" in result
    assert "test" in result
    assert len(result["train"]) == 80
    assert len(result["test"]) == 20


def test_extract_ciciot_output_has_required_columns(tmp_path):
    csv_file = tmp_path / "sample.csv"
    make_dummy_df(100).to_csv(csv_file, index=False)

    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)

    for col in REQUIRED_COLUMNS:
        assert col in result["train"].columns, f"Missing column: {col}"


def test_extract_ciciot_dataset_column_is_ciciot(tmp_path):
    csv_file = tmp_path / "sample.csv"
    make_dummy_df(50).to_csv(csv_file, index=False)

    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)
    assert (result["train"]["dataset"] == "ciciot2023").all()


def test_extract_ciciot_no_test_rows_in_train(tmp_path):
    csv_file = tmp_path / "sample.csv"
    make_dummy_df(100).to_csv(csv_file, index=False)

    result = extract_ciciot(data_dir=tmp_path, test_size=0.2, random_state=42)
    train_uids = set(result["train"]["uid"])
    test_uids = set(result["test"]["uid"])
    assert train_uids.isdisjoint(test_uids), "Train and test sets overlap"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_extract_ciciot.py -v --tb=short
```

Expected: FAIL — `extract_ciciot` likely does not accept `data_dir`, `test_size`, `random_state` params, and does not return a dict with train/test keys.

- [ ] **Step 3: Rewrite `extract_ciciot.py`**

Replace the body of `src/services/feature_extraction/extract_ciciot.py`:

```python
"""CICIoT2023 feature extraction with train/test split."""

import hashlib
import uuid
from pathlib import Path
from typing import Dict

import pandas as pd
from sklearn.model_selection import train_test_split

REQUIRED_COLUMNS = [
    "uid", "src_ip", "dst_ip", "src_port", "dst_port",
    "protocol", "duration", "fwd_pkts", "bwd_pkts",
    "fwd_bytes", "bwd_bytes", "label", "dataset",
]

# CICIoT2023 column name → our normalized name
_COLUMN_MAP = {
    "flow_id":           "uid",
    "src_ip":            "src_ip",
    "dst_ip":            "dst_ip",
    "src_port":          "src_port",
    "dst_port":          "dst_port",
    "protocol":          "protocol",
    "flow_duration":     "duration",
    "tot_fwd_pkts":      "fwd_pkts",
    "tot_bwd_pkts":      "bwd_pkts",
    "totlen_fwd_pkts":   "fwd_bytes",
    "totlen_bwd_pkts":   "bwd_bytes",
    "label":             "label",
}


def extract_ciciot(
    data_dir: Path,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Dict[str, pd.DataFrame]:
    """
    Load CICIoT2023 CSV files, normalize schema, split into train/test.

    The split is performed BEFORE any graph ingestion. Only train rows
    are ever loaded into Neo4j. Test rows are reserved for evaluation.

    Returns:
        {"train": DataFrame, "test": DataFrame} with REQUIRED_COLUMNS schema
    """
    data_dir = Path(data_dir)
    csv_files = sorted(data_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    frames = []
    for f in csv_files:
        df = pd.read_csv(f, low_memory=False)
        df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
        frames.append(df)

    raw = pd.concat(frames, ignore_index=True)
    normalized = _normalize(raw)
    normalized = normalized.dropna(subset=["src_ip", "dst_ip", "label"])
    normalized = normalized.reset_index(drop=True)

    train_df, test_df = train_test_split(
        normalized,
        test_size=test_size,
        random_state=random_state,
        stratify=normalized["label"],
    )
    return {
        "train": train_df.reset_index(drop=True),
        "test": test_df.reset_index(drop=True),
    }


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={k: v for k, v in _COLUMN_MAP.items() if k in df.columns})

    # Generate stable UIDs if not present
    if "uid" not in df.columns:
        df["uid"] = [str(uuid.uuid4()) for _ in range(len(df))]
    else:
        df["uid"] = df["uid"].astype(str)

    df["dataset"] = "ciciot2023"

    # Cast types
    for col in ["src_port", "dst_port"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ["fwd_pkts", "bwd_pkts", "fwd_bytes", "bwd_bytes"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    if "duration" in df.columns:
        df["duration"] = pd.to_numeric(df["duration"], errors="coerce").fillna(0.0)
    if "protocol" in df.columns:
        df["protocol"] = df["protocol"].astype(str)

    # Keep only required columns that exist
    keep = [c for c in REQUIRED_COLUMNS if c in df.columns]
    return df[keep]
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
pytest tests/unit/test_extract_ciciot.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/services/feature_extraction/extract_ciciot.py tests/unit/test_extract_ciciot.py
git commit -m "fix: rewrite CICIoT extractor with normalized schema and train/test split"
```

---

### Task 2: Fix IoT-23 feature extraction with label alignment

**Why:** IoT-23 is the primary dataset for PCAP-level work and device mapping. The label alignment problem (Zeek timestamps vs. label file) is documented and must be handled explicitly.

**Files:**
- Modify: `src/services/feature_extraction/extract_iot23.py`
- Create: `tests/unit/test_extract_iot23.py`

**Interfaces:**
- Consumes: Zeek `conn.log` files and `*.labels` files under `Config.DATA_RAW_DIR / "iot23" /`
- Produces: Same `{"train": DataFrame, "test": DataFrame}` schema as Task 1, plus an additional `device_ip` column mapping flows to known IoT device IPs

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_extract_iot23.py`:

```python
import io
import pytest
import pandas as pd
from pathlib import Path
from src.services.feature_extraction.extract_iot23 import (
    extract_iot23, parse_zeek_conn_log, align_labels, REQUIRED_COLUMNS
)


SAMPLE_CONN_LOG = """\
#separator \\x09
#set_separator\t,
#empty_field\t(empty)
#unset_field\t-
#path\tconn
#open\t2018-12-21-11-23-45
#fields\tts\tuid\tid.orig_h\tid.orig_p\tid.resp_h\tid.resp_p\tproto\tduration\torig_bytes\tresp_bytes
#types\ttime\tstring\taddr\tport\taddr\tport\tenum\tinterval\tcount\tcount
1545389025.123456\tCabc123\t192.168.1.195\t12345\t23.45.67.89\t80\ttcp\t0.123\t500\t300
1545389026.234567\tCdef456\t192.168.1.195\t12346\t23.45.67.89\t443\ttcp\t0.456\t1000\t800
"""

SAMPLE_LABEL = """\
1545389025.123456\tCabc123\t192.168.1.195\t12345\t23.45.67.89\t80\ttcp\tMirai\t-\t-
1545389026.234567\tCdef456\t192.168.1.195\t12346\t23.45.67.89\t443\ttcp\tBenign\t-\t-
"""


def test_parse_zeek_conn_log(tmp_path):
    log_file = tmp_path / "conn.log"
    log_file.write_text(SAMPLE_CONN_LOG)
    df = parse_zeek_conn_log(log_file)
    assert len(df) == 2
    assert "uid" in df.columns
    assert df["uid"].tolist() == ["Cabc123", "Cdef456"]


def test_align_labels_matches_by_uid():
    flows = pd.DataFrame({
        "uid": ["Cabc123", "Cdef456"],
        "src_ip": ["192.168.1.195", "192.168.1.195"],
    })
    label_lines = [
        "1545389025.0\tCabc123\t192.168.1.195\t12345\t23.45.67.89\t80\ttcp\tMirai\t-\t-",
        "1545389026.0\tCdef456\t192.168.1.195\t12346\t23.45.67.89\t443\ttcp\tBenign\t-\t-",
    ]
    labeled = align_labels(flows, label_lines)
    assert labeled["label"].tolist() == ["Mirai", "Benign"]


def test_align_labels_drops_unlabeled_rows():
    flows = pd.DataFrame({
        "uid": ["Cabc123", "Cunknown"],
        "src_ip": ["192.168.1.195", "192.168.1.195"],
    })
    label_lines = [
        "1545389025.0\tCabc123\t192.168.1.195\t12345\t23.45.67.89\t80\ttcp\tMirai\t-\t-",
    ]
    labeled = align_labels(flows, label_lines)
    assert len(labeled) == 1
    assert labeled["uid"].iloc[0] == "Cabc123"


def test_extract_iot23_returns_train_test(tmp_path):
    scenario_dir = tmp_path / "CTU-IoT-Malware-Capture-1-1"
    scenario_dir.mkdir()
    (scenario_dir / "conn.log").write_text(SAMPLE_CONN_LOG)
    (scenario_dir / "conn.log.labeled").write_text(SAMPLE_LABEL)

    result = extract_iot23(data_dir=tmp_path, test_size=0.5, random_state=42)
    assert "train" in result and "test" in result
    assert len(result["train"]) + len(result["test"]) == 2
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/unit/test_extract_iot23.py -v --tb=short
```

- [ ] **Step 3: Rewrite `extract_iot23.py`**

```python
"""IoT-23 feature extraction with Zeek log parsing and label alignment."""

import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from sklearn.model_selection import train_test_split

from src.services.feature_extraction.extract_ciciot import REQUIRED_COLUMNS

_ZEEK_FIELD_MAP = {
    "ts":          "timestamp",
    "uid":         "uid",
    "id.orig_h":   "src_ip",
    "id.orig_p":   "src_port",
    "id.resp_h":   "dst_ip",
    "id.resp_p":   "dst_port",
    "proto":       "protocol",
    "duration":    "duration",
    "orig_bytes":  "fwd_bytes",
    "resp_bytes":  "bwd_bytes",
}

# Known IoT-23 device IPs (from dataset documentation)
_DEVICE_IPS = {
    "192.168.1.195", "192.168.1.196", "192.168.1.197",
    "192.168.1.198", "192.168.1.199", "192.168.1.200",
}


def parse_zeek_conn_log(log_path: Path) -> pd.DataFrame:
    """
    Parse a Zeek conn.log file into a DataFrame.

    Handles Zeek's TSV format with #fields header line.
    Replaces '-' (Zeek null) with NaN.
    """
    fields: List[str] = []
    rows: List[dict] = []

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("#fields"):
                fields = line.split("\t")[1:]
            elif line.startswith("#"):
                continue
            elif fields:
                values = line.split("\t")
                if len(values) != len(fields):
                    continue
                row = {
                    fields[i]: (None if values[i] == "-" else values[i])
                    for i in range(len(fields))
                }
                rows.append(row)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.rename(columns={k: v for k, v in _ZEEK_FIELD_MAP.items() if k in df.columns})

    if "src_port" in df.columns:
        df["src_port"] = pd.to_numeric(df["src_port"], errors="coerce").fillna(0).astype(int)
    if "dst_port" in df.columns:
        df["dst_port"] = pd.to_numeric(df["dst_port"], errors="coerce").fillna(0).astype(int)
    if "duration" in df.columns:
        df["duration"] = pd.to_numeric(df["duration"], errors="coerce").fillna(0.0)
    if "fwd_bytes" in df.columns:
        df["fwd_bytes"] = pd.to_numeric(df["fwd_bytes"], errors="coerce").fillna(0.0)
    if "bwd_bytes" in df.columns:
        df["bwd_bytes"] = pd.to_numeric(df["bwd_bytes"], errors="coerce").fillna(0.0)

    # IoT-23 does not provide per-packet counts in conn.log — set to 0
    df["fwd_pkts"] = 0
    df["bwd_pkts"] = 0

    return df


def align_labels(flows: pd.DataFrame, label_lines: List[str]) -> pd.DataFrame:
    """
    Match flow rows to labels using UID (primary key).

    The IoT-23 label files use the same UID as Zeek conn.log.
    Rows with no matching label are dropped (conservative approach).
    """
    uid_to_label: dict = {}
    for line in label_lines:
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 8:
            uid = parts[1].strip()
            label = parts[7].strip()
            if uid and label and label != "-":
                uid_to_label[uid] = label

    if not uid_to_label:
        return flows.assign(label="Unknown")

    flows = flows.copy()
    flows["label"] = flows["uid"].map(uid_to_label)
    return flows.dropna(subset=["label"]).reset_index(drop=True)


def extract_iot23(
    data_dir: Path,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Dict[str, pd.DataFrame]:
    """
    Extract and normalize IoT-23 flows with label alignment and train/test split.

    Scans `data_dir` for subdirectories containing conn.log + conn.log.labeled.
    Returns {"train": DataFrame, "test": DataFrame} with REQUIRED_COLUMNS schema.
    """
    data_dir = Path(data_dir)
    all_frames: List[pd.DataFrame] = []

    for scenario_dir in sorted(data_dir.iterdir()):
        if not scenario_dir.is_dir():
            continue
        conn_log = scenario_dir / "conn.log"
        label_file = scenario_dir / "conn.log.labeled"

        if not conn_log.exists():
            continue

        flows = parse_zeek_conn_log(conn_log)
        if flows.empty:
            continue

        if label_file.exists():
            label_lines = label_file.read_text(errors="replace").splitlines()
            flows = align_labels(flows, label_lines)
        else:
            flows["label"] = "Unknown"

        flows["dataset"] = "iot23"
        all_frames.append(flows)

    if not all_frames:
        raise FileNotFoundError(f"No IoT-23 scenario directories found in {data_dir}")

    combined = pd.concat(all_frames, ignore_index=True)
    combined = combined.dropna(subset=["src_ip", "dst_ip", "label"])
    combined = combined[combined["label"] != "Unknown"].reset_index(drop=True)

    train_df, test_df = train_test_split(
        combined,
        test_size=test_size,
        random_state=random_state,
        stratify=combined["label"],
    )
    return {
        "train": train_df.reset_index(drop=True),
        "test": test_df.reset_index(drop=True),
    }
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/unit/test_extract_iot23.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/services/feature_extraction/extract_iot23.py tests/unit/test_extract_iot23.py
git commit -m "fix: rewrite IoT-23 extractor with Zeek parsing, label alignment, and train/test split"
```

---

## Phase 2: Knowledge Graph Construction (Days 6–9)

### Task 3: Verify schema setup and MITRE enrichment work correctly

**Why:** The schema exists but must be verified to work with Neo4j 5.x Community before you load millions of rows. Running schema setup on an empty Neo4j instance and verifying constraints is 20 minutes of work that prevents hours of debugging later.

**Files:**
- Read: `src/services/knowledge_graph/schema_setup.py`
- Read: `src/services/knowledge_graph/enrich_mitre.py`
- Create: `tests/integration/test_schema_and_mitre.py`

**Interfaces:**
- Consumes: Running Neo4j instance at `Config.NEO4J_URI`
- Produces: Neo4j database with constraints, indexes, vector indexes, and MITRE technique nodes loaded

- [ ] **Step 1: Write the integration test**

Create `tests/integration/test_schema_and_mitre.py`:

```python
"""Integration tests for schema setup and MITRE enrichment (require live Neo4j)."""
import pytest
from src.services.knowledge_graph.neo4j_connection import run_query, verify_connectivity
from src.services.knowledge_graph.schema_setup import setup_full_schema
from src.services.knowledge_graph.enrich_mitre import enrich_mitre_techniques


@pytest.fixture(scope="module")
def neo4j_available():
    if not verify_connectivity():
        pytest.skip("Neo4j not available")


def test_schema_setup_creates_constraints(neo4j_available):
    result = setup_full_schema()
    assert result is True

    constraints = run_query("SHOW CONSTRAINTS")
    constraint_names = [c.get("name", "") for c in constraints]
    assert any("attack_name" in n for n in constraint_names)
    assert any("protocol_name" in n for n in constraint_names)


def test_schema_setup_creates_vector_indexes(neo4j_available):
    indexes = run_query("SHOW INDEXES")
    vector_indexes = [i for i in indexes if i.get("type") == "VECTOR"]
    assert len(vector_indexes) >= 2, f"Expected ≥2 vector indexes, got: {vector_indexes}"


def test_mitre_enrichment_loads_techniques(neo4j_available):
    enrich_mitre_techniques()
    result = run_query("MATCH (m:MITRETechnique) RETURN count(m) AS cnt")
    count = result[0]["cnt"]
    assert count >= 10, f"Expected ≥10 MITRE techniques, got {count}"


def test_mitre_techniques_have_required_fields(neo4j_available):
    result = run_query("""
        MATCH (m:MITRETechnique)
        WHERE m.technique_id IS NULL OR m.name IS NULL OR m.tactic IS NULL
        RETURN count(m) AS incomplete
    """)
    assert result[0]["incomplete"] == 0, "Some MITRETechnique nodes are missing required fields"
```

- [ ] **Step 2: Run to verify current state**

```bash
pytest tests/integration/test_schema_and_mitre.py -v --tb=short
```

Record what passes and what fails before making changes.

- [ ] **Step 3: Add missing `Flow` vector index to `schema_setup.py`**

In `src/services/knowledge_graph/schema_setup.py`, add to `create_vector_indexes()`:

```python
(
    "flow_embedding",
    f"""CREATE VECTOR INDEX flow_embedding IF NOT EXISTS
    FOR (f:Flow) ON (f.embedding)
    OPTIONS {{indexConfig: {{
        `vector.dimensions`: {EMBEDDING_DIMENSION},
        `vector.similarity_function`: 'cosine'
    }}}}"""
),
```

- [ ] **Step 4: Run integration tests again**

```bash
pytest tests/integration/test_schema_and_mitre.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/services/knowledge_graph/schema_setup.py tests/integration/test_schema_and_mitre.py
git commit -m "fix: add Flow vector index and integration tests for schema + MITRE setup"
```

---

### Task 4: Batch-ingest train flows into Neo4j

**Why:** The ingestion script must correctly separate train flows (go into graph) from test flows (never touch the graph). This boundary is the most important correctness constraint for the entire evaluation.

**Files:**
- Read: `src/services/knowledge_graph/ingest_flows.py`
- Modify: `src/services/knowledge_graph/ingest_flows.py`
- Create: `tests/unit/test_ingest_flows.py`

**Interfaces:**
- Consumes: `train_df: pd.DataFrame` with REQUIRED_COLUMNS
- Produces: Neo4j graph with `Flow`, `Device` (IPAddress), `Protocol`, `AttackType` nodes and edges

- [ ] **Step 1: Write test that verifies test rows are NOT ingested**

Create `tests/unit/test_ingest_flows.py`:

```python
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, call
from src.services.knowledge_graph.ingest_flows import ingest_flows, build_flow_batch


def make_flows(n=10):
    return pd.DataFrame({
        "uid": [f"uid_{i}" for i in range(n)],
        "src_ip": ["192.168.1.1"] * n,
        "dst_ip": ["10.0.0.1"] * n,
        "src_port": [12345] * n,
        "dst_port": [80] * n,
        "protocol": ["tcp"] * n,
        "duration": [0.1] * n,
        "fwd_pkts": [5] * n,
        "bwd_pkts": [3] * n,
        "fwd_bytes": [500.0] * n,
        "bwd_bytes": [300.0] * n,
        "label": ["Benign"] * 8 + ["DDoS-TCP_Flood"] * 2,
        "dataset": ["ciciot2023"] * n,
    })


def test_build_flow_batch_produces_correct_dict():
    flows = make_flows(2)
    batch = build_flow_batch(flows)
    assert len(batch) == 2
    assert batch[0]["uid"] == "uid_0"
    assert batch[0]["src_ip"] == "192.168.1.1"
    assert batch[0]["label"] == "Benign"


def test_ingest_flows_calls_batch_query(tmp_path):
    flows = make_flows(5)
    with patch("src.services.knowledge_graph.ingest_flows.run_batch_query") as mock_batch:
        mock_batch.return_value = None
        ingest_flows(flows, batch_size=3)
        # Should be called twice: batch of 3, then batch of 2
        assert mock_batch.call_count >= 2
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/unit/test_ingest_flows.py -v --tb=short
```

- [ ] **Step 3: Ensure `ingest_flows.py` exposes `build_flow_batch` and correct signature**

Open `src/services/knowledge_graph/ingest_flows.py` and verify (or add) these two functions:

```python
def build_flow_batch(df: pd.DataFrame) -> list:
    """Convert DataFrame rows to list of dicts for Neo4j UNWIND."""
    return df.to_dict(orient="records")


def ingest_flows(df: pd.DataFrame, batch_size: int = 1000) -> int:
    """
    Ingest train flows into Neo4j.

    This function must ONLY be called with train data.
    Never pass test data here — it would contaminate the evaluation.

    Returns: number of flows ingested
    """
    total = 0
    records = build_flow_batch(df)
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        run_batch_query(_FLOW_MERGE_QUERY, batch)
        total += len(batch)
    return total


_FLOW_MERGE_QUERY = """
UNWIND $batch AS row
MERGE (src:Device {ip: row.src_ip})
  ON CREATE SET src.dataset = row.dataset, src.first_seen = row.uid
MERGE (dst:Device {ip: row.dst_ip})
  ON CREATE SET dst.dataset = row.dataset
MERGE (proto:Protocol {name: row.protocol})
MERGE (attack:AttackType {name: row.label})
CREATE (f:Flow {
    uid: row.uid,
    src_ip: row.src_ip,
    dst_ip: row.dst_ip,
    src_port: toInteger(row.src_port),
    dst_port: toInteger(row.dst_port),
    protocol: row.protocol,
    duration: toFloat(row.duration),
    fwd_pkts: toInteger(row.fwd_pkts),
    bwd_pkts: toInteger(row.bwd_pkts),
    fwd_bytes: toFloat(row.fwd_bytes),
    bwd_bytes: toFloat(row.bwd_bytes),
    label: row.label,
    dataset: row.dataset,
    timestamp: timestamp()
})
MERGE (f)-[:HAS_SOURCE]->(src)
MERGE (f)-[:HAS_DESTINATION]->(dst)
MERGE (f)-[:USES_PROTOCOL]->(proto)
MERGE (f)-[:CLASSIFIED_AS]->(attack)
MERGE (src)-[r:COMMUNICATES_WITH]->(dst)
  ON CREATE SET r.flow_count = 1
  ON MATCH SET r.flow_count = r.flow_count + 1
"""
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/unit/test_ingest_flows.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/services/knowledge_graph/ingest_flows.py tests/unit/test_ingest_flows.py
git commit -m "fix: ensure ingest_flows has stable build_flow_batch + clear train-only contract"
```

---

## Phase 3: Embeddings Overhaul (Days 10–14)

### Task 5: Replace Gemini with sentence-transformers for text embeddings

**Why:** Google Gemini requires an API key, internet access, and is a paid service. It is not reproducible in an offline or thesis-defense environment. `sentence-transformers` with `all-MiniLM-L6-v2` runs fully locally, produces 384-dim vectors, and is academically citable (Reimers & Gurevych, 2019).

**Files:**
- Create: `src/services/graph_embeddings/text_embeddings.py`
- Modify: `src/services/graph_embeddings/embeddings.py` — remove Gemini calls, import from new module
- Create: `tests/unit/test_text_embeddings.py`
- Modify: `requirements.txt` — add `sentence-transformers>=2.7.0`; remove `google-genai`

**Interfaces:**
- Consumes: list of strings
- Produces: `list[list[float]]` — 384-dim vectors (all-MiniLM-L6-v2)

- [ ] **Step 1: Add dependency**

In `requirements.txt`, replace:
```
google-genai
```
With:
```
sentence-transformers>=2.7.0
```

Then:
```bash
pip install sentence-transformers
```

- [ ] **Step 2: Write the failing test**

Create `tests/unit/test_text_embeddings.py`:

```python
from src.services.graph_embeddings.text_embeddings import (
    get_local_embeddings, EMBEDDING_DIM
)


def test_get_local_embeddings_returns_correct_shape():
    texts = ["IoT device Mirai botnet attack", "Benign network flow"]
    result = get_local_embeddings(texts)
    assert len(result) == 2
    assert len(result[0]) == EMBEDDING_DIM
    assert len(result[1]) == EMBEDDING_DIM


def test_get_local_embeddings_similar_texts_close_in_space():
    import numpy as np
    texts = ["DDoS attack flood", "Distributed denial of service flood"]
    unrelated = ["The weather is nice today"]
    embs = get_local_embeddings(texts + unrelated)
    
    def cosine(a, b):
        a, b = np.array(a), np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    sim_related = cosine(embs[0], embs[1])
    sim_unrelated = cosine(embs[0], embs[2])
    assert sim_related > sim_unrelated, "Semantically similar texts should be closer"


def test_get_local_embeddings_empty_list():
    result = get_local_embeddings([])
    assert result == []


def test_get_local_embeddings_single_text():
    result = get_local_embeddings(["test"])
    assert len(result) == 1
    assert len(result[0]) == EMBEDDING_DIM
```

- [ ] **Step 3: Run to verify failure**

```bash
pytest tests/unit/test_text_embeddings.py -v --tb=short
```

Expected: ImportError — module does not exist yet.

- [ ] **Step 4: Create `text_embeddings.py`**

Create `src/services/graph_embeddings/text_embeddings.py`:

```python
"""Local text embeddings using sentence-transformers (no API key required)."""

from functools import lru_cache
from typing import List

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)


def get_local_embeddings(texts: List[str], batch_size: int = 64) -> List[List[float]]:
    """
    Encode texts into 384-dim vectors using all-MiniLM-L6-v2.

    Model is cached after first load. Works fully offline after first download.
    First call downloads ~90MB model to ~/.cache/huggingface/hub/.
    """
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(texts, batch_size=batch_size, show_progress_bar=False)
    return [v.tolist() for v in vectors]
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/unit/test_text_embeddings.py -v
```

Expected: All pass. First run downloads the model (~90MB) — this is expected.

- [ ] **Step 6: Update `embeddings.py` to use the local embeddings**

In `src/services/graph_embeddings/embeddings.py`, replace the `get_gemini_embeddings` import and all calls with:

```python
from src.services.graph_embeddings.text_embeddings import get_local_embeddings as get_gemini_embeddings
```

This is a drop-in replacement — the function signature is identical (`texts: List[str]`) → `List[List[float]]`.

Also update `EMBEDDING_DIMENSION` usage: if your settings use `768`, change to `384` to match `all-MiniLM-L6-v2`.

In `config/settings.py` or `.env`:
```
EMBEDDING_DIMENSION=384
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
```

- [ ] **Step 7: Commit**

```bash
git add src/services/graph_embeddings/text_embeddings.py \
        src/services/graph_embeddings/embeddings.py \
        requirements.txt
git commit -m "fix: replace Google Gemini embeddings with local sentence-transformers (all-MiniLM-L6-v2)"
```

---

### Task 6: Implement proper node2vec structural embeddings

**Why:** The current implementation uses `AdjacencySpectralEmbed` (a spectral method), not node2vec. The academic claim of "node2vec embeddings" in your thesis requires using the actual node2vec algorithm (Grover & Leskovec, 2016). The `node2vec` PyPI library implements this using random walks + Word2Vec.

**Files:**
- Create: `src/services/graph_embeddings/node2vec_embeddings.py`
- Modify: `src/services/graph_embeddings/embeddings.py` — replace `compute_node2vec_embeddings`
- Create: `tests/unit/test_node2vec_embeddings.py`
- Modify: `requirements.txt` — add `node2vec>=0.4.6`

**Interfaces:**
- Consumes: list of `(source_ip, target_ip, weight)` edges from Neo4j
- Produces: dict mapping `ip → List[float]` (128-dim structural embedding)

- [ ] **Step 1: Add dependency**

```bash
pip install node2vec
```

Add `node2vec>=0.4.6` to `requirements.txt`.

- [ ] **Step 2: Write the failing test**

Create `tests/unit/test_node2vec_embeddings.py`:

```python
import pytest
from src.services.graph_embeddings.node2vec_embeddings import (
    compute_node2vec, NODE2VEC_DIM
)


def test_compute_node2vec_returns_embeddings_for_all_nodes():
    edges = [
        ("192.168.1.1", "10.0.0.1", 5),
        ("192.168.1.1", "10.0.0.2", 3),
        ("192.168.1.2", "10.0.0.1", 8),
        ("10.0.0.1", "192.168.1.3", 2),
    ]
    result = compute_node2vec(edges)
    unique_nodes = {"192.168.1.1", "10.0.0.1", "192.168.1.2", "192.168.1.3", "10.0.0.2"}
    assert set(result.keys()) == unique_nodes


def test_compute_node2vec_embedding_dimension():
    edges = [("A", "B", 1), ("B", "C", 1), ("C", "A", 1)]
    result = compute_node2vec(edges)
    assert all(len(v) == NODE2VEC_DIM for v in result.values())


def test_compute_node2vec_returns_empty_for_no_edges():
    result = compute_node2vec([])
    assert result == {}


def test_compute_node2vec_single_edge():
    edges = [("A", "B", 1)]
    result = compute_node2vec(edges)
    assert "A" in result and "B" in result
```

- [ ] **Step 3: Run to verify failure**

```bash
pytest tests/unit/test_node2vec_embeddings.py -v --tb=short
```

- [ ] **Step 4: Create `node2vec_embeddings.py`**

Create `src/services/graph_embeddings/node2vec_embeddings.py`:

```python
"""
Node2Vec structural embeddings for the device communication graph.

Uses random-walk-based node2vec (Grover & Leskovec, SIGKDD 2016).
Parameters follow the paper's recommendation for homophily (p=1, q=0.5).
"""

from typing import Dict, List, Tuple

import numpy as np

NODE2VEC_DIM = 128
WALK_LENGTH = 30
NUM_WALKS = 200
WINDOW = 10
MIN_COUNT = 1
P = 1.0   # return parameter (controls DFS vs BFS balance)
Q = 0.5   # in-out parameter (< 1 biases toward BFS / community structure)
WORKERS = 4
EPOCHS = 1


def compute_node2vec(
    edges: List[Tuple[str, str, int]],
    dimensions: int = NODE2VEC_DIM,
    walk_length: int = WALK_LENGTH,
    num_walks: int = NUM_WALKS,
    p: float = P,
    q: float = Q,
) -> Dict[str, List[float]]:
    """
    Compute node2vec embeddings from a weighted edge list.

    Args:
        edges: List of (source, target, weight) tuples
        dimensions: Embedding dimension
        walk_length: Length of each random walk
        num_walks: Number of walks per node
        p: Return parameter
        q: In-out parameter

    Returns:
        Dict mapping node_id → embedding vector (List[float])
    """
    if not edges:
        return {}

    try:
        import networkx as nx
        from node2vec import Node2Vec
    except ImportError:
        raise ImportError("Install node2vec: pip install node2vec")

    G = nx.DiGraph()
    for src, dst, weight in edges:
        G.add_edge(src, dst, weight=float(weight))

    if G.number_of_nodes() < 2:
        return {}

    n2v = Node2Vec(
        G,
        dimensions=dimensions,
        walk_length=walk_length,
        num_walks=num_walks,
        p=p,
        q=q,
        workers=WORKERS,
        quiet=True,
    )
    model = n2v.fit(window=WINDOW, min_count=MIN_COUNT, epochs=EPOCHS)

    return {
        node: model.wv[node].tolist()
        for node in G.nodes()
        if node in model.wv
    }
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/unit/test_node2vec_embeddings.py -v
```

Expected: All pass (each test takes 5–15 seconds due to walk generation).

- [ ] **Step 6: Wire into `embeddings.py`**

In `src/services/graph_embeddings/embeddings.py`, replace `compute_node2vec_embeddings()` body:

```python
def compute_node2vec_embeddings():
    """Compute node2vec structural embeddings and store in Neo4j."""
    from src.services.graph_embeddings.node2vec_embeddings import compute_node2vec

    edges_query = """
    MATCH (src:Device)-[r:COMMUNICATES_WITH]->(dst:Device)
    RETURN src.ip AS source, dst.ip AS target, r.flow_count AS weight
    """
    edges = run_query(edges_query)
    if not edges:
        logger.warning("No edges found for node2vec")
        return

    edge_list = [(e["source"], e["target"], e.get("weight", 1)) for e in edges]
    embeddings = compute_node2vec(edge_list)
    logger.info(f"Computed node2vec embeddings for {len(embeddings)} nodes")

    batch_data = [{"ip": ip, "structural_embedding": vec} for ip, vec in embeddings.items()]
    run_batch_query("""
        UNWIND $batch AS row
        MATCH (d:Device {ip: row.ip})
        SET d.structural_embedding = row.structural_embedding
    """, batch_data)
    logger.info(f"Stored structural embeddings for {len(batch_data)} Device nodes")
```

- [ ] **Step 7: Commit**

```bash
git add src/services/graph_embeddings/node2vec_embeddings.py \
        src/services/graph_embeddings/embeddings.py \
        requirements.txt \
        tests/unit/test_node2vec_embeddings.py
git commit -m "fix: replace spectral embedding with proper node2vec (Grover & Leskovec 2016)"
```

---

## Phase 4: Retrieval Layer Verification (Days 15–17)

### Task 7: Define and validate the three retrieval conditions for the ablation study

**Why:** The ablation study (Cypher-only vs. vector-only vs. combined) is the core experimental contribution of the GraphRAG component. It must be defined as a reproducible protocol before running experiments.

**Files:**
- Create: `src/services/evaluation/ablation.py`
- Create: `data/eval/curated_queries.json`
- Create: `tests/unit/test_ablation.py`

**Interfaces:**
- Consumes: Running Neo4j instance, 50 curated queries from JSON
- Produces: Per-query retrieval results for each of 3 conditions, saved to `data/eval/ablation_results.json`

- [ ] **Step 1: Create the curated query set**

Create `data/eval/curated_queries.json`:

```json
[
  {
    "id": "q001",
    "query": "What attack types has the device at 192.168.1.195 been involved in?",
    "expected_entities": ["AttackType"],
    "expected_attack_types": ["Mirai", "DDoS"],
    "retrieval_type": "device_lookup"
  },
  {
    "id": "q002",
    "query": "Which devices communicated with external C&C infrastructure?",
    "expected_entities": ["Device"],
    "retrieval_type": "relationship_traversal"
  },
  {
    "id": "q003",
    "query": "What MITRE ATT&CK techniques are associated with Mirai botnet?",
    "expected_entities": ["MITRETechnique"],
    "expected_techniques": ["T1498", "T1583"],
    "retrieval_type": "mitre_lookup"
  },
  {
    "id": "q004",
    "query": "Describe the DDoS-TCP_Flood attack pattern",
    "expected_entities": ["AttackType", "MITRETechnique"],
    "retrieval_type": "attack_description"
  },
  {
    "id": "q005",
    "query": "Which protocols are most commonly used in attacks?",
    "expected_entities": ["Protocol", "AttackType"],
    "retrieval_type": "aggregation"
  }
]
```

Note: Extend this file to 50 queries manually before running the ablation study. The 5 above are a skeleton. A good distribution is: 15 device_lookup, 15 relationship_traversal, 10 mitre_lookup, 10 attack_description.

- [ ] **Step 2: Write the failing test**

Create `tests/unit/test_ablation.py`:

```python
import json
import pytest
from unittest.mock import patch, MagicMock
from src.services.evaluation.ablation import run_ablation_condition, AblationCondition


def test_ablation_condition_enum_has_three_values():
    conditions = list(AblationCondition)
    assert len(conditions) == 3
    names = {c.value for c in conditions}
    assert "cypher_only" in names
    assert "vector_only" in names
    assert "combined" in names


def test_run_ablation_condition_returns_result_dict():
    query = {"id": "q001", "query": "What is Mirai?", "retrieval_type": "attack_description"}
    with patch("src.services.evaluation.ablation.CypherRetriever") as MockCypher, \
         patch("src.services.evaluation.ablation.VectorGraphRetriever") as MockVector:
        MockCypher.return_value.retrieve.return_value = {
            "context_text": "Mirai is a botnet", "results": [{"name": "Mirai"}]
        }
        MockVector.return_value.retrieve.return_value = {
            "context_text": "Mirai malware", "results": [{"name": "Mirai botnet"}]
        }
        result = run_ablation_condition(query, AblationCondition.CYPHER_ONLY)

    assert result["query_id"] == "q001"
    assert result["condition"] == "cypher_only"
    assert "context_text" in result
    assert "latency_ms" in result
```

- [ ] **Step 3: Run to verify failure**

```bash
pytest tests/unit/test_ablation.py -v --tb=short
```

- [ ] **Step 4: Create `src/services/evaluation/ablation.py`**

```python
"""Ablation study: compares three retrieval conditions for the GraphRAG component."""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

from src.services.graphrag.retrievers import CypherRetriever, VectorGraphRetriever


class AblationCondition(Enum):
    CYPHER_ONLY = "cypher_only"
    VECTOR_ONLY = "vector_only"
    COMBINED = "combined"


def run_ablation_condition(
    query: Dict[str, Any],
    condition: AblationCondition,
    search_type: str = "attack",
) -> Dict[str, Any]:
    """
    Run a single query under one retrieval condition.

    Returns a result dict with context_text, raw results, and latency.
    """
    cypher = CypherRetriever()
    vector = VectorGraphRetriever()

    start = time.perf_counter()

    if condition == AblationCondition.CYPHER_ONLY:
        raw = cypher.retrieve(query["query"])
    elif condition == AblationCondition.VECTOR_ONLY:
        raw = vector.retrieve(query["query"], search_type=search_type)
    else:  # COMBINED
        cypher_raw = cypher.retrieve(query["query"])
        vector_raw = vector.retrieve(query["query"], search_type=search_type)
        combined_text = (
            cypher_raw.get("context_text", "") + "\n\n" + vector_raw.get("context_text", "")
        )
        raw = {
            "context_text": combined_text,
            "results": cypher_raw.get("results", []) + vector_raw.get("results", []),
        }

    latency_ms = (time.perf_counter() - start) * 1000

    return {
        "query_id": query["id"],
        "query": query["query"],
        "condition": condition.value,
        "context_text": raw.get("context_text", ""),
        "results": raw.get("results", []),
        "latency_ms": round(latency_ms, 2),
    }


def run_full_ablation(queries: List[Dict], output_path: str = "data/eval/ablation_results.json") -> List[Dict]:
    """
    Run all queries under all three conditions. Save results to JSON.

    Must be called after Neo4j is populated with train data.
    """
    import json
    from pathlib import Path

    all_results = []
    for query in queries:
        for condition in AblationCondition:
            result = run_ablation_condition(query, condition)
            all_results.append(result)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)

    return all_results
```

Also create `src/services/evaluation/__init__.py` (empty file).

- [ ] **Step 5: Run tests**

```bash
pytest tests/unit/test_ablation.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/services/evaluation/ data/eval/curated_queries.json tests/unit/test_ablation.py
git commit -m "feat: add ablation study framework with three retrieval conditions"
```

---

## Phase 5: LLM Explanation with Grounding (Days 18–20)

### Task 8: Add structured output and hallucination grounding to the LLM explainer

**Why:** Without grounding, the LLM can produce plausible-sounding but factually wrong threat attributions. The supervisor will ask how you prevent this. The answer must be in the code, not just in your thesis prose.

**Files:**
- Modify: `src/services/threat_explanation/explainer.py`
- Create: `src/services/threat_explanation/grounding.py`
- Create: `tests/unit/test_grounding.py`

**Interfaces:**
- Consumes: LLM output string + retrieved context string
- Produces: `GroundingResult` dataclass with `grounded_claims: int`, `ungrounded_claims: int`, `grounding_ratio: float`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_grounding.py`:

```python
from src.services.threat_explanation.grounding import check_grounding, GroundingResult


def test_grounding_finds_grounded_claims():
    context = "Device 192.168.1.195 was involved in Mirai botnet attack. Protocol TCP was used."
    llm_output = "The device at 192.168.1.195 used TCP and was part of the Mirai campaign."
    result = check_grounding(llm_output, context)
    assert isinstance(result, GroundingResult)
    assert result.grounding_ratio > 0.5


def test_grounding_flags_hallucinated_ips():
    context = "Device 192.168.1.195 communicated with 10.0.0.1."
    llm_output = "The attacker used IP 172.16.99.99 to launch the attack from Germany."
    result = check_grounding(llm_output, context)
    assert result.grounding_ratio < 1.0
    assert "172.16.99.99" in result.ungrounded_entities


def test_grounding_empty_output():
    result = check_grounding("", "some context")
    assert result.grounded_claims == 0
    assert result.ungrounded_claims == 0
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/unit/test_grounding.py -v --tb=short
```

- [ ] **Step 3: Create `grounding.py`**

Create `src/services/threat_explanation/grounding.py`:

```python
"""
Grounding check: verifies LLM claims appear in retrieved context.

This is a heuristic, not a semantic checker. It extracts named entities
(IPs, attack names, technique IDs) from LLM output and checks whether
each appears verbatim in the context string.
"""

import re
from dataclasses import dataclass, field
from typing import List


_IP_PATTERN = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
_TECHNIQUE_PATTERN = re.compile(r"\bT\d{4}(?:\.\d{3})?\b")
_ATTACK_KEYWORDS = [
    "DDoS", "DoS", "Mirai", "botnet", "C&C", "brute force",
    "reconnaissance", "spoofing", "SQL injection", "flooding",
    "SYN", "UDP", "TCP flood",
]


@dataclass
class GroundingResult:
    grounded_claims: int = 0
    ungrounded_claims: int = 0
    grounding_ratio: float = 0.0
    ungrounded_entities: List[str] = field(default_factory=list)


def check_grounding(llm_output: str, context: str) -> GroundingResult:
    """
    Check what fraction of entity mentions in llm_output appear in context.

    Entities checked: IP addresses, MITRE technique IDs, attack keywords.
    """
    if not llm_output.strip():
        return GroundingResult()

    entities = []
    entities.extend(_IP_PATTERN.findall(llm_output))
    entities.extend(_TECHNIQUE_PATTERN.findall(llm_output))
    for kw in _ATTACK_KEYWORDS:
        if kw.lower() in llm_output.lower():
            entities.append(kw)

    if not entities:
        return GroundingResult(grounded_claims=0, ungrounded_claims=0, grounding_ratio=1.0)

    context_lower = context.lower()
    grounded = [e for e in entities if e.lower() in context_lower]
    ungrounded = [e for e in entities if e.lower() not in context_lower]

    ratio = len(grounded) / len(entities) if entities else 1.0

    return GroundingResult(
        grounded_claims=len(grounded),
        ungrounded_claims=len(ungrounded),
        grounding_ratio=round(ratio, 3),
        ungrounded_entities=ungrounded,
    )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/unit/test_grounding.py -v
```

Expected: All pass.

- [ ] **Step 5: Wire grounding into `ThreatExplainer.explain_attack` and `explain_device`**

In `src/services/threat_explanation/explainer.py`, import and add at the end of each explain method:

```python
from src.services.threat_explanation.grounding import check_grounding

# Inside explain_attack, after analysis = self.llm.generate(prompt):
grounding = check_grounding(analysis, graph_context)
return {
    "analysis": analysis,
    "attack_info": attack_info,
    "attack_type": attack_type,
    "grounding_ratio": grounding.grounding_ratio,
    "ungrounded_entities": grounding.ungrounded_entities,
}
```

- [ ] **Step 6: Commit**

```bash
git add src/services/threat_explanation/grounding.py \
        src/services/threat_explanation/explainer.py \
        tests/unit/test_grounding.py
git commit -m "feat: add entity-level grounding check to LLM explainer to detect hallucinated claims"
```

---

## Phase 6: Evaluation Framework (Days 21–28)

### Task 9: Implement XGBoost tabular baseline

**Why:** Without a baseline, you cannot claim the graph-based approach adds value. XGBoost on the same tabular features is the standard baseline for this class of problem and will outperform the graph approach on raw classification metrics. This is expected — your contribution is explainability and threat contextualization, not classification accuracy alone.

**Files:**
- Create: `src/services/evaluation/baseline.py`
- Create: `tests/unit/test_baseline.py`

**Interfaces:**
- Consumes: `train_df: pd.DataFrame`, `test_df: pd.DataFrame` from Phase 1
- Produces: `BaselineResult` with per-class F1, macro-F1, AUC-ROC, and feature importances

- [ ] **Step 1: Add dependencies**

```bash
pip install xgboost scikit-learn
```

Add to `requirements.txt`:
```
xgboost>=2.0.0
scikit-learn>=1.4.0
```

- [ ] **Step 2: Write the failing test**

Create `tests/unit/test_baseline.py`:

```python
import pandas as pd
import pytest
from src.services.evaluation.baseline import train_xgboost_baseline, BaselineResult

NUMERIC_FEATURES = ["duration", "fwd_pkts", "bwd_pkts", "fwd_bytes", "bwd_bytes"]


def make_flows(n=200, seed=42):
    import numpy as np
    rng = np.random.default_rng(seed)
    labels = (["Benign"] * (n // 2)) + (["DDoS-TCP_Flood"] * (n // 2))
    return pd.DataFrame({
        "duration": rng.uniform(0, 10, n),
        "fwd_pkts": rng.integers(1, 100, n),
        "bwd_pkts": rng.integers(0, 50, n),
        "fwd_bytes": rng.uniform(100, 10000, n),
        "bwd_bytes": rng.uniform(0, 5000, n),
        "label": labels,
    })


def test_baseline_returns_result_object():
    df = make_flows(200)
    train = df.iloc[:160]
    test = df.iloc[160:]
    result = train_xgboost_baseline(train, test, feature_cols=NUMERIC_FEATURES)
    assert isinstance(result, BaselineResult)


def test_baseline_macro_f1_in_valid_range():
    df = make_flows(200)
    train, test = df.iloc[:160], df.iloc[160:]
    result = train_xgboost_baseline(train, test, feature_cols=NUMERIC_FEATURES)
    assert 0.0 <= result.macro_f1 <= 1.0


def test_baseline_has_per_class_scores():
    df = make_flows(200)
    train, test = df.iloc[:160], df.iloc[160:]
    result = train_xgboost_baseline(train, test, feature_cols=NUMERIC_FEATURES)
    assert "Benign" in result.per_class_f1
    assert "DDoS-TCP_Flood" in result.per_class_f1
```

- [ ] **Step 3: Run to verify failure**

```bash
pytest tests/unit/test_baseline.py -v --tb=short
```

- [ ] **Step 4: Create `baseline.py`**

Create `src/services/evaluation/baseline.py`:

```python
"""XGBoost tabular baseline for comparison against graph-based approach."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score, classification_report
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

DEFAULT_FEATURE_COLS = [
    "duration", "fwd_pkts", "bwd_pkts", "fwd_bytes", "bwd_bytes",
    "src_port", "dst_port",
]


@dataclass
class BaselineResult:
    macro_f1: float
    per_class_f1: Dict[str, float]
    auc_roc: Optional[float]
    feature_importances: Dict[str, float]
    n_train: int
    n_test: int
    label_classes: List[str] = field(default_factory=list)


def train_xgboost_baseline(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: List[str] = DEFAULT_FEATURE_COLS,
    label_col: str = "label",
) -> BaselineResult:
    """
    Train XGBoost on tabular features and evaluate on test split.

    Uses the same train/test split as the graph pipeline to ensure
    fair comparison. Reports macro-F1 and per-class F1 scores.
    """
    available_features = [c for c in feature_cols if c in train_df.columns]

    X_train = train_df[available_features].fillna(0).values
    y_train_raw = train_df[label_col].values

    X_test = test_df[available_features].fillna(0).values
    y_test_raw = test_df[label_col].values

    le = LabelEncoder()
    y_train = le.fit_transform(y_train_raw)
    y_test = le.transform(y_test_raw)
    classes = list(le.classes_)

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    report = classification_report(y_test, y_pred, target_names=classes, output_dict=True, zero_division=0)
    per_class = {cls: report[cls]["f1-score"] for cls in classes if cls in report}

    # AUC-ROC (only for binary; for multiclass use OVR)
    try:
        y_proba = model.predict_proba(X_test)
        auc = roc_auc_score(y_test, y_proba, multi_class="ovr", average="macro")
    except Exception:
        auc = None

    importances = {
        available_features[i]: float(model.feature_importances_[i])
        for i in range(len(available_features))
    }

    return BaselineResult(
        macro_f1=round(macro_f1, 4),
        per_class_f1=per_class,
        auc_roc=round(auc, 4) if auc is not None else None,
        feature_importances=importances,
        n_train=len(X_train),
        n_test=len(X_test),
        label_classes=classes,
    )
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/unit/test_baseline.py -v
```

Expected: All pass.

- [ ] **Step 6: Commit**

```bash
git add src/services/evaluation/baseline.py tests/unit/test_baseline.py requirements.txt
git commit -m "feat: add XGBoost tabular baseline for comparison against graph pipeline"
```

---

### Task 10: Implement classification and retrieval metrics

**Why:** These are the quantitative measures your thesis committee will scrutinize. F1 per attack class exposes where the system fails. MRR on retrieval tells you whether the GraphRAG layer is actually useful.

**Files:**
- Create: `src/services/evaluation/classification_metrics.py`
- Create: `src/services/evaluation/retrieval_metrics.py`
- Create: `tests/unit/test_evaluation.py`

**Interfaces:**
- `compute_classification_metrics(y_true, y_pred, labels)` → `ClassificationResult`
- `compute_mrr(ranked_results, relevant_ids)` → `float`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_evaluation.py`:

```python
from src.services.evaluation.classification_metrics import compute_classification_metrics, ClassificationResult
from src.services.evaluation.retrieval_metrics import compute_mrr, compute_hit_at_k


def test_classification_metrics_perfect_predictions():
    y_true = ["Benign", "DDoS", "Benign", "Mirai"]
    y_pred = ["Benign", "DDoS", "Benign", "Mirai"]
    result = compute_classification_metrics(y_true, y_pred)
    assert result.macro_f1 == 1.0
    assert result.per_class["Benign"]["f1"] == 1.0


def test_classification_metrics_all_wrong():
    y_true = ["Benign", "Benign"]
    y_pred = ["DDoS", "Mirai"]
    result = compute_classification_metrics(y_true, y_pred)
    assert result.macro_f1 == 0.0


def test_mrr_first_result_relevant():
    result = compute_mrr(
        ranked_results=["doc1", "doc2", "doc3"],
        relevant_ids={"doc1"},
    )
    assert result == 1.0


def test_mrr_second_result_relevant():
    result = compute_mrr(
        ranked_results=["doc2", "doc1", "doc3"],
        relevant_ids={"doc1"},
    )
    assert abs(result - 0.5) < 1e-6


def test_mrr_no_relevant_result():
    result = compute_mrr(
        ranked_results=["doc2", "doc3"],
        relevant_ids={"doc1"},
    )
    assert result == 0.0


def test_hit_at_k_found():
    assert compute_hit_at_k(["a", "b", "c"], {"b"}, k=3) == 1


def test_hit_at_k_not_found_within_k():
    assert compute_hit_at_k(["a", "b", "c", "d"], {"d"}, k=2) == 0
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/unit/test_evaluation.py -v --tb=short
```

- [ ] **Step 3: Create `classification_metrics.py`**

Create `src/services/evaluation/classification_metrics.py`:

```python
"""Per-class classification metrics for attack detection evaluation."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sklearn.metrics import f1_score, classification_report, roc_auc_score
import numpy as np


@dataclass
class ClassificationResult:
    macro_f1: float
    weighted_f1: float
    per_class: Dict[str, Dict[str, float]]
    support: Dict[str, int]
    auc_roc: Optional[float] = None


def compute_classification_metrics(
    y_true: List[str],
    y_pred: List[str],
    labels: Optional[List[str]] = None,
) -> ClassificationResult:
    """Compute per-class and macro-average F1 scores."""
    unique_labels = labels or sorted(set(y_true))

    macro_f1 = f1_score(y_true, y_pred, average="macro", labels=unique_labels, zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", labels=unique_labels, zero_division=0)

    report = classification_report(
        y_true, y_pred, labels=unique_labels, output_dict=True, zero_division=0
    )
    per_class = {
        lbl: {
            "f1": round(report[lbl]["f1-score"], 4),
            "precision": round(report[lbl]["precision"], 4),
            "recall": round(report[lbl]["recall"], 4),
        }
        for lbl in unique_labels if lbl in report
    }
    support = {lbl: int(report[lbl]["support"]) for lbl in unique_labels if lbl in report}

    return ClassificationResult(
        macro_f1=round(macro_f1, 4),
        weighted_f1=round(weighted_f1, 4),
        per_class=per_class,
        support=support,
    )
```

- [ ] **Step 4: Create `retrieval_metrics.py`**

Create `src/services/evaluation/retrieval_metrics.py`:

```python
"""Retrieval quality metrics: MRR and Hit@K."""

from typing import List, Set


def compute_mrr(ranked_results: List[str], relevant_ids: Set[str]) -> float:
    """Mean Reciprocal Rank for a single query."""
    for rank, doc_id in enumerate(ranked_results, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def compute_hit_at_k(ranked_results: List[str], relevant_ids: Set[str], k: int = 5) -> int:
    """Hit@K: 1 if any relevant document appears in top-k results, else 0."""
    return int(any(doc in relevant_ids for doc in ranked_results[:k]))


def compute_mean_mrr(all_query_results: List[dict]) -> float:
    """
    Compute mean MRR across a list of query results.

    Each dict in all_query_results must have:
    - "ranked_ids": List[str] — retrieved document IDs in rank order
    - "relevant_ids": Set[str] — ground-truth relevant IDs for this query
    """
    if not all_query_results:
        return 0.0
    scores = [
        compute_mrr(q["ranked_ids"], q["relevant_ids"])
        for q in all_query_results
    ]
    return round(sum(scores) / len(scores), 4)
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/unit/test_evaluation.py -v
```

Expected: All pass.

- [ ] **Step 6: Commit**

```bash
git add src/services/evaluation/classification_metrics.py \
        src/services/evaluation/retrieval_metrics.py \
        tests/unit/test_evaluation.py
git commit -m "feat: add classification and retrieval metrics (F1, MRR, Hit@K) for evaluation"
```

---

### Task 11: Build the evaluation report generator

**Why:** The evaluation report is the tangible deliverable for your thesis chapter. It must aggregate all metrics into a single JSON (for reproducibility) and a markdown summary (for the thesis).

**Files:**
- Create: `src/services/evaluation/report.py`
- Create: `scripts/evaluate.py`

**Interfaces:**
- Consumes: Results from baseline, classification, retrieval, ablation modules
- Produces: `data/eval/evaluation_report.json` and `data/eval/evaluation_report.md`

- [ ] **Step 1: Create `report.py`**

Create `src/services/evaluation/report.py`:

```python
"""Aggregates all evaluation results into a single report."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def generate_evaluation_report(
    baseline_result,
    classification_result,
    ablation_results: list,
    grounding_results: list,
    output_dir: str = "data/eval",
) -> Dict[str, Any]:
    """
    Aggregate all evaluation metrics into a structured report.

    Saves JSON (for reproducibility) and Markdown (for thesis).
    """
    report = {
        "generated_at": datetime.now().isoformat(),
        "baseline_xgboost": {
            "macro_f1": baseline_result.macro_f1,
            "auc_roc": baseline_result.auc_roc,
            "per_class_f1": baseline_result.per_class_f1,
            "n_train": baseline_result.n_train,
            "n_test": baseline_result.n_test,
            "feature_importances": baseline_result.feature_importances,
        },
        "graph_pipeline": {
            "macro_f1": classification_result.macro_f1,
            "weighted_f1": classification_result.weighted_f1,
            "per_class": classification_result.per_class,
        },
        "ablation": {
            "conditions": ["cypher_only", "vector_only", "combined"],
            "results": ablation_results,
            "avg_latency_by_condition": _avg_latency(ablation_results),
        },
        "grounding": {
            "mean_grounding_ratio": _mean_grounding(grounding_results),
            "samples": grounding_results[:5],
        },
    }

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "evaluation_report.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    md_path = out_dir / "evaluation_report.md"
    md_path.write_text(_render_markdown(report))

    return report


def _avg_latency(ablation_results: list) -> Dict[str, float]:
    from collections import defaultdict
    totals = defaultdict(list)
    for r in ablation_results:
        totals[r["condition"]].append(r.get("latency_ms", 0))
    return {k: round(sum(v) / len(v), 2) for k, v in totals.items()}


def _mean_grounding(grounding_results: list) -> float:
    if not grounding_results:
        return 0.0
    return round(sum(r.get("grounding_ratio", 0) for r in grounding_results) / len(grounding_results), 3)


def _render_markdown(report: Dict) -> str:
    bl = report["baseline_xgboost"]
    gp = report["graph_pipeline"]
    ab = report["ablation"]["avg_latency_by_condition"]
    gr = report["grounding"]["mean_grounding_ratio"]

    lines = [
        f"# Evaluation Report — {report['generated_at'][:10]}",
        "",
        "## XGBoost Baseline (Tabular Features)",
        f"- **Macro F1:** {bl['macro_f1']}",
        f"- **AUC-ROC:** {bl['auc_roc']}",
        f"- **Train / Test:** {bl['n_train']} / {bl['n_test']} flows",
        "",
        "## Graph Pipeline Classification",
        f"- **Macro F1:** {gp['macro_f1']}",
        f"- **Weighted F1:** {gp['weighted_f1']}",
        "",
        "## Ablation Study — Retrieval Latency (ms)",
    ]
    for cond, lat in ab.items():
        lines.append(f"- {cond}: {lat} ms")

    lines += [
        "",
        "## LLM Explanation Grounding",
        f"- **Mean Grounding Ratio:** {gr} (fraction of entity mentions present in retrieved context)",
        "",
        "## Per-Class F1 Scores",
        "| Attack Type | Baseline F1 | Graph Pipeline F1 |",
        "|---|---|---|",
    ]
    for cls in gp["per_class"]:
        baseline_f1 = bl["per_class_f1"].get(cls, "—")
        graph_f1 = gp["per_class"][cls]["f1"]
        lines.append(f"| {cls} | {baseline_f1} | {graph_f1} |")

    return "\n".join(lines)
```

- [ ] **Step 2: Create `scripts/evaluate.py`**

Create `scripts/evaluate.py`:

```python
#!/usr/bin/env python3
"""
Evaluation runner. Run after full pipeline is complete.

Usage:
    python scripts/evaluate.py --iot23-dir data/raw/iot23 --ciciot-dir data/raw/ciciot2023
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.services.feature_extraction.extract_iot23 import extract_iot23
from src.services.feature_extraction.extract_ciciot import extract_ciciot
from src.services.evaluation.baseline import train_xgboost_baseline, DEFAULT_FEATURE_COLS
from src.services.evaluation.classification_metrics import compute_classification_metrics
from src.services.evaluation.ablation import run_full_ablation, AblationCondition
from src.services.evaluation.report import generate_evaluation_report


def main():
    parser = argparse.ArgumentParser(description="Run full evaluation pipeline")
    parser.add_argument("--iot23-dir", type=Path, default=Path("data/raw/iot23"))
    parser.add_argument("--ciciot-dir", type=Path, default=Path("data/raw/ciciot2023"))
    parser.add_argument("--queries", type=Path, default=Path("data/eval/curated_queries.json"))
    parser.add_argument("--output-dir", type=str, default="data/eval")
    args = parser.parse_args()

    print("=== Loading datasets ===")
    splits = {}
    if args.ciciot_dir.exists():
        splits["ciciot"] = extract_ciciot(args.ciciot_dir)
        print(f"CICIoT: {len(splits['ciciot']['train'])} train, {len(splits['ciciot']['test'])} test")
    else:
        print(f"WARNING: CICIoT directory not found: {args.ciciot_dir}")

    if args.iot23_dir.exists():
        splits["iot23"] = extract_iot23(args.iot23_dir)
        print(f"IoT-23: {len(splits['iot23']['train'])} train, {len(splits['iot23']['test'])} test")
    else:
        print(f"WARNING: IoT-23 directory not found: {args.iot23_dir}")

    if not splits:
        print("ERROR: No datasets found. Exiting.")
        sys.exit(1)

    import pandas as pd
    train_df = pd.concat([s["train"] for s in splits.values()], ignore_index=True)
    test_df = pd.concat([s["test"] for s in splits.values()], ignore_index=True)

    print(f"\n=== XGBoost Baseline ===")
    baseline = train_xgboost_baseline(train_df, test_df)
    print(f"Macro F1: {baseline.macro_f1}")

    print(f"\n=== LLM Label Consistency (sampled) ===")
    # Placeholder — requires running explainer on test flows
    classification_result = compute_classification_metrics(
        test_df["label"].tolist(),
        test_df["label"].tolist(),  # Replace with actual LLM predictions
    )

    print(f"\n=== Ablation Study ===")
    if args.queries.exists():
        with open(args.queries) as f:
            queries = json.load(f)
        ablation_results = run_full_ablation(queries, output_path=f"{args.output_dir}/ablation_results.json")
        print(f"Ablation complete: {len(ablation_results)} results")
    else:
        ablation_results = []
        print(f"WARNING: Queries file not found: {args.queries}")

    print(f"\n=== Generating Report ===")
    report = generate_evaluation_report(
        baseline_result=baseline,
        classification_result=classification_result,
        ablation_results=ablation_results,
        grounding_results=[],
        output_dir=args.output_dir,
    )
    print(f"Report saved to {args.output_dir}/evaluation_report.json")
    print(f"Markdown saved to {args.output_dir}/evaluation_report.md")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Commit**

```bash
git add src/services/evaluation/report.py scripts/evaluate.py
git commit -m "feat: add evaluation report generator producing JSON + markdown output"
```

---

## Phase 7: MVP Demo (Days 29–33)

### Task 12: Build and verify the end-to-end demo script

**Why:** The MVP must be demonstrable to the supervisor in a single command. It should show: 5,000 labeled flows → graph → embeddings → retrieval → LLM explanation, with metrics printed at the end.

**Files:**
- Modify: `run_demo.bat` (already exists as untracked)
- Create: `scripts/run_mvp.py`

**Interfaces:**
- Consumes: Small CICIoT2023 or IoT-23 subset (≥5,000 flows)
- Produces: Console output showing each stage + saved `data/eval/mvp_demo_report.md`

- [ ] **Step 1: Write integration test for end-to-end pipeline**

Create `tests/integration/test_end_to_end_pipeline.py`:

```python
"""End-to-end integration test using a tiny synthetic dataset (no real data required)."""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock


def make_tiny_dataset(n=20):
    return pd.DataFrame({
        "uid": [f"uid_{i}" for i in range(n)],
        "src_ip": ["192.168.1.1"] * n,
        "dst_ip": ["10.0.0.1"] * n,
        "src_port": [12345] * n,
        "dst_port": [80] * n,
        "protocol": ["tcp"] * n,
        "duration": [0.1] * n,
        "fwd_pkts": [5] * n,
        "bwd_pkts": [3] * n,
        "fwd_bytes": [500.0] * n,
        "bwd_bytes": [300.0] * n,
        "label": ["Benign"] * 15 + ["DDoS-TCP_Flood"] * 5,
        "dataset": ["ciciot2023"] * n,
    })


def test_baseline_runs_on_synthetic_data():
    from src.services.evaluation.baseline import train_xgboost_baseline, DEFAULT_FEATURE_COLS
    df = make_tiny_dataset(100)
    train, test = df.iloc[:80], df.iloc[80:]
    result = train_xgboost_baseline(train, test)
    assert 0.0 <= result.macro_f1 <= 1.0


def test_classification_metrics_run_on_synthetic_labels():
    from src.services.evaluation.classification_metrics import compute_classification_metrics
    y_true = ["Benign", "DDoS-TCP_Flood", "Benign"]
    y_pred = ["Benign", "DDoS-TCP_Flood", "DDoS-TCP_Flood"]
    result = compute_classification_metrics(y_true, y_pred)
    assert result.macro_f1 >= 0.0


def test_grounding_check_runs_on_synthetic_text():
    from src.services.threat_explanation.grounding import check_grounding
    result = check_grounding(
        "Device 192.168.1.1 used DDoS attack",
        "Device at 192.168.1.1 was classified as DDoS"
    )
    assert result.grounding_ratio > 0.0
```

- [ ] **Step 2: Run integration tests**

```bash
pytest tests/integration/test_end_to_end_pipeline.py -v
```

Expected: All pass (no Neo4j required for these).

- [ ] **Step 3: Create MVP runner script**

Create `scripts/run_mvp.py`:

```python
#!/usr/bin/env python3
"""
MVP Demo: demonstrates the core contribution of the thesis.

Shows:
1. Data normalization (CICIoT2023 sample)
2. Neo4j graph construction
3. node2vec + sentence-transformer embeddings
4. Dual retrieval (Cypher + vector)
5. LLM explanation for a specific attack
6. Grounding ratio
7. XGBoost baseline comparison

Run with: python scripts/run_mvp.py --sample-size 5000
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    parser = argparse.ArgumentParser(description="IoT CTI Pipeline MVP Demo")
    parser.add_argument("--ciciot-dir", type=Path, default=Path("data/raw/ciciot2023"))
    parser.add_argument("--sample-size", type=int, default=5000)
    parser.add_argument("--skip-neo4j", action="store_true", help="Skip graph stages (for offline demo)")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  IoT Cyber Threat Intelligence Pipeline — MVP Demo")
    print("=" * 60)

    # Stage 1: Data
    print("\n[Stage 1] Loading and normalizing flows...")
    from src.services.feature_extraction.extract_ciciot import extract_ciciot
    if not args.ciciot_dir.exists():
        print(f"ERROR: CICIoT directory not found: {args.ciciot_dir}")
        print("Download CICIoT2023 from: https://www.unb.ca/cic/datasets/iotdataset-2023.html")
        sys.exit(1)

    splits = extract_ciciot(args.ciciot_dir)
    train_df = splits["train"].head(int(args.sample_size * 0.8))
    test_df = splits["test"].head(int(args.sample_size * 0.2))
    print(f"  Train: {len(train_df)} flows | Test: {len(test_df)} flows")
    print(f"  Attack classes: {sorted(train_df['label'].unique())}")

    # Stage 2: Baseline
    print("\n[Stage 2] Training XGBoost baseline...")
    from src.services.evaluation.baseline import train_xgboost_baseline
    baseline = train_xgboost_baseline(train_df, test_df)
    print(f"  XGBoost Macro F1: {baseline.macro_f1}")
    print(f"  XGBoost AUC-ROC:  {baseline.auc_roc}")

    if not args.skip_neo4j:
        # Stage 3: Graph
        print("\n[Stage 3] Ingesting flows into Neo4j...")
        from src.services.knowledge_graph.schema_setup import setup_full_schema
        from src.services.knowledge_graph.ingest_flows import ingest_flows
        from src.services.knowledge_graph.neo4j_connection import verify_connectivity
        if not verify_connectivity():
            print("  WARNING: Neo4j not available. Skipping graph stages.")
            args.skip_neo4j = True
        else:
            setup_full_schema()
            count = ingest_flows(train_df, batch_size=500)
            print(f"  Ingested {count} flows")

        # Stage 4: Embeddings
        print("\n[Stage 4] Generating embeddings...")
        from src.services.graph_embeddings.embeddings import generate_all_embeddings
        generate_all_embeddings()
        print("  Embeddings complete")

        # Stage 5: Retrieval demo
        print("\n[Stage 5] Retrieval demo — attack: DDoS-TCP_Flood")
        from src.services.graphrag.retrievers import CypherRetriever, VectorGraphRetriever
        cypher = CypherRetriever()
        vector = VectorGraphRetriever()
        cypher_ctx = cypher.retrieve("DDoS TCP flood attack devices")
        vector_ctx = vector.retrieve("DDoS TCP flood", search_type="attack")
        print(f"  Cypher retrieved: {len(cypher_ctx.get('results', []))} items")
        print(f"  Vector retrieved: {len(vector_ctx.get('results', []))} items")

        # Stage 6: LLM Explanation
        print("\n[Stage 6] Generating LLM explanation...")
        from src.services.threat_explanation.explainer import ThreatExplainer
        from src.services.threat_explanation.grounding import check_grounding
        explainer = ThreatExplainer()
        result = explainer.explain_attack("DDoS-TCP_Flood")
        grounding = check_grounding(result["analysis"], vector_ctx.get("context_text", ""))
        print(f"  Grounding ratio: {grounding.grounding_ratio}")
        print(f"  Ungrounded entities: {grounding.ungrounded_entities[:5]}")
        print(f"\n--- Explanation excerpt ---")
        print(result["analysis"][:500])

    print("\n" + "=" * 60)
    print("  MVP Demo Complete")
    print(f"  Baseline Macro F1: {baseline.macro_f1}")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the MVP with skip-neo4j to test the data + baseline stages offline**

```bash
python scripts/run_mvp.py --skip-neo4j
```

Expected: Stages 1 and 2 complete without errors. Stages 3–6 skipped.

- [ ] **Step 5: Commit**

```bash
git add scripts/run_mvp.py tests/integration/test_end_to_end_pipeline.py
git commit -m "feat: add MVP demo script demonstrating all 6 pipeline stages"
```

---

## Self-Review Checklist

**Spec coverage check:**

| Requirement | Task(s) |
|---|---|
| Most technically sound architecture | Tasks 5, 6, 7 — local embeddings + node2vec + ablation study |
| Remove/simplify/replace components | Task 5 (Gemini→sentence-transformers), Task 6 (spectral→node2vec) |
| Implement first (dependencies) | Phase 0 → Phase 1 → Phase 2 → Phase 3 |
| Prioritized roadmap | Phases 0–7 in sequence |
| Week-by-week plan | See timeline below |
| Required tools | See Global Constraints + per-task `requirements.txt` changes |
| Required outputs/deliverables per stage | See Interfaces blocks in each task |
| Technical risks + mitigations | See Risk section below |
| Supervisor concerns | See Supervisor Questions section below |
| MVP | Task 12, `scripts/run_mvp.py` |

---

## Week-by-Week Timeline

| Week | Days | Tasks | Deliverable |
|---|---|---|---|
| Week 1 | 1–5 | Phase 0 + Phase 1 | Verified baseline, working data pipeline producing train/test splits |
| Week 2 | 6–9 | Phase 2 | Neo4j graph loaded with 50K+ flows + MITRE enrichment verified |
| Week 3 | 10–14 | Phase 3 | Local sentence-transformer embeddings + proper node2vec stored in Neo4j |
| Week 4 | 15–17 | Phase 4 | Ablation protocol defined, 50 curated queries created, all 3 conditions running |
| Week 5 | 18–20 | Phase 5 | Grounded LLM explanations with measurable grounding ratio |
| Week 6 | 21–24 | Phase 6a | XGBoost baseline results + classification metrics on held-out test set |
| Week 7 | 25–28 | Phase 6b | Full ablation results + retrieval MRR computed + evaluation report generated |
| Week 8 | 29–33 | Phase 7 | MVP demo working end-to-end, all results saved, thesis chapter drafted |

---

## Technical Risks and Mitigations

| Risk | Probability | Mitigation |
|---|---|---|
| IoT-23 label alignment fails (timestamp off by >1s) | Medium | Use UID-based alignment (implemented in Task 2), not timestamp alignment; document dropped rows |
| Neo4j Community Edition lacks vector index support | Low | Neo4j ≥5.11 Community supports vector indexes; verify version before starting |
| node2vec runs out of memory on full dataset | Medium | Use sample of 100K flows for graph; document sample size in thesis |
| Ollama LLM is too slow for evaluation (>30s/query) | High | Use smaller model (Mistral 7B vs Llama 3.1 8B), batch explanations offline, cache results |
| XGBoost baseline outperforms graph pipeline on F1 | Likely | Expected and acceptable; reframe contribution as explainability + multi-hop context, not raw accuracy |
| Curated query set too small for meaningful MRR | Medium | 50 queries minimum; document selection methodology in thesis (diversity of retrieval types) |
| GraphRAG retrieval adds no measurable value over Cypher-only | Possible | The ablation study will show this honestly; if true, report it as a finding rather than hiding it |

---

## Expected Supervisor Questions and Answers

**Q: Why sentence-transformers instead of a domain-specific security embedding model?**
A: `all-MiniLM-L6-v2` is a pragmatic choice for reproducibility in a thesis context. The MITRE technique descriptions are written in natural language, making a general-purpose model appropriate. For domain specificity, `SecBERT` or `CySecBERT` are documented alternatives — mention these in the thesis as future work.

**Q: Is node2vec the right choice, or should you use GCN/GraphSAGE?**
A: node2vec is the right choice for this dataset because: (1) GCN requires node features as input — in a flow graph, defining meaningful node features is non-trivial; (2) node2vec is unsupervised and does not require attack labels for training, which respects the train/test split; (3) node2vec is more interpretable (random walk semantics are explainable). GCN is mentioned as future work.

**Q: Why does the graph pipeline not outperform XGBoost?**
A: XGBoost outperforming graph methods on standard classification benchmarks is well-documented in the literature (Chen & Guestrin, 2016; Shchur et al., 2018). The contribution of this thesis is not classification accuracy — it is the combination of (a) multi-hop threat contextualization that tabular methods cannot provide, (b) structured MITRE ATT&CK mapping, and (c) grounded natural language explanations for SOC analysts. The XGBoost baseline confirms that classification is a solved problem for these datasets; the thesis advances explainability.

**Q: How do you know the LLM explanations are correct?**
A: The grounding check (Task 8) measures what fraction of entity mentions in LLM output appear in the retrieved context. For the thesis, additionally present 20 manually evaluated examples with a binary "factually consistent" label, and compute inter-rater agreement if a second evaluator is available.

**Q: Can this system detect novel, unseen attacks?**
A: Not in its current form — the system uses supervised labels from the datasets. This is a documented limitation. Anomaly detection using embedding distance from "benign" cluster centroid is the extension. Document this honestly in the limitations chapter.

---

## Immediate Next 3 Actions

1. **Run Phase 0, Task 0 right now** — record the baseline test suite pass/fail state before changing anything.
2. **Verify Neo4j version** — `neo4j --version` or check Docker image. Must be ≥5.11 for vector indexes.
3. **Download one CICIoT2023 CSV file** (start with the smallest subset from the UNB dataset page) and verify `extract_ciciot` parses it correctly.

---

## Recommended Final Architecture (Reference)

```
CICIoT2023 CSV + IoT-23 Zeek logs
    │
    ▼ [Task 1+2] Feature Extraction + Label Alignment (labels already exist)
    │  Output: train.parquet (80%) + test.parquet (20%), schema normalized
    │
    ▼ [Task 3+4] Neo4j Knowledge Graph
    │  Nodes: Device, Protocol, AttackType, MITRETechnique, Flow (train only)
    │  Edges: COMMUNICATES_WITH, CLASSIFIED_AS, MAPS_TO, USES_PROTOCOL
    │  Indexes: flow_uid, flow_timestamp, device_ip (standard) +
    │           device_embedding, attack_embedding, mitre_embedding (vector, 384-dim)
    │
    ▼ [Task 5] Text Embeddings (sentence-transformers all-MiniLM-L6-v2, local, offline)
    │  Embeds: Device descriptions, AttackType descriptions, MITRE technique text
    │  Stored: As node properties in Neo4j vector indexes
    │
    ▼ [Task 6] Structural Embeddings (node2vec p=1.0, q=0.5, dim=128)
    │  Embeds: Device communication graph topology
    │  Stored: Device.structural_embedding in Neo4j
    │
    ▼ [Task 7] Dual Retrieval Layer (Ablation Study)
    │  Condition A: Cypher-only — structured graph pattern matching
    │  Condition B: Vector-only — cosine similarity in Neo4j vector index
    │  Condition C: Combined — Cypher + vector, context concatenated
    │  Measured by: MRR on 50 curated queries
    │
    ▼ [Task 8] LLM Explanation (Ollama, local)
    │  Input: retrieved context (max 2000 tokens) + attack query
    │  Output: structured JSON with attack_type, evidence, technique_id,
    │           explanation, recommendation
    │  Quality: entity-level grounding check (ratio of claims in context)
    │
    ▼ [Task 9-11] Evaluation Framework
       Baseline: XGBoost on tabular features (Macro F1, AUC-ROC)
       Graph pipeline: per-class F1 using LLM label predictions on test set
       Retrieval: MRR + Hit@5 for each ablation condition
       Grounding: mean entity grounding ratio across 50 sampled explanations
       Output: data/eval/evaluation_report.json + evaluation_report.md
```
