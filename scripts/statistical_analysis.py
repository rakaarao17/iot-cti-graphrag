#!/usr/bin/env python3
"""
Statistical analysis of GraphRAG ablation study results.

Tests whether retrieval condition (CYPHER_ONLY / VECTOR_ONLY / COMBINED) has
a significant effect on latency and context richness (result count).

Methods:
  - Kruskal-Wallis H-test (non-parametric one-way ANOVA)
  - Dunn post-hoc test with Bonferroni correction
  - Eta-squared effect size (eta2)
  - Descriptive statistics per condition and retrieval type

Usage:
    python scripts/statistical_analysis.py
    python scripts/statistical_analysis.py --input data/eval/ablation_results.json
    python scripts/statistical_analysis.py --output data/eval/statistical_report.md
"""

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import math
import statistics

try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("[WARN] scipy not installed -- using manual Kruskal-Wallis implementation")


# -- Statistical helpers -------------------------------------------------------

def kruskal_wallis(groups: list[list[float]]) -> tuple[float, float]:
    """Return (H statistic, p-value) for Kruskal-Wallis H-test."""
    if HAS_SCIPY:
        stat, p = scipy_stats.kruskal(*groups)
        return float(stat), float(p)
    # Manual implementation
    all_vals = [(v, g_idx) for g_idx, g in enumerate(groups) for v in g]
    all_vals.sort(key=lambda x: x[0])
    n = len(all_vals)
    ranks = list(range(1, n + 1))
    # Average ranks for ties
    i = 0
    while i < n:
        j = i
        while j < n and all_vals[j][0] == all_vals[i][0]:
            j += 1
        avg_rank = sum(ranks[i:j]) / (j - i)
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j
    group_rank_sums = [0.0] * len(groups)
    group_ns = [0] * len(groups)
    for (_, g_idx), rank in zip(all_vals, ranks):
        group_rank_sums[g_idx] += rank
        group_ns[g_idx] += 1
    H = (12 / (n * (n + 1))) * sum(
        rs ** 2 / ni for rs, ni in zip(group_rank_sums, group_ns)
    ) - 3 * (n + 1)
    # Tie correction
    tie_counts = {}
    for v, _ in all_vals:
        tie_counts[v] = tie_counts.get(v, 0) + 1
    C = 1 - sum(t ** 3 - t for t in tie_counts.values()) / (n ** 3 - n)
    H = H / C if C > 0 else H
    k = len(groups)
    # p-value from chi-squared distribution with k-1 df
    if HAS_SCIPY:
        p = float(scipy_stats.chi2.sf(H, df=k - 1))
    else:
        p = float("nan")  # chi2 CDF not easily done without scipy
    return H, p


def dunn_posthoc(groups: list[list[float]], labels: list[str]) -> dict:
    """
    Dunn's post-hoc pairwise test after Kruskal-Wallis.
    Returns dict of {(label_a, label_b): {"z": ..., "p_raw": ..., "p_adj": ...}}.
    """
    all_vals = [(v, g_idx) for g_idx, g in enumerate(groups) for v in g]
    all_vals.sort(key=lambda x: x[0])
    n = len(all_vals)

    # Assign average ranks (with tie handling)
    ranks = []
    i = 0
    sorted_vals = [v for v, _ in all_vals]
    while i < n:
        j = i
        while j < n and sorted_vals[j] == sorted_vals[i]:
            j += 1
        avg = (i + 1 + j) / 2  # average 1-based rank
        ranks += [avg] * (j - i)
        i = j

    group_ranks: list[list[float]] = [[] for _ in groups]
    for (_, g_idx), rank in zip(all_vals, ranks):
        group_ranks[g_idx].append(rank)

    # Tie correction factor
    tie_counts: dict[float, int] = {}
    for v in sorted_vals:
        tie_counts[v] = tie_counts.get(v, 0) + 1
    C = sum(t ** 3 - t for t in tie_counts.values())

    results = {}
    pairs = list(combinations(range(len(groups)), 2))
    for a, b in pairs:
        na, nb = len(group_ranks[a]), len(group_ranks[b])
        mean_ra = sum(group_ranks[a]) / na
        mean_rb = sum(group_ranks[b]) / nb
        # Standard error
        se = math.sqrt(
            (n * (n + 1) / 12 - C / (12 * (n - 1))) * (1 / na + 1 / nb)
        )
        z = (mean_ra - mean_rb) / se if se > 0 else 0.0
        if HAS_SCIPY:
            p_raw = float(2 * scipy_stats.norm.sf(abs(z)))
        else:
            p_raw = float("nan")
        results[(labels[a], labels[b])] = {"z": z, "p_raw": p_raw}

    # Bonferroni correction
    m = len(pairs)
    for key in results:
        p_raw = results[key]["p_raw"]
        results[key]["p_adj"] = min(p_raw * m, 1.0)

    return results


def eta_squared(H: float, k: int, n: int) -> float:
    """Eta-squared effect size from Kruskal-Wallis H statistic."""
    return (H - k + 1) / (n - k)


def descriptive(values: list[float]) -> dict:
    if not values:
        return {}
    return {
        "n": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
    }


