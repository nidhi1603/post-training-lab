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
| 1 Baseline (Qwen + Llama) | ~15 | ~8–12 est. (both done; Llama gen took only ~37 min on L4) | Qwen 17.59% / Llama 29.94% pass@1 |
| 2 Data pipeline | ~10 + API | | teacher-model API separate |
| 3 SFT ×3 seeds | ~15 | | |
| 4 DPO ×3 seeds | ~10 | | |
| 5 GRPO ×3 seeds | ~60 | | the main event |
| 6 Controls + Llama rerun | ~50 | | random-reward + cross-family |
| 7 Final eval | ~15 | | one-shot held-out |
| **Total** | **~178** | | overflow → Modal / Lightning free tiers |

## Status

### 🏆 HEADLINE (2026-07-19): TARGET BEATEN — confirmed on 3 seeds

| model | pass@1 | pass@10 |
|---|---|---|
| Qwen2.5-Coder-1.5B base | 17.59% | 23.50% |
| **OctoCoder-16B (the paper's flagship — our locked target)** | **30.40%** | — |
| **ours: SFT v2, 3-seed mean** | **38.63% (sd 4.07)** | **48.66%** |
| ours: worst seed | 34.51% | 47.24% |
| ours: best seed | 42.65% | 50.21% |

A 1.5B model beats the 16B flagship by **+8.2 mean** (worst seed +4.1) under the
paper's own frozen protocol — no HumanEval-derived training data, contamination-
screened, pre-registered claim standard (mean AND every seed above target) met.
The winning intervention was **data**: a $0.34 LLM-self-broken, docstring-style
bug corpus (2,551 bugs), after the controlled study showed every RL arm tying
or nudging spuriously (random-reward control) at v0 data difficulty.

**Phases 0–1 COMPLETE (2026-07-18). Protocol FROZEN.**

| Model | pass@1 | pass@10 |
|---|---|---|
| Qwen2.5-Coder-1.5B-Instruct (primary) | **17.59%** | 23.50% |
| Llama-3.2-3B-Instruct (validation arm) | **29.94%** | 47.35% |

Locked target (pre-committed gate): **beat OctoCoder-16B's 30.4% with the 1.5B Qwen**;
stretch GPT-4 (~47%). Harness commit `8fc5bae`.

**Phase 2 COMPLETE (2026-07-19):** data v0.1 = 672 certified bugs (taxonomy-balanced,
contamination-screened, function-level splits) + 374-function restraint suite, all in
`data/`. Routing pass done (A2): **97 sft / 376 rl / 71 easy** — learnable fraction
**69.1%** (variance gate needs ≥30% → GRPO pre-flight passed early). Mean base pass
rate on train bugs 51.2% (vs 17.6% on exam — curriculum easier than exam, as designed).
Routing detail: Drive `phase2/routing_v0.json`.

**Phase 3 dev-side COMPLETE (2026-07-18):** recipe locked by two A/Bs — **no-trace
targets, 1 epoch** (epoch 2 collapses dev pass@16 91.8→82.0; DeepSeek short-trace
distillation loses 7.1 pts pass@1 at matched budget — negative result, kept).
3-seed dev result: **pass@1 59.5% ± 0.8, pass@16 91.8% ± 1.6** (base 45.9/93.4).
Rank ablation: r=16 costs ~2.7 pts pass@1 (outside the cross-seed ruler) — r=32
stays.

**Phase 3 COMPLETE — held-out milestone (2026-07-18):**

| model | pass@1 | pass@10 |
|---|---|---|
| base | 17.59% | 23.50% |
| **SFT ×3 seeds (mean)** | **24.82% (sd 4.2)** | **32.60%** |

**The ceiling moved**: base pass@10 (23.5%) was below the 30.4% target; SFT mean
pass@10 is 32.6% — RL now has room to win. +7.2 pts pass@1 from 672 synthetic
bugs; best seed 29.51%. Exam cross-seed variance (sd 4.2) ≫ dev variance (0.8),
and dev ranking anti-predicted exam ranking → **Amendment A3**: paired-lineage
init (DPO/GRPO seed i starts from SFT seed i; no init selection anywhere).

**CONTROLLED STUDY COMPLETE (2026-07-19)** — held-out final exam, frozen protocol:

| arm (3 seeds) | mean pass@1 | mean pass@10 |
|---|---|---|
| base | 17.59% | 23.50% |
| SFT | 24.82% (sd 4.2) | 32.60% |
| SFT+DPO | 24.90% (sd 4.5) | 32.96% |
| SFT+GRPO | 25.39% (sd 4.0) | 33.70% |
| GRPO w/ **random reward** (control) | 23.29% (s3407) | 31.49% |

Findings: **SFT is the entire lift** (+7.2); DPO adds nothing; GRPO adds a tiny
9/9-paired-consistent nudge that the **random-reward control fully reproduces**
(Spurious-Rewards replication in code repair at 1.5B — process effect, not
signal, at this budget). Best singles: 29.97% (both RL arms, seed 1234) — 0.43
from OctoCoder-16B. Follow-up (13b matrix): v1-SFT scores **below base** on
docstring-style inputs (SFT-forgetting), while **data-v1 SFT ("v2 push",
2,551 self-broken bugs) scores +27 over v1** on that exam-like slice — the
v2 extension (notebooks 12–14+) chases 30.4 from there.

## License

Apache-2.0 (matches the Qwen2.5-Coder base model). See [`LICENSE`](LICENSE).
