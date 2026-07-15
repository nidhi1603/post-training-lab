"""Unbiased pass@k estimation and confidence intervals for execution-verified evals.

Implements the estimator from Chen et al. 2021 (Codex / HumanEval):

    pass@k = 1 - C(n-c, k) / C(n, k)

computed in the numerically stable product form that avoids overflowing the
binomial coefficients on large n.

Frozen protocol for this lab (see ../EVAL_PROTOCOL.md): n=20 samples, k=1 for every
headline number, temperature 0.2 / top_p 0.95. The only sanctioned k>1 use is the
pass@16 on the held-in dev slice used to pick the RL-init checkpoint in Phase 3
(Quagmires, arXiv 2510.01624: RL needs the distribution to *contain* correct
answers, so pass@large-k predicts RL outcomes where greedy pass@1 does not).
"""
from __future__ import annotations

import numpy as np

# z for a two-sided 95% normal interval. Kept as a constant so the whole lab
# reports the same interval without pulling in scipy.
Z_95 = 1.959963984540054


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased estimate of pass@k for a single problem.

    Args:
        n: total number of samples drawn for the problem.
        c: number of correct (all-tests-passing) samples, 0 <= c <= n.
        k: the k in pass@k, 1 <= k <= n.

    Returns:
        Probability that at least one of k samples drawn *without replacement*
        from the n samples is correct.
    """
    if not (0 <= c <= n):
        raise ValueError(f"c={c} out of range [0, n={n}]")
    if not (1 <= k <= n):
        raise ValueError(f"k={k} out of range [1, n={n}]")
    if n - c < k:
        # Fewer than k incorrect samples remain: every k-subset must contain a
        # correct one, so the estimate is exactly 1.
        return 1.0
    return float(1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1)))


def aggregate_pass_at_k(counts, k: int):
    """Mean pass@k over a benchmark.

    Args:
        counts: iterable of (n_i, c_i) per problem.
        k: the k in pass@k.

    Returns:
        (mean, per_problem) where per_problem is a float array of the per-problem
        pass@k estimates in input order. Keep per_problem around -- it is what the
        confidence interval and the paired tests (stats.py) consume.
    """
    per_problem = np.array([pass_at_k(n, c, k) for n, c in counts], dtype=float)
    if per_problem.size == 0:
        raise ValueError("no problems provided")
    return float(per_problem.mean()), per_problem


def mean_and_ci(per_problem, z: float = Z_95):
    """Benchmark score with a problem-level (clustered) confidence interval.

    The benchmark score is the mean of the per-problem pass@k estimates; its
    standard error is the standard deviation across problems divided by sqrt(#problems).
    Clustering at the problem level -- rather than pooling all n*#problems samples --
    is the correct unit and is what "Adding Error Bars to Evals" (arXiv 2411.00640)
    recommends: samples within a problem are not independent draws of "the metric".

    Returns:
        dict(mean, se, ci_low, ci_high, n_problems).
    """
    x = np.asarray(per_problem, dtype=float)
    n = x.size
    if n == 0:
        raise ValueError("no problems provided")
    mean = float(x.mean())
    se = float(x.std(ddof=1) / np.sqrt(n)) if n > 1 else 0.0
    half = z * se
    return {
        "mean": mean,
        "se": se,
        "ci_low": mean - half,
        "ci_high": mean + half,
        "n_problems": n,
    }