# -- Data loading --------------------------------------------------------------

def load_results(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def group_by_condition(results: list[dict], metric: str) -> dict[str, list[float]]:
    grouped: dict[str, list[float]] = {}
    for r in results:
        cond = r["condition"]
        val = r.get(metric)
        if val is None and metric == "result_count":
            val = len(r.get("results", []))
        if val is not None:
            grouped.setdefault(cond, []).append(float(val))
    return grouped


# -- Report generation ---------------------------------------------------------

def significance_stars(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def run_analysis(results: list[dict]) -> dict:
    CONDITIONS = ["cypher_only", "vector_only", "combined"]

    analysis: dict = {}

    for metric, label in [("latency_ms", "Latency (ms)"), ("result_count", "Result count")]:
        by_cond = group_by_condition(results, metric)
        # Ensure consistent order, skip missing conditions
        present = [c for c in CONDITIONS if c in by_cond]
        groups = [by_cond[c] for c in present]

        desc = {c: descriptive(by_cond.get(c, [])) for c in present}

        if len(groups) >= 2 and all(len(g) >= 2 for g in groups):
            H, p = kruskal_wallis(groups)
            n_total = sum(len(g) for g in groups)
            eta2 = eta_squared(H, len(groups), n_total)
            dunn = dunn_posthoc(groups, present)
        else:
            H, p, eta2, dunn = float("nan"), float("nan"), float("nan"), {}

        analysis[metric] = {
            "label": label,
            "conditions": present,
            "descriptive": desc,
            "kruskal_wallis": {"H": H, "p": p},
            "eta_squared": eta2,
            "dunn": dunn,
        }

    # Per retrieval-type breakdown for latency
    retrieval_types = {}
    by_type = {}
    for r in results:
        rt = r.get("retrieval_type", "unknown")
        cond = r["condition"]
        lat = r.get("latency_ms")
        if lat is not None:
            by_type.setdefault(rt, {}).setdefault(cond, []).append(float(lat))
            retrieval_types[rt] = True

    analysis["by_retrieval_type"] = by_type

    # Condition ranking
    lat_desc = analysis["latency_ms"]["descriptive"]
    cond_order = sorted(lat_desc.keys(), key=lambda c: lat_desc[c].get("median", 9e9))
    analysis["condition_ranking_by_latency"] = cond_order

    return analysis


def render_markdown(analysis: dict, n_queries: int, n_conditions: int) -> str:
    lines = [
        "# GraphRAG Ablation Study -- Statistical Analysis",
        "",
        "**Method:** Kruskal-Wallis H-test with Dunn post-hoc (Bonferroni correction)",
        f"**Queries:** {n_queries}  |  **Conditions:** {n_conditions}  |  **Total observations:** {n_queries * n_conditions}",
        "",
        "---",
        "",
    ]

    for metric_key in ["latency_ms", "result_count"]:
        m = analysis[metric_key]
        lines += [f"## {m['label']}", ""]

        # Descriptive table
        lines += [
            "### Descriptive Statistics",
            "",
            "| Condition | N | Mean | Median | Std Dev | Min | Max |",
            "|-----------|---|------|--------|---------|-----|-----|",
        ]
        for cond in m["conditions"]:
            d = m["descriptive"][cond]
            unit = " ms" if metric_key == "latency_ms" else ""
            lines.append(
                f"| {cond} | {d['n']} | {d['mean']:.1f}{unit} | "
                f"{d['median']:.1f}{unit} | {d['stdev']:.1f}{unit} | "
                f"{d['min']:.1f}{unit} | {d['max']:.1f}{unit} |"
            )
        lines.append("")

        # KW test
        kw = m["kruskal_wallis"]
        eta2 = m["eta_squared"]
        sig = significance_stars(kw["p"]) if not math.isnan(kw["p"]) else "?"
        lines += [
            "### Kruskal-Wallis H-test",
            "",
            f"- **H statistic:** {kw['H']:.4f}",
            f"- **p-value:** {kw['p']:.4f} {sig}",
            f"- **Effect size (eta2):** {eta2:.4f}",
            "",
            "_Significance: \\*\\*\\* p<0.001, \\*\\* p<0.01, \\* p<0.05, ns = not significant_",
            "",
        ]

        # Effect size interpretation
        if not math.isnan(eta2):
            if eta2 < 0.01:
                interp = "negligible"
            elif eta2 < 0.06:
                interp = "small"
            elif eta2 < 0.14:
                interp = "medium"
            else:
                interp = "large"
            lines.append(f"_Effect size interpretation: **{interp}** (eta2 = {eta2:.4f})_")
            lines.append("")

        # Dunn post-hoc
        if m["dunn"]:
            lines += [
                "### Dunn Post-hoc Pairwise Comparisons (Bonferroni-adjusted)",
                "",
                "| Pair | z statistic | p (raw) | p (adjusted) | Significant? |",
                "|------|-------------|---------|--------------|--------------|",
            ]
            for (a, b), vals in m["dunn"].items():
                sig_pair = "Yes" if vals["p_adj"] < 0.05 else "No"
                lines.append(
                    f"| {a} vs {b} | {vals['z']:.3f} | {vals['p_raw']:.4f} | "
                    f"{vals['p_adj']:.4f} | {sig_pair} |"
                )
            lines.append("")

    # Latency ranking
    rank = analysis["condition_ranking_by_latency"]
    lines += [
        "## Condition Ranking by Median Latency (fastest first)",
        "",
    ]
    lat_desc = analysis["latency_ms"]["descriptive"]
    for i, cond in enumerate(rank, 1):
        d = lat_desc[cond]
        lines.append(f"{i}. **{cond}** -- median {d['median']:.0f} ms, mean {d['mean']:.0f} ms")
    lines.append("")

    # Per retrieval-type table
    by_rt = analysis["by_retrieval_type"]
    if by_rt:
        lines += [
            "## Latency by Retrieval Type",
            "",
            "| Retrieval Type | cypher_only (med ms) | vector_only (med ms) | combined (med ms) |",
            "|----------------|---------------------|---------------------|------------------|",
        ]
        for rt in sorted(by_rt.keys()):
            row = by_rt[rt]
            def med(lst):
                return f"{statistics.median(lst):.0f}" if lst else "--"
            lines.append(
                f"| {rt} | {med(row.get('cypher_only', []))} | "
                f"{med(row.get('vector_only', []))} | {med(row.get('combined', []))} |"
            )
        lines.append("")

    lines += [
        "---",
        "",
        "_Generated by `scripts/statistical_analysis.py`_",
    ]
    return "\n".join(lines)


# -- Main ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Statistical analysis of ablation results")
    parser.add_argument("--input", default="data/eval/ablation_results.json",
                        help="Path to ablation_results.json")
    parser.add_argument("--output", default="data/eval/statistical_report.md",
                        help="Path for the Markdown report output")
    parser.add_argument("--json-output", default="data/eval/statistical_report.json",
                        help="Path for the JSON report output")
    args = parser.parse_args()

    print("=" * 60)
    print("  GraphRAG Statistical Analysis")
    print("=" * 60)

    if not Path(args.input).exists():
        print(f"[FAIL] Input file not found: {args.input}")
        sys.exit(1)

    results = load_results(args.input)
    print(f"\n[OK] Loaded {len(results)} ablation records from {args.input}")

    conditions = sorted(set(r["condition"] for r in results))
    query_ids = sorted(set(r["query_id"] for r in results))
    print(f"  Conditions: {conditions}")
    print(f"  Queries: {len(query_ids)}")

    # Add result_count field for analysis
    for r in results:
        if "result_count" not in r:
            r["result_count"] = len(r.get("results", []))

    # Attach retrieval_type from queries if available
    queries_path = Path("data/eval/curated_queries.json")
    if queries_path.exists():
        with open(queries_path) as f:
            queries = {q["id"]: q for q in json.load(f)}
        for r in results:
            qmeta = queries.get(r["query_id"], {})
            r.setdefault("retrieval_type", qmeta.get("retrieval_type", "unknown"))

    analysis = run_analysis(results)

    # Print summary to console
    print("\n--- Latency Summary ---")
    lat = analysis["latency_ms"]
    for cond in lat["conditions"]:
        d = lat["descriptive"][cond]
        print(f"  {cond:15s}  median={d['median']:.0f}ms  mean={d['mean']:.0f}ms  n={d['n']}")

    kw = lat["kruskal_wallis"]
    if not math.isnan(kw["H"]):
        sig = significance_stars(kw["p"])
        print(f"\n  Kruskal-Wallis: H={kw['H']:.3f}, p={kw['p']:.4f} {sig}")
        print(f"  Effect size eta2={analysis['latency_ms']['eta_squared']:.4f}")

    print("\n--- Result Count Summary ---")
    rc = analysis["result_count"]
    for cond in rc["conditions"]:
        d = rc["descriptive"][cond]
        print(f"  {cond:15s}  median={d['median']:.1f}  mean={d['mean']:.1f}  n={d['n']}")

    kw2 = rc["kruskal_wallis"]
    if not math.isnan(kw2["H"]):
        sig2 = significance_stars(kw2["p"])
        print(f"\n  Kruskal-Wallis: H={kw2['H']:.3f}, p={kw2['p']:.4f} {sig2}")
        print(f"  Effect size eta2={analysis['result_count']['eta_squared']:.4f}")

    # Write reports
    md = render_markdown(analysis, len(query_ids), len(conditions))
    Path(args.output).write_text(md, encoding="utf-8")
    print(f"\n[OK] Markdown report written to {args.output}")

    # Serialize analysis (convert tuple keys to strings for JSON)
    def make_serializable(obj):
        if isinstance(obj, dict):
            return {str(k): make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [make_serializable(i) for i in obj]
        if isinstance(obj, float) and math.isnan(obj):
            return None
        return obj

    json_out = make_serializable(analysis)
    Path(args.json_output).write_text(
        json.dumps(json_out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[OK] JSON report written to {args.json_output}")

    print("\n" + "=" * 60)
    print("  Analysis complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
