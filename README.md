# post-training-lab

**A fine-tuned 1.5B model beat OctoCoder (15.5B) on HumanEvalFix: 38.63% pass@1, 3-seed
mean, against a 30.40% target, under the OctoPack paper's own protocol.** A controlled
SFT vs DPO vs GRPO study, with a random-reward control, then showed what produced the
gain: the training data, not the RL.

## Results

Held-out HumanEvalFix (Python, 164 problems), frozen protocol:

| model | pass@1 | pass@10 |
|---|---|---|
| Qwen2.5-Coder-1.5B base | 17.59% | 23.50% |
| **OctoCoder, 15.5B (the paper's flagship — our locked target)** | **30.40%** | — |
| **ours: SFT v2, 3-seed mean** | **38.63% (sd 4.07)** | **48.66%** |
| ours: worst seed | 34.51% | 47.24% |
| ours: best seed | 42.65% | 50.21% |

A 1.5B model beats the 15.5B flagship by **+8.2 pts mean** (worst seed +4.1) under the
paper's own frozen protocol — no HumanEval-derived training data, contamination-
screened, pre-registered claim standard (mean AND every seed above target) met.
The winning intervention was **data**: a $0.34 LLM-self-broken, docstring-style
bug corpus (2,551 bugs), after the controlled study showed every RL arm tying
or nudging spuriously (random-reward control) at v0 data difficulty.

How it was measured: pass@1 at temperature 0.2, top-p 0.95 and 20 samples per problem,
following [OctoPack (arXiv 2308.07124)](https://arxiv.org/abs/2308.07124).
[`EVAL_PROTOCOL.md`](EVAL_PROTOCOL.md) was frozen in commit `1adb353`, before the first
training run, and has not been edited since. OctoCoder's 30.4% is the paper's published
score; its size is from [StarCoder (arXiv 2305.06161)](https://arxiv.org/abs/2305.06161).

## What the study found

1. **Data beat the algorithm.** On the first 672-bug corpus, SFT gave +7.2 pts pass@1,
   DPO added nothing, and GRPO's small nudge was fully reproduced by GRPO with a
   *random* reward.
2. **The RL signal stayed at noise with better data.** Byte-identical GRPO twins from the
   SFT v2 model, one trained on the real execution reward and one on a random reward:
   real minus random came to +0.61 pass@1.
3. **With a verifier, the scaffold does the work.** Sampling fixes, running each
   problem's provided tests and repairing on failure takes the *untrained* base to 65.2%
   verified-resolve (a separate agentic protocol, never mixed with pass@1). Training's
   lift shrinks from +21.3 pts at one try to +2.5 at ~14–18 tries, inside the ±3.7
   binomial noise. Fine-tune when you can't verify; scaffold when you can.

Prior art: Repair-R1 ([arXiv 2507.22853](https://arxiv.org/abs/2507.22853)) already ran
GRPO with execution rewards on this exact model, so RL for code repair is not new here.
What this lab adds is the controlled three-arm comparison under matched budgets and
paired seeds, a random-reward control (a replication of
[Spurious Rewards, arXiv 2506.10947](https://arxiv.org/abs/2506.10947) in code repair at
1.5B), and the evaluation discipline.

The full record is in [Lab history](#lab-history) below and, run by run, in
[`docs/LAB_NOTEBOOK.md`](docs/LAB_NOTEBOOK.md).

## Limits

- One benchmark and one model family for the headline. A Llama-3.2-3B arm was
  baselined (29.94% pass@1), but its training rerun was skipped as low-value after the
  controls.
- The target is OctoCoder's published number, not a re-run under this harness. It also
  pits a 2023 model against a 2024 base, and newer bases start stronger.
- The contamination screen that ran drops training functions whose names collide with
  an exam entry point or whose normalized solution matches an exam solution: 4 of 378
  MBPP+ functions ([`scripts/build_data_v0.py`](scripts/build_data_v0.py)). The fuller
  n-gram and embedding audit described in
  [`eval/contamination_report.md`](eval/contamination_report.md) was not run.
- Exam variance across seeds is large (sd 4.07 on the headline), which is why the claim
  required every seed, not just the mean, to clear the target.

## Repo layout

```
post-training-lab/
├── EVAL_PROTOCOL.md               the frozen ruler (commit 1adb353)
├── RL_Project_Master_Workflow.md  the original study plan
├── docs/
│   ├── LAB_NOTEBOOK.md            every run, decision and result, in order
│   ├── EVALS_PLAYBOOK.md          maps the lab to agent-evals concepts
│   ├── READING_UPDATES.md         dated literature passes after the plan froze
│   └── hacking_log.md             reward-hacking checklist and log template
├── eval/
│   ├── pass_at_k.py               unbiased pass@k + clustered CIs
│   ├── stats.py                   McNemar + paired bootstrap + Holm
│   ├── taxonomy.json              OctoPack Table 15 bug taxonomy (per-problem map: placeholder)
│   ├── taxonomy_breakdown.py      per-category pass@k table
│   ├── contamination_report.md    the planned fuller audit (not run; see Limits)
│   └── results/phase1_audit.md    baseline audit
├── src/
│   ├── reward.py                  GRPO reward with the CoRPO invariant
│   ├── variance_gate.py           GRPO pre-flight signal gate
│   ├── mutate.py                  mutation-based bug injection
│   └── prompts.py                 the single training-side repair prompt
├── scripts/build_data_v0.py       data v0 build, including the contamination screen
├── data/                          v0 corpus (672 bugs), restraint suite (374), contamination drops (4)
├── notebooks/                     01–21: every training and evaluation run (Colab)
└── tests/                         77 tests, CPU-only
```

Training ran in Colab; the eval and reward layers run and are tested on a laptop.

## Run the tests (CPU, no GPU)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m pytest -q          # 77 passed
```

## Protocol rules (fixed before training)

1. The ruler is **frozen** before training (`EVAL_PROTOCOL.md`, never edited after).
2. **Nothing** derived from HumanEval enters training data — enforced by the contamination
   screen in `scripts/build_data_v0.py`.
3. The held-out benchmark is touched **only at milestones**; daily decisions use the dev slice.
4. **Matched budgets** across arms.
5. **Same decode settings** for every headline number (temp 0.2, top_p 0.95, n=20, pass@1).
6. Correctness graded by **execution only** — no LLM judge in the correctness pipeline.
7. **Report what happened** — failed runs and hacked rewards are content, not embarrassments.

## Lab history

The study's running log, in order. Every number above traces to an entry here or in
the lab notebook.

**Phases 0–1 COMPLETE (2026-07-18). Protocol FROZEN.**

| Model | pass@1 | pass@10 |
|---|---|---|
| Qwen2.5-Coder-1.5B-Instruct (primary) | **17.59%** | 23.50% |
| Llama-3.2-3B-Instruct (validation arm) | **29.94%** | 47.35% |

Locked target (pre-committed gate): **beat OctoCoder's 30.4% (15.5B) with the 1.5B Qwen**;
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
from OctoCoder's 30.4%. Follow-up (13b matrix): v1-SFT scores **below base** on
docstring-style inputs (SFT-forgetting), while **data-v1 SFT ("v2 push",
2,551 self-broken bugs) scores +27 over v1** on that exam-like slice — the
v2 extension (notebooks 12–14+) chases 30.4 from there.

**GRPO v2 TWINS — ATTRIBUTION REFEREE (2026-07-20):** we gave the execution
signal everything it lacked at v0 — the harder v1 pile, 2× steps, 2× lr, and a
QiMeng-style edit-aware penalty — and trained byte-identical twins (real reward
vs Uniform(0,1.3)) from the SFT v2 s3407 init. Held-out exam: **real 35.95/47.07
vs random 35.34/47.73 vs init 34.51/47.24** — real−random = +0.61 pass@1,
effectively zero. **The Spurious-Rewards result replicates at v2 difficulty:
every RL gain in this project was process, not signal.** Mechanism: the
pre-flight gate found only **15%** of the pile still produced mixed pass/fail
groups for the v2 init — SFT had consumed the headroom GRPO needs; random
reward's damage (−5 dev pass@8) was a tail collapse the temp-0.2 exam never
sees; the EA penalty visibly shaped behavior (record 49% unchanged-rate on the
restraint probe) without shaping exam correctness. **Final study conclusion:
data > algorithm at this scale and budget** — the best exam number remains
plain SFT on better data (42.65% pass@1, seed 1234).

**AGENTIC TRACK (2026-07-20 — separate protocol, never compared to pass@1):**
the same SFT v2 model run as an *agent* — sample 10 candidate fixes in its
native prompt format, **execute the task's own provided unit tests**, submit a
verified fix, ≤2 self-repair rounds on the error output:

| stage (seed 3407, 164 problems) | verified-resolve |
|---|---|
| single sample (native prompt, temp 0.8) | 44.5% |
| best-of-10, test-verified | 65.9% |
| + 2 repair rounds (final) | **67.7%** |

**1.96× the same seed's frozen single-shot score (34.51%) with zero new
training.** Bonus finding: the native-format single-sample row (44.5%)
quantifies a ~10-pt prompt-format tax the frozen harness prompt charges this
model. Guardrail: this number is always "verified-resolve, agentic
protocol" — it never enters the frozen table above.

**THE CONTROL (2026-07-21) — the 2×2 that re-attributes the 67.7:** running
the **untrained base** through the byte-identical scaffold:

|  | single-shot | + agent |
|---|---|---|
| Base 1.5B | 17.6% | **65.2%** |
| SFT v2 | 34.5% | 67.7% |

Under verification, training adds only **+2.5 pts (within the ±3.7 binomial
noise)** — the scaffold, not the fine-tune, does the work once tests can be
executed at inference. Registered prediction (base+agent 30–42%) was wrong,
same root cause as before: ceilings anchored on frozen-protocol pass@10
wildly understate what native-prompt hot sampling can reach. **Corrected
reading: SFT at this scale consolidates (first-try reliability +17 to +21
pts) far more than it adds capability (ceiling +2.5 ≈ noise). Fine-tuning's
value concentrates where a verifier is NOT available; where one is, best-of-n
on the raw base already gets ~65%.** Third control of the project, third
appearance overturned.

## License

Apache-2.0 (matches the Qwen2.5-Coder base model). See [`LICENSE`](LICENSE).
