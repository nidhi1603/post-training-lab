# contamination_report.md (Phase 2, step 7)

**Gate:** this report must be committed and clean before any training data is used.
Nothing derived from HumanEval may enter training data — enforced here, not by intent.

Status: **NOT YET RUN** (Phase 2).

## Method (three layers)

1. **50-gram substring overlap** between every training example and every one of the
   164 benchmark problems (code-standard n-gram size). Flag any hit.
2. **Embedding near-duplicate check** for rephrased / logic-preserving leaks that
   n-grams miss (LLM Decontaminator, arXiv 2311.04850). Flag above a cosine threshold
   (record the threshold used).
3. **Function-name grep** for the HumanEval/HumanEvalFix function names in training data.

Anything flagged is **deleted** from training data. Record what was removed.

## Results

| Layer | Threshold / n | Train examples scanned | Flagged | Removed |
|---|---|---|---|---|
| 50-gram substring | 50 | | | |
| Embedding near-dup | cos ≥ TODO | | | |
| Function-name grep | — | | | |

## Optional: post-cutoff slice (Phase 7)

A LiveCodeBench-style slice of problems published *after* the base model's training
cutoff is contamination-proof by construction. Add if time permits and note the cutoff
date used.

## Sign-off

- [ ] All three layers run
- [ ] Flagged examples removed from `data/`
- [ ] Report committed with the commit hash of the cleaned dataset
