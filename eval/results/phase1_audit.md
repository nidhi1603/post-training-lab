# Phase 1 baseline audit (2026-07-18)

Independent re-grade of every baseline attempt (subprocess execution of each
problem's tests; scorer = `eval/pass_at_k.py` tools; notebook `02a_failure_audit`).
Per-problem results files: Drive `rl-post-training/phase1/results_{run}.json`
(the `{task_id, n, c}` contract). 30 never-solved failures per model saved as
`failures_{run}.txt` for reading.

## Scores, verified

| Model | Official pass@1 | Our re-grade | Gap | 95% CI (clustered) | pass@10 |
|---|---|---|---|---|---|
| Qwen2.5-Coder-1.5B-Instruct | 17.59% | 17.59% | 0.00 | [12.13, 23.05] | 23.50% |
| Llama-3.2-3B-Instruct | 29.94% | 29.66% | 0.28 | [23.78, 35.54] | 47.35% |

Two independent graders agree to ≤0.3 pts (residual gap ≈ timeout/flakiness margins
— ours used 8s vs the harness's shorter default). The 30.4% target lies OUTSIDE
Qwen's CI: the gap to close is real, not noise.

## Failure species (failed attempts only)

| Species | Qwen (2,703 failed) | Llama (2,307 failed) |
|---|---|---|
| wrong_logic | 99.4% | 98.2% |
| stutter (repetition loop) | 0.0% | 1.4% |
| broken_syntax | 0.6% | 0.4% |

**No free points anywhere:** failures are overwhelmingly honest reasoning failures.
Format extraction is clean for both models; every future gain must come from
actually teaching repair.

## Reachable sets and the amplification ceiling

| Model | Problems solved ≥1 time in 20 tries | Never solved | Pure-amplification ceiling |
|---|---|---|---|
| Qwen 1.5B | 42/164 | 122 | ≈ 25.6% — **below the 30.4% target** |
| Llama 3B | 83/164 | 81 | ≈ 50.6% |

Implications (feeds Phases 3–5 design; the RL-Squeezes/SFT-Expands 2509.21128
story observed in our own data):

1. **Qwen cannot reach the target by RL alone from base** — GRPO amplifies what
   exists, and only 25.6% worth exists at n=20/temp 0.2. SFT must EXPAND the
   solvable set first; the SFT→GRPO ordering is a necessity, not a convention.
   (Caveat: hotter training-time exploration may find more than n=20@0.2 shows;
   indicative ceiling, not a law.)
2. **Llama has enormous amplification headroom** (29.9 → ~50.6 ceiling): the
   cross-family arm may show a LARGER RL effect than the primary arm — worth
   anticipating in the paper's analysis rather than being surprised by it.
3. Qwen's pass@k selection for RL-init (Phase 3, pass@16 on dev slice) is now
   doubly motivated: the init checkpoint must maximize the reachable set, not
   the greedy score.
