#!/usr/bin/env python3
"""
LLM-as-judge relevance evaluation for the IoT CTI GraphRAG ablation study.

METHODOLOGY (report this honestly in the thesis):
  This is an AUTOMATED LLM-as-judge evaluation, NOT human evaluation.
  Judge model : claude-opus-4-8 (Anthropic), accessed via Claude Code
  Date        : 2026-06-22
  Protocol    : For each of 20 benchmark queries, the judge was shown the
                context retrieved by each condition (CYPHER_ONLY, VECTOR_ONLY,
                COMBINED) and assigned a 1-5 relevance score using the rubric
                below. COMBINED context is exactly CYPHER_ONLY + VECTOR_ONLY
                concatenated (verified programmatically). Scores reflect how
                well the retrieved context supports answering the query.

  Rubric (1-5):
    5 - Directly answers the query; entities and details are exactly right
    4 - Mostly relevant; answers the core question with minor gaps
    3 - Partially relevant; some useful info but key details missing/off-topic
    2 - Marginally relevant; mostly off-topic but contains something related
    1 - Not relevant; context does not help answer the query at all

  LIMITATION: A single LLM judge has known biases (e.g., verbosity preference).
  Scores are deterministic given the fixed inputs and documented rubric, so the
  evaluation is reproducible but should be read as automated, not human, ground
  truth. Inter-rater reliability would require a second independent judge.

The judge scores + rationales are embedded below as data so this file is the
auditable record. Running it (re)writes the CSV and prints summary statistics.

Usage:
    python scripts/llm_judge_eval.py
    python scripts/llm_judge_eval.py --output data/eval/llm_judge_scores.csv
"""

import argparse
import csv
import json
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "data" / "eval" / "llm_judge_scores.csv"

JUDGE_MODEL = "claude-opus-4-8"
JUDGE_DATE = "2026-06-22"

