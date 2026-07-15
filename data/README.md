# data/ — audited datasets (Phase 2, per Amendment A1)

Raw and interim data files are git-ignored (see root `.gitignore`); they live in Drive /
Hugging Face. This README documents what the folder should contain once Phase 2 is done.
Data sources follow **Amendment A1 (2026-07-14)** in `../RL_Project_Master_Workflow.md`.

## Sources (A1)

| Source | Role | Notes |
|---|---|---|
| **MBPP+** (EvalPlus-augmented sanitized MBPP) | primary seed corpus: ~400 correct functions with strong tests | tests ~35× original MBPP; MBPP numbers can never be reported for these models |
| **CommitPackFT** (Python, single-function diffs) | real human bugs for diversity | teacher tests, gold-sanity gated |
| ~~code_x_glue_cc_code_refinement~~ | **CUT** | verified Java-only, abstracted identifiers — no Python exists in it |
| Teacher model | SFT traces, test generation, LLM bug injection | **DeepSeek** (licensing — Gemini outputs may not train public models) |

## The mutation pipeline (the backbone)

Correct function + tests → inject ONE bug → validated training problem.

- AST mutation operators mapped 1:1 to the OctoPack taxonomy: operator swap →
  *operator misuse*, identifier swap → *variable misuse*, constant perturbation →
  *value misuse*, statement deletion → *missing logic*, statement insertion →
  *excess logic*, call substitution → *function misuse*. Plus LLM-injected subtle bugs.
- **Equivalent-mutant rule:** every mutant must compile AND fail ≥1 test, else discard.
- **≤2 mutants per source function**; **split at FUNCTION level** (all mutants of one
  function in the same split — enforced by hashing the original function).
- Taxonomy-balanced, oversampling *excess-logic* (the benchmark's hardest category).
- **Visible/hidden test split:** K tests shown in the RL prompt, held-back tests join
  the reward — hardcoding visible tests earns nothing.

## Target contents

| Item | Description | Balance / gate |
|---|---|---|
| `sft/` | Verified reasoning-distillation traces (`<think>` + fix, tests pass) | every example provably correct; traces ≤512 think tokens |
| `rl/` | Mutation + real bugs with visible/hidden test pools | every test cleared the gold-sanity gate; every mutant fails ≥1 test |
| `restraint/` | Unmutated originals (verified-clean, tests attached) | free from the pipeline; ≥15–20% of training mix is clean |
| `dev_slice/` | Fixed ~100 training-distribution bugs for checkpoint decisions | function-level disjoint from train & benchmark |
| `splits.json` | train / dev / held-out sanity assignment, hashed at function level | no overlap, enforced |

## Non-negotiable audits (Phase 2 gate — unchanged)

1. **Gold-sanity gate** on every generated test: PASS on the known-correct fix, FAIL on
   the buggy version (arXiv 2606.16062: ~25–28% of tasks in major RL code datasets
   accept incorrect patches).
2. **Restraint balance**: ≥15–20% clean examples. The cautionary tale: 8.3% clean → a
   model that flagged defects on 77% of clean inputs.
3. **Diversity over multiplicity** (AceReason 2506.13284) — enforced by the ≤2-mutant cap.
4. **Contamination audit**: see `../eval/contamination_report.md` — now also runs over
   all MBPP-derived data. Clean before use.
