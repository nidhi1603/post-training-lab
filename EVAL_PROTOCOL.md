# EVAL_PROTOCOL.md — the frozen ruler

**This file is the ruler. It is filled in during Phase 1 and NEVER edited afterward.**
Every headline number in the paper is produced under exactly these settings. If a
setting below still says `TODO`, the protocol is not yet frozen and no arm may be
compared. Freezing = filling every field, committing this file, and recording the
commit hash in the paper's reproducibility statement.

Status: **FROZEN on 2026-07-18** (both baselines measured; the freezing commit is
recorded in git history). From this point, this file receives no edits — any
deviation forced by reality gets a dated note in the paper's limitations instead.

---

## Benchmark

- Benchmark: **HumanEvalFix**, Python split (`humanevalfixtests-python`).
- Source: OctoPack, arXiv 2308.07124.
- Number of problems: **164** (held-out; touched only at phase-end milestones).
- Held-in dev slice: a fixed ~100-problem slice of **training-distribution** bugs
  (built in Phase 2, NOT drawn from the benchmark) — used for every checkpoint decision.

## Harness

- Harness: **bigcode-evaluation-harness**.
- Git commit hash: `8fc5bae6479c4fbbb28c3f8b644f6a15b3f3b5bd` (recorded from the Phase-1 run, 2026-07-15).
- Install: `git clone https://github.com/bigcode-project/bigcode-evaluation-harness && pip install -e .` on Colab L4, then `pip install -U transformers accelerate`.

## Prompt format

- Chosen format: **`--prompt instruct`** (used for the Phase-1 baseline run, 2026-07-15).
- Note: the harness's post-processing extracted code well enough to produce a plausible
  score distribution; a raw-generation audit (failure taxonomy read) is scheduled as the
  first step of Phase 2 and any format pathology found there gets a dated note here —
  the format itself does not change. (FormatSpread, arXiv 2310.11324 — formatting alone
  swings results; that is why we freeze it.)
- Frozen prompt template: the harness `humanevalfixtests-python` task's `instruct`
  template at commit `8fc5bae` (see harness source for verbatim text).

## Decode settings (identical for every headline number)

| Setting | Value |
|---|---|
| temperature | 0.2 |
| top_p | 0.95 |
| n_samples | 20 |
| max_length_generation | 2048 (total sequence budget — generous on purpose so reasoning-style checkpoints are never truncated by the ruler) |
| batch_size | 16 (1.5B) / 8 (3B) |
| seed | 0 |
| execution | `--allow_code_execution` |
| GPU / dtype | L4, bfloat16 (T4 lacks bf16) |

Training rollouts may use a different temperature (~1.0). **Eval decoding never
changes.** Never compare checkpoint A at one temperature with checkpoint B at another.

## Scoring

- Metric: **pass@1** via the unbiased Codex estimator, `pass@k = 1 − C(n−c,k)/C(n,k)`
  (implemented in [`eval/pass_at_k.py`](eval/pass_at_k.py)).
- Correctness: **execution only** — all unit tests pass. No LLM judge.
- Confidence intervals: problem-level (clustered) 95% CI, mean ± z·SE.
- Paired comparisons: McNemar exact (binary) and/or paired bootstrap on the shared 164
  problems ([`eval/stats.py`](eval/stats.py)). Holm–Bonferroni across the family of
  comparisons. Never two independent means.
- Taxonomy: every eval also emits a per-category table
  ([`eval/taxonomy_breakdown.py`](eval/taxonomy_breakdown.py)).

## Targets (locked in Phase 1, step 5 — no goalpost-moving)

- Base pass@1 measured: **17.59%** (Qwen2.5-Coder-1.5B-Instruct, 2026-07-15; pass@10 = 23.50%;
  rough 95% CI ≈ ±6 pts, exact clustered CI to be computed from per-problem results).
  **Llama-3.2-3B-Instruct: 29.94%** (2026-07-18; pass@10 = 47.35%; model revision
  `0cb88a4f764b7a12671c53f0838cd831a0843b95`; loaded from local snapshot after a hub
  sharded-resolution failure — dated note, not a protocol change).
- Role note (pre-committed in the master workflow): Llama is the **cross-family
  validation arm** — it is compared only against its own baseline, never against the
  OctoCoder target. Its base (~29.9%) already sits at the OctoCoder line, so
  "Llama beats OctoCoder" would be a trivial non-claim; the headline claim structure
  remains Qwen-primary.
- Decision rule (pre-committed): base < 30.4% → target = beat **OctoCoder-16B (30.4%)**;
  stretch = GPT-4 row (~47%). Base ≥ 30.4% → target = GPT-4 row.
- **LOCKED TARGET (2026-07-15): 17.59% < 30.4% → beat OctoCoder-16B's 30.4% pass@1
  with the 1.5B model. Stretch: GPT-4's ~47%. Gap to close: ~+12.8 points.
  No goalpost-moving after this line.**

## Contamination rule

- Nothing derived from HumanEval may enter training data.
- Audit: 50-gram substring overlap + embedding near-duplicate check (LLM Decontaminator,
  arXiv 2311.04850) + grep for HumanEval function names. Report:
  [`eval/contamination_report.md`](eval/contamination_report.md).

## Held-in / held-out policy

- Held-out benchmark (164): evaluated **once** per arm, at phase-end milestones only.
- Held-in dev slice (~100): all day-to-day checkpoint decisions.
- No overlap between train / dev / benchmark, enforced by hashing.

---

*Reproducibility: cite this file's commit hash in the paper. Any deviation forced by
reality gets a dated note in the paper's limitations, not a silent edit here.*
