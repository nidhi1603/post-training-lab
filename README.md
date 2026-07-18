# post-training-lab

A controlled study of **SFT vs DPO vs GRPO** for small-model **code repair**, with a
first-class **evaluation** track. We take Qwen2.5-Coder-1.5B-Instruct, teach it to fix
buggy Python three ways, and measure every step on **HumanEvalFix** (OctoPack, arXiv
2308.07124) using the paper's own protocol — aiming to beat a 16B flagship (OctoCoder,
~30.4% pass@1) at **1.5B**, then prove the gains are real with a random-reward control,
three seeds per arm, and a cross-family rerun on Llama-3.2-3B-Instruct.

The full plan lives in [`RL_Project_Master_Workflow.md`](RL_Project_Master_Workflow.md).
Keep it open while you work.

**Honest novelty statement:** we are *not* the first to run RL with execution rewards
on code repair — Repair-R1 (arXiv 2507.22853) did GRPO on exactly this model and is our
closest prior art and baseline. Our contribution is the **controlled three-arm
comparison under matched budgets**, the **cross-family validation** (Spurious Rewards,
arXiv 2506.10947, in the code domain), and the **evaluation rigor**.

## Repo layout

```
post-training-lab/
├── RL_Project_Master_Workflow.md   the frozen plan (source of truth)
├── EVAL_PROTOCOL.md                the frozen ruler — filled & committed in Phase 1
├── eval/                           the evals deliverable (Phase 7)
│   ├── pass_at_k.py                unbiased pass@k + clustered CIs        [done, tested]
│   ├── stats.py                    McNemar + paired bootstrap + Holm      [done, tested]
│   ├── taxonomy.json               OctoPack Table 15 bug taxonomy         [done]
│   ├── taxonomy_breakdown.py       per-category pass@k table              [done, tested]
│   └── contamination_report.md     n-gram + embedding audit               [Phase 2]
├── src/
│   ├── reward.py                   GRPO reward w/ CoRPO invariant         [done, tested]
│   └── variance_gate.py            GRPO pre-flight signal gate            [done, tested]
├── tests/                          57 tests, all green — run before any GPU
├── docs/
│   ├── EVALS_PLAYBOOK.md           interview crosswalk                    [done]
│   └── hacking_log.md              reward-hacking war log                 [fill in Phase 5]
├── data/                           audited datasets (git-ignored; see README)
└── notebooks/                      Colab notebooks (training lives here)
```

`[done]` items are implemented and unit-tested now — the whole eval + reward layer is
laptop-runnable and green before the first GPU hour. Training happens in Colab.

## Quickstart (local, no GPU)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m pytest -q          # 57 passed
```

The reward invariant and the pass@k math are proven here, not on a GPU.

## Ground rules (from the master workflow — violating any invalidates the study)

1. The ruler is **frozen** before training (`EVAL_PROTOCOL.md`, never edited after).
2. **Nothing** derived from HumanEval enters training data — enforced by the Phase-2 audit.
3. The held-out benchmark is touched **only at milestones**; daily decisions use the dev slice.
4. **Matched budgets** across arms.
5. **Same decode settings** for every headline number (temp 0.2, top_p 0.95, n=20, pass@1).
6. Correctness graded by **execution only** — no LLM judge in the correctness pipeline.
7. **Report what happened** — failed runs and hacked rewards are content, not embarrassments.

## Compute budget tracker

Colab Pro ≈ 300 units. Plan ≈ 175. Update this table as you burn units.

| Phase | Budgeted units | Spent | Notes |
|---|---|---|---|
| 0 Setup / Milestone 0 | ~3 | ~3 (2026-07-15) | Unsloth GRPO notebook unchanged — 250 steps, T4, 1h40m |
| 1 Baseline (Qwen + Llama) | ~15 | ~10–15 est. (Qwen done 2026-07-15; Llama pending) | L4; n=20 each; Qwen pass@1 = 17.59% |
| 2 Data pipeline | ~10 + API | | teacher-model API separate |
| 3 SFT ×3 seeds | ~15 | | |
| 4 DPO ×3 seeds | ~10 | | |
| 5 GRPO ×3 seeds | ~60 | | the main event |
| 6 Controls + Llama rerun | ~50 | | random-reward + cross-family |
| 7 Final eval | ~15 | | one-shot held-out |
| **Total** | **~178** | | overflow → Modal / Lightning free tiers |

## Status

**Phase 0 complete.** **Phase 1 in progress:** Qwen baseline measured 2026-07-15 —
**pass@1 = 17.59%** (pass@10 = 23.50%) on `humanevalfixtests-python`, full frozen
protocol, harness commit `8fc5bae`. **Target locked per the pre-committed gate: beat
OctoCoder-16B (30.4%) at 1.5B; stretch GPT-4 (~47%).** Remaining in Phase 1: Llama-3.2-3B
baseline (same notebook, 3 config changes), then freeze `EVAL_PROTOCOL.md`. Phase 2 kickoff:
raw-generation audit of the baseline failures + the A1 mutation pipeline.

## License

Apache-2.0 (matches the Qwen2.5-Coder base model). See [`LICENSE`](LICENSE).