# (query_id, query_text, retrieval_type,
#  cypher_score, vector_score, combined_score,
#  cypher_note, vector_note, combined_note)
JUDGMENTS = [
    ("q001", "What attack types has the device at 192.168.1.195 been involved in?", "device_lookup",
     2, 2, 3,
     "Lists all attack types with counts but not filtered to the specified device 192.168.1.195.",
     "Generic recon/DoS attack descriptions; no device data, device IP absent.",
     "Union gives a fuller attack-type picture but still lacks device-specific filtering."),
    ("q023", "Which devices communicated on port 23 telnet and were flagged as malicious?", "device_lookup",
     2, 1, 2,
     "Returns one aggregate device (0.0.0.0) with its attacks; no port-23/telnet filtering.",
     "Attack descriptions only; no device or port information.",
     "Adds attack context to the single device but no port-level evidence."),
    ("q002", "Which devices communicated with external C&C infrastructure?", "relationship_traversal",
     3, 1, 3,
     "Returns 20 real external-IP devices with role 'both' and degree; plausible C&C peers though not labelled C&C.",
     "Attack descriptions only; no devices.",
     "Device list (useful) plus attack semantics; C&C not explicitly labelled."),
    ("q020", "Which devices acted as both source and destination of malicious traffic?", "relationship_traversal",
     2, 1, 2,
     "Picked top_attackers (1 device) instead of device_profile's role 'both'; partial match.",
     "Attack descriptions only; no source/destination role data.",
     "No role-based evidence beyond the single aggregate device."),
    ("q003", "What MITRE ATT&CK techniques are associated with Mirai botnet?", "mitre_lookup",
     4, 4, 5,
     "mitre_mapping includes T1584 (Compromise Infrastructure) mapped to the three Mirai attacks - correct.",
     "Top-3 results are Mirai attacks with T1584; directly on point.",
     "Both the technique mapping and the Mirai attack descriptions present - complete."),
    ("q018", "Which MITRE ATT&CK techniques map to denial of service attacks?", "mitre_lookup",
     5, 4, 5,
     "T1498 (Network DoS) and T1499 (Endpoint DoS) returned exactly - precise answer.",
     "Top results are DDoS/DoS attacks carrying T1498/T1499; relevant.",
     "Precise technique mapping plus supporting attack list."),
    ("q032", "Which MITRE ATT&CK techniques are associated with brute force attacks?", "mitre_lookup",
     2, 2, 2,
     "Returns DoS/scan/infra techniques; no brute-force technique (T1110) exists in the KG mapping.",
     "Recon/DoS/MITM descriptions; no brute-force technique surfaced.",
     "Neither modality surfaces a brute-force mapping - genuine coverage gap."),
    ("q004", "Describe the DDoS-TCP_Flood attack pattern", "attack_description",
     3, 4, 4,
     "DDoS-TCP_Flood appears in the attack list with count but no descriptive pattern.",
     "Top hit DDoS-TCP_Flood (0.88) with MITRE T1498/Impact and related DDoS - descriptive.",
     "Count plus description together give a fuller pattern picture."),
    ("q017", "What are the characteristics of a Slowloris HTTP attack?", "attack_description",
     2, 4, 4,
     "DDoS-SlowLoris present in full list but only as name+count.",
     "Top hit DDoS-SlowLoris (0.81) with T1498 plus DoS-HTTP_Flood - on point.",
     "Vector description carries it; Cypher adds frequency context."),
    ("q035", "Describe the impact of SYN flood attacks on network infrastructure", "attack_description",
     3, 4, 4,
     "DDoS-SYN_Flood and DoS-SYN_Flood in list with counts; no impact narrative.",
     "Top hits DDoS/DoS-SYN_Flood with Impact-tactic mapping - relevant.",
     "Counts plus impact-tactic descriptions combine well."),
    ("q005", "Which protocols are most commonly used in attacks?", "aggregation",
     2, 2, 2,
     "top_attackers returns a device+attack list; no protocol breakdown.",
     "Attack descriptions imply protocols but no explicit protocol aggregation.",
     "No protocol-level aggregation surfaced by either modality."),
    ("q015", "List the top 5 attack categories by total flow count", "aggregation",
     2, 2, 3,
     "network_summary gives only grand totals, not per-category ranking.",
     "Individual attacks with flow counts; categories inferable but unranked.",
     "Totals plus per-attack flows allow rough category inference."),
    ("q024", "What is the total number of unique devices in the dataset?", "aggregation",
     2, 1, 2,
     "Picked device_profile (a 20-device sample) instead of network_summary's devices=667770.",
     "Attack descriptions only; no device count.",
     "Still no clean total; network_summary template would have answered exactly."),
    ("q006", "Show me the most dangerous IoT devices by malicious traffic ratio", "device_ranking",
     3, 1, 3,
     "top_attackers ranks the most malicious device by flow count (proxy for danger), not ratio.",
     "Attack descriptions only; no devices or ratios.",
     "Device ranking present; ratio dimension still missing."),
    ("q016", "Which IoT devices have a malicious traffic ratio above 50 percent?", "device_ranking",
     3, 1, 3,
     "Returns the most malicious device but no ratio threshold filtering.",
     "Attack descriptions only; no device/ratio data.",
     "Device evidence without the ratio>50% filter."),
    ("q007", "What reconnaissance techniques are used by IoT malware?", "mitre_tactic",
     4, 5, 5,
     "mitre_mapping includes T1046 (Network Service Scanning) with the four Recon attacks.",
     "Top-4 are the Recon techniques with T1046 - exact match.",
     "Technique mapping plus recon descriptions - complete and precise."),
    ("q026", "Explain how Mirai botnet propagates through IoT networks", "mitre_tactic",
     1, 4, 4,
     "network_summary returns only totals; nothing about Mirai propagation.",
     "Top-3 Mirai attacks with T1584 Compromise Infrastructure - relevant to propagation.",
     "Vector carries the Mirai context; Cypher contributes little."),
    ("q009", "Which devices initiated UDP flood attacks?", "attack_device_join",
     2, 2, 3,
     "attack_types lists UDP floods with counts but no initiating devices.",
     "Top hits are UDP flood attacks but no device attribution.",
     "UDP attack context from both sides, still no explicit device->attack join."),
    ("q034", "Which devices acted as scanners probing multiple ports?", "attack_device_join",
     3, 3, 4,
     "device_profile returns 20 devices with degree but no scan attribution.",
     "Top hits Recon-PortScan/OSScan (T1046) capture scanning semantics; no devices.",
     "Genuine complementarity: device list (Cypher) + scan technique semantics (Vector)."),
    ("q011", "Compare attack distributions between IoT-23 and CICIoT datasets", "dataset_comparison",
     5, 2, 5,
     "dataset_comparison returns per-category counts for both CICIoT2023 and IoT-23 - direct answer.",
     "Attack descriptions only; no dataset-level comparison.",
     "Cypher fully answers the comparison; Vector adds minor attack colour."),
]

