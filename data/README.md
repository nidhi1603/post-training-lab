# data/ — audited datasets (Phase 2)

Raw and interim data files are git-ignored (see root `.gitignore`); they live in Drive /
Hugging Face. This README documents what the folder should contain once Phase 2 is done.

## Target contents

| Item | Description | Balance / gate |
|---|---|---|
| `sft/` | Verified reasoning-distillation traces (`<think>` + fix, tests pass) | every example provably correct |
| `rl/` | RL training bugs with trustworthy tests | every test cleared the gold-sanity gate |
| `restraint/` | ~100 verified-clean functions (no bug) for the false-fix suite | — |
| `dev_slice/` | Fixed ~100 training-distribution bugs for checkpoint decisions | disjoint from train & benchmark |
| `splits.json` | train / dev / held-out sanity assignment, hashed | no overlap, enforced |

## Non-negotiable audits (Phase 2 gate)

1. **Gold-sanity gate** on every RL problem's tests: must PASS on the known-correct fix
   and FAIL on the buggy version (arXiv 2606.16062: ~25–28% of tasks in major RL code
   datasets accept incorrect patches). Discard problems that can't clear it.
2. **Restraint balance**: ≥15–20% clean examples ("no fix needed"). The cautionary tale:
   8.3% clean → a model that flagged defects on 77% of clean inputs.
3. **Diversity over multiplicity**: many different bugs beats many completions of one
   (AceReason-Nemotron, arXiv 2506.13284).
4. **Contamination audit**: see `../eval/contamination_report.md`. Clean before use.

## Sources

- CommitPackFT (OctoPack's own filtered commit data)
- `google/code_x_glue_cc_code_refinement`
- Teacher model for SFT distillation: Gemini (AI Studio) or DeepSeek. Only keep traces
  whose fix passes the tests.
