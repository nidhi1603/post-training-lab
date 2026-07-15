# notebooks/ — Colab training notebooks

Training runs in Colab (GPU); this repo holds the reproducible eval + reward layer.
Notebooks sync checkpoints to Drive `rl-post-training/` every run — Colab *will*
disconnect, and a run without checkpoint syncing is a run you will lose.

## Planned notebooks

| Notebook | Phase | Purpose | ~Units |
|---|---|---|---|
| `00_milestone0_grpo_smoke.ipynb` | 0 | Unsloth GRPO notebook unchanged; prove the machinery, name every reward column | ~3 |
| `01_baseline_eval.ipynb` | 1 | Qwen + Llama baseline pass@1 on HumanEvalFix, L4, n=20 | ~15 |
| `02_data_pipeline.ipynb` | 2 | Source, filter, distill, gold-sanity gate, contamination audit | ~10 + API |
| `03_sft.ipynb` | 3 | QLoRA SFT ×3 seeds; pick RL-init by pass@16 | ~15 |
| `04_dpo.ipynb` | 4 | Pairs from the verifier; DPO ×3 seeds | ~10 |
| `05_grpo.ipynb` | 5 | Dr.GRPO ×3 seeds, GSPO A/B; reward server; transcript reads | ~60 |
| `06_controls.ipynb` | 6 | Random-reward control + Llama cross-family rerun | ~50 |
| `07_final_eval.ipynb` | 7 | One-shot held-out table, all arms, CIs + taxonomy + restraint | ~15 |

## Conventions

- Import the tested modules from this repo (`eval/`, `src/`) — do NOT re-implement the
  reward or the pass@k math in a notebook cell. Clone the repo into the Colab session.
- Freeze eval decoding at temp 0.2 / top_p 0.95 / n=20 in every eval cell.
- Log units spent back into the README budget tracker after each run.