CONDITIONS = ["cypher_only", "vector_only", "combined"]


def write_csv(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "query_id", "query_text", "retrieval_type",
            "cypher_only_score", "vector_only_score", "combined_score",
            "cypher_only_notes", "vector_only_notes", "combined_notes",
            "judge_model", "judge_date", "evaluation_type",
        ])
        for row in JUDGMENTS:
            qid, qt, rt, cs, vs, ms, cn, vn, mn = row
            w.writerow([qid, qt, rt, cs, vs, ms, cn, vn, mn,
                        JUDGE_MODEL, JUDGE_DATE, "llm_as_judge"])


def summary() -> dict:
    cyp = [r[3] for r in JUDGMENTS]
    vec = [r[4] for r in JUDGMENTS]
    com = [r[5] for r in JUDGMENTS]
    return {
        "n_queries": len(JUDGMENTS),
        "cypher_only": {"mean": round(mean(cyp), 3), "median": median(cyp), "min": min(cyp), "max": max(cyp)},
        "vector_only": {"mean": round(mean(vec), 3), "median": median(vec), "min": min(vec), "max": max(vec)},
        "combined":    {"mean": round(mean(com), 3), "median": median(com), "min": min(com), "max": max(com)},
        "combined_wins_or_ties_vs_cypher": sum(1 for r in JUDGMENTS if r[5] >= r[3]),
        "combined_strictly_beats_cypher": sum(1 for r in JUDGMENTS if r[5] > r[3]),
        "combined_wins_or_ties_vs_vector": sum(1 for r in JUDGMENTS if r[5] >= r[4]),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="LLM-as-judge relevance evaluation")
    p.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = p.parse_args()

    out = Path(args.output)
    write_csv(out)
    s = summary()

    print(f"[OK] Wrote {len(JUDGMENTS)} judgments to {out}")
    print(f"[INFO] Judge: {JUDGE_MODEL} ({JUDGE_DATE}), type=llm_as_judge")
    print()
    print(f"{'Condition':<14} {'Mean':>6} {'Median':>7} {'Min':>4} {'Max':>4}")
    print("-" * 40)
    for cond in CONDITIONS:
        st = s[cond]
        print(f"{cond:<14} {st['mean']:>6} {st['median']:>7} {st['min']:>4} {st['max']:>4}")
    print()
    print(f"COMBINED >= CYPHER on {s['combined_wins_or_ties_vs_cypher']}/{s['n_queries']} queries "
          f"(strictly better on {s['combined_strictly_beats_cypher']})")
    print(f"COMBINED >= VECTOR on {s['combined_wins_or_ties_vs_vector']}/{s['n_queries']} queries")

    # Persist summary JSON alongside CSV
    summary_path = out.parent / "llm_judge_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)
    print(f"[OK] Summary stats -> {summary_path}")


if __name__ == "__main__":
    main()
