# LLM-as-Judge Relevance Evaluation

**Evaluation type:** Automated LLM-as-judge (NOT human evaluation)
**Judge model:** claude-opus-4-8 (Anthropic), accessed via Claude Code
**Date:** 2026-06-22
**Queries:** 20 (subset of the 50-query ablation benchmark, 2-3 per retrieval type)
**Conditions:** CYPHER_ONLY, VECTOR_ONLY, COMBINED

## Methodology

For each of 20 benchmark queries, the judge was shown the context retrieved by
each of the three ablation conditions and assigned a 1-5 relevance score using
a fixed rubric. The COMBINED context is exactly CYPHER_ONLY + VECTOR_ONLY
concatenated (verified programmatically across all 20 queries). Scores measure
how well the retrieved context supports answering the query.

**Rubric:**

| Score | Meaning |
|-------|---------|
| 5 | Directly answers the query; entities and details exactly right |
| 4 | Mostly relevant; answers the core question with minor gaps |
| 3 | Partially relevant; useful info but key details missing/off-topic |
| 2 | Marginally relevant; mostly off-topic but something related |
| 1 | Not relevant; context does not help answer the query |

The full per-query scores and rationales are in `llm_judge_scores.csv`; the
auditable judge record (scores embedded as data) is `scripts/llm_judge_eval.py`.

## Results

| Condition | Mean | Median | Min | Max |
|-----------|------|--------|-----|-----|
| CYPHER_ONLY | 2.75 | 2.5 | 1 | 5 |
| VECTOR_ONLY | 2.50 | 2.0 | 1 | 5 |
| **COMBINED** | **3.40** | **3.0** | 2 | 5 |

- COMBINED scored >= CYPHER_ONLY on **20/20** queries (strictly higher on 10).
- COMBINED scored >= VECTOR_ONLY on **20/20** queries.

### Statistical significance

- **Friedman test** (3 paired conditions): chi-square = 15.44, **p = 0.00044** -
  a statistically significant difference exists across conditions.
- **Wilcoxon signed-rank post-hoc:**
  - COMBINED vs CYPHER_ONLY: W = 0.0, **p = 0.0030** (significant)
  - COMBINED vs VECTOR_ONLY: W = 0.0, **p = 0.0009** (significant)
  - CYPHER_ONLY vs VECTOR_ONLY: W = 34.0, p = 0.412 (not significant)

## Interpretation

The qualitative LLM-judge evaluation **converges with the quantitative ablation
study**: COMBINED retrieval is judged significantly more relevant than either
single-modality condition, while CYPHER_ONLY and VECTOR_ONLY are statistically
indistinguishable from each other. This is the identical ordering and
significance pattern found for the quantitative result-count metric
(COMBINED > {CYPHER, VECTOR}; CYPHER ~ VECTOR), providing convergent validity.

**Where each modality is strong/weak (from per-query rationales):**

- **VECTOR_ONLY** excels on *descriptive* queries (attack patterns, MITRE
  tactics, Mirai behaviour) where semantic similarity surfaces the right attack
  descriptions; it fails on *device-specific* queries because device data is not
  in the attack-description embedding space.
- **CYPHER_ONLY** excels on *structured* queries that match a query template
  (dataset comparison, DoS technique mapping) but degrades when the template
  router picks a sub-optimal template (e.g. returning a device sample instead of
  a total count) or when the requested concept has no KG mapping (brute force).
- **COMBINED** wins by union: it covers descriptive *and* structured queries,
  and shows genuine complementarity on hybrid queries (e.g. "scanner devices" =
  device list from Cypher + scan-technique semantics from Vector).

## Limitations

- A single LLM judge has known biases (e.g., possible verbosity preference).
  Scores are deterministic and reproducible given the fixed inputs and rubric,
  but represent automated, not human, ground truth.
- Establishing inter-rater reliability would require a second independent judge
  (a second LLM or a human annotator) and a kappa/correlation analysis.
- The mean scores (~2.5-3.4 / 5) are moderate, reflecting real retriever
  weaknesses (fixed Cypher templates, device data absent from vector space) that
  are documented per-query rather than hidden.
