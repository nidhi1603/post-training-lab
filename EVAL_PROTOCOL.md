# EVAL_PROTOCOL.md — the frozen ruler

**This file is the ruler. It is filled in during Phase 1 and NEVER edited afterward.**
Every headline number in the paper is produced under exactly these settings. If a
setting below still says `TODO`, the protocol is not yet frozen and no arm may be
compared. Freezing = filling every field, committing this file, and recording the
commit hash in the paper's reproducibility statement.

Status: **DRAFT — not yet frozen** (fill in Phase 1, then change this line to
`FROZEN as of <commit hash> on <date>` and stop editing).

---

## Benchmark

- Benchmark: **HumanEvalFix**, Python split (`humanevalfixtests-python`).
- Source: OctoPack, arXiv 2308.07124.
- Number of problems: **164** (held-out; touched only at phase-end milestones).
- Held-in dev slice: a fixed ~100-problem slice of **training-distribution** bugs
  (built in Phase 2, NOT drawn from the benchmark) — used for every checkpoint decision.

## Harness

- Harness: **bigcode-evaluation-harness**.
- Git commit hash: `TODO — record exact commit`.
- Install command / container: `TODO`.

## Prompt format

- Chosen format: `TODO` (candidates: `--prompt instruct` and the harness alternatives).
- Selection procedure: ran 20 problems per candidate on Qwen2.5-Coder-1.5B-Instruct,
  read raw generations, picked the one with no malformed outputs. (FormatSpread,
  arXiv 2310.11324 — formatting alone swings results; that is why we freeze it.)
- Frozen prompt template: `TODO — paste verbatim`.

## Decode settings (identical for every headline number)

| Setting | Value |
|---|---|
| temperature | 0.2 |
| top_p | 0.95 |
| n_samples | 20 |
| max_new_tokens | `TODO` |
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

- Base pass@1 measured: `TODO %` (Qwen), `TODO %` (Llama), each with 95% CI.
- If base < 30.4% → target = beat **OctoCoder-16B (30.4%)**; stretch = GPT-4 row (~47%).
- If base ≥ 30.4% → target = GPT-4 row, or the harder language splits.
- Locked target: `TODO`.

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
