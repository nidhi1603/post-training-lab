"""Paired significance tests for comparing two arms on the SAME benchmark problems.

Ground rule 5 + Phase 6: every headline comparison is *paired* on the shared 164
HumanEvalFix problems -- never two independent means. Two arms are evaluated on the
identical problem set, so the right question is "on how many problems did they
disagree, and in whose favour?", not "do two separate score distributions overlap?".

Two complementary tools:
  * mcnemar_exact       -- binary correctness (e.g. greedy or majority-vote), exact
                           binomial test on the discordant pairs.
  * paired_bootstrap_diff -- continuous per-problem scores (pass@k estimates), a CI
                             on the mean paired difference via ~10k resamples.

On a 164-item benchmark near 50%, CIs span several points -- claim nothing inside
the interval (Phase 6 / "A Sober Look", arXiv 2504.07086).
"""
from __future__ import annotations

from math import comb

import numpy as np


def mcnemar_exact(a_correct, b_correct) -> dict:
    """Exact McNemar test on paired binary outcomes.

    Args:
        a_correct, b_correct: 0/1 (or bool) arrays, same length and problem order.

    Returns:
        dict with
          b            -- #problems A solved and B did not,
          c            -- #problems B solved and A did not,
          n_discordant -- b + c,
          p_value      -- two-sided exact binomial p under H0: P(discordant favours A)=0.5.
    """
    a = np.asarray(a_correct).astype(bool)
    b = np.asarray(b_correct).astype(bool)
    if a.shape != b.shape:
        raise ValueError("a_correct and b_correct must have the same shape")
    b01 = int(np.sum(a & ~b))  # A correct, B wrong
    c01 = int(np.sum(~a & b))  # A wrong, B correct
    n = b01 + c01
    if n == 0:
        return {"b": 0, "c": 0, "n_discordant": 0, "p_value": 1.0}
    k = min(b01, c01)
    tail = sum(comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    p_value = min(1.0, 2.0 * tail)
    return {"b": b01, "c": c01, "n_discordant": n, "p_value": p_value}


def paired_bootstrap_diff(
    a_scores,
    b_scores,
    n_resamples: int = 10_000,
    confidence: float = 0.95,
    seed: int = 0,
) -> dict:
    """Bootstrap CI for the mean paired difference (B - A) over problems.

    Resamples *problems* (the cluster unit) with replacement. Seeded, so results
    are reproducible for the paper.

    Args:
        a_scores, b_scores: per-problem scores (e.g. pass@1 estimates), same order.
        n_resamples: number of bootstrap resamples.
        confidence: two-sided coverage (0.95 -> 2.5%/97.5% percentiles).
        seed: RNG seed.

    Returns:
        dict(mean_diff, ci_low, ci_high, n_resamples).
    """
    a = np.asarray(a_scores, dtype=float)
    b = np.asarray(b_scores, dtype=float)
    if a.shape != b.shape:
        raise ValueError("a_scores and b_scores must have the same shape")
    diff = b - a
    m = diff.size
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, m, size=(n_resamples, m))
    boot = diff[idx].mean(axis=1)
    lo = float(np.quantile(boot, (1 - confidence) / 2))
    hi = float(np.quantile(boot, 1 - (1 - confidence) / 2))
    return {
        "mean_diff": float(diff.mean()),
        "ci_low": lo,
        "ci_high": hi,
        "n_resamples": n_resamples,
    }


def holm_bonferroni(pvalues, alpha: float = 0.05) -> list[dict]:
    """Holm-Bonferroni step-down correction for a family of comparisons.

    Use when the results table makes several arm-vs-arm claims at once (Phase 6).

    Args:
        pvalues: iterable of raw p-values.
        alpha: family-wise error rate.

    Returns:
        list of dicts (index, p_value, threshold, reject) in the ORIGINAL order.
    """
    p = list(pvalues)
    n = len(p)
    order = sorted(range(n), key=lambda i: p[i])
    out = [None] * n
    still_rejecting = True
    for rank, i in enumerate(order):
        threshold = alpha / (n - rank)
        reject = still_rejecting and p[i] <= threshold
        if not reject:
            still_rejecting = False  # once one fails, all larger p's fail too
        out[i] = {"index": i, "p_value": p[i], "threshold": threshold, "reject": reject}
    return out
