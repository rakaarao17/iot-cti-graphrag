# Evaluation Corrections (LLM Model Comparison)

*Date: 2026-06-25. Author: automated review during the post-submission hardening pass.*

This document records a methodological flaw found in the original local-LLM
comparison and the corrected evaluation that supersedes it. It is written to be
included (in summary) in the dissertation's methodology / threats-to-validity
section, because **finding and fixing this strengthens the work** — the corrected
result is verifiable by reading the model outputs directly.

## 1. The original result (now superseded)

`data/eval/comparison_report.md` ranked three local models by **grounding ratio**
(fraction of answer entities that appear in the retrieved context):

| Model | Original grounding | Original verdict |
|-------|--------------------|------------------|
| zeroday-phi3-ciciot-v2 | 0.949 | "best" |
| phi3 | 0.851 | 2nd |
| gemma4:e2b | 0.600 (10% errors) | "worst" |

## 2. Three flaws found

1. **Prompt format.** All models were called through `/api/generate` with a raw
   prompt, bypassing each model's chat template. Instruction-tuned models expect
   their template; the raw path degraded gemma4 (empty/error responses) and the
   fine-tuned model.
2. **A gameable metric.** Grounding scores a near-empty answer ~1.0 (few/no
   entities can be "ungrounded"). A model that says almost nothing wins.
3. **Task mismatch.** `zeroday-phi3-ciciot-v2` is a *classification* fine-tune.
   Asked to *explain*, its raw outputs are bare labels/counts, e.g. verbatim:
   `"Recon-PingSweep"`, `"DDoS-SynonymousIP_Flood, DDoS-ICMP_Flood, ..."`, `"1,930,568"`.
   These echo context labels, so they score grounding ~1.0 while containing no analysis.
   (Full text: `data/eval/model_readout.md`.)

## 3. The corrected evaluation

`scripts/run_model_comparison_fixed.py` (results in `corrected_comparison_report.md`):

- **Chat mode** (`/api/chat`) so each model gets its own template — fixes (1).
- **Usable-answer metric**: an answer counts only if it has >= 20 words AND a
  coherence score >= 0.6; otherwise its grounding contributes 0 — fixes (2).
- **Headline = usable-answer rate** (did the model actually produce a substantive,
  grounded answer), reported next to the old metric so the gap is visible — addresses (3).

### Corrected results (chat mode, n=20)

| Model | Usable rate | Eff. grounding | Coherence | Mean words | Old grounding |
|-------|-------------|----------------|-----------|------------|---------------|
| **phi3** | **1.00** | 0.94 | 0.98 | 173 | 0.94 |
| gemma4:e2b | 0.95 | 0.90 | 0.98 | 65 | 0.95 |
| zeroday-phi3-ciciot-v2 | 0.60 | 0.55 | 0.97 | 350 | 0.95 |

## 4. What changed and why it matters

- **The ranking reverses.** zeroday goes from "best" (0.949) to last (usable 0.60);
  gemma4 goes from "worst" to a strong second once given its proper template.
- **phi3 is the defensible winner** for threat *explanation* — 100% usable, well
  grounded, coherent — and this is confirmable by reading the outputs, not just a number.
- **zeroday is not a bad model** — it is mis-applied. It is a classifier; on its
  intended task it would likely excel. This is a task/tool-fit finding, not a quality ranking.

## 5. Honest take-away for the dissertation

The first metric (grounding alone) was insufficient: it rewarded brevity/echoing.
A defensible LLM evaluation for this task needs (a) per-model prompt templates,
(b) a substance gate (length + coherence) so empty answers cannot win, and ideally
(c) human or strong-judge reading of a sample. The corrected comparison applies
(a) and (b); the per-query text in `model_readout.md` supports (c).

Figures: `results/fig_corrected_comparison.png` (ranking reversal),
`results/fig_grounding_vs_tokens.png` (why grounding is gameable),
`results/fig_model_readout.png` (grounding vs coherence by model and mode).
