"""Tests for the paired significance tools."""
import numpy as np
import pytest

from stats import holm_bonferroni, mcnemar_exact, paired_bootstrap_diff


def test_mcnemar_counts_discordant_pairs():
    a = [1, 1, 0, 0, 1]
    b = [1, 0, 1, 0, 0]
    out = mcnemar_exact(a, b)
    assert out["b"] == 2  # A right, B wrong: problems idx1, idx4
    assert out["c"] == 1  # A wrong, B right: idx2
    assert out["n_discordant"] == 3


def test_mcnemar_no_discordant_is_p1():
    a = [1, 0, 1]
    out = mcnemar_exact(a, a)
    assert out["p_value"] == 1.0
    assert out["n_discordant"] == 0


def test_mcnemar_extreme_split_is_significant():
    # A solves 10 that B misses, B solves 0 that A misses -> strong evidence.
    a = [1] * 10 + [1] * 10
    b = [0] * 10 + [1] * 10
    out = mcnemar_exact(a, b)
    assert out["b"] == 10 and out["c"] == 0
    assert out["p_value"] < 0.01


def test_bootstrap_ci_brackets_mean_diff():
    rng = np.random.default_rng(0)
    a = rng.random(164)
    # B better on average by ~0.05, but with per-problem noise so the bootstrap
    # distribution is non-degenerate (a constant offset would give a zero-width CI).
    b = np.clip(a + 0.05 + rng.normal(0, 0.02, size=164), 0, 1)
    out = paired_bootstrap_diff(a, b, n_resamples=2000, seed=1)
    assert out["mean_diff"] == pytest.approx((b - a).mean(), abs=1e-9)
    assert out["ci_low"] <= out["mean_diff"] <= out["ci_high"]
    # A clear, consistent improvement should not straddle zero.
    assert out["ci_low"] > 0


def test_bootstrap_is_deterministic_under_seed():
    a = np.linspace(0, 1, 50)
    b = a[::-1]
    o1 = paired_bootstrap_diff(a, b, n_resamples=1000, seed=7)
    o2 = paired_bootstrap_diff(a, b, n_resamples=1000, seed=7)
    assert o1 == o2


def test_holm_bonferroni_orders_and_rejects():
    pvals = [0.001, 0.04, 0.03, 0.5]
    out = holm_bonferroni(pvals, alpha=0.05)
    # Smallest p tested against alpha/4 = 0.0125 -> reject.
    assert out[0]["reject"] is True
    # 0.5 is nowhere near significant.
    assert out[3]["reject"] is False
    # Output preserves original order.
    assert [o["index"] for o in out] == [0, 1, 2, 3]


def test_holm_bonferroni_step_down_stops():
    # Once a hypothesis fails, all larger p-values also fail.
    pvals = [0.01, 0.20, 0.02]
    out = holm_bonferroni(pvals, alpha=0.05)
    # sorted: 0.01 (thr .0167 -> reject), 0.02 (thr .025 -> but must stop? no:
    # 0.02 <= .025 reject), 0.20 (thr .05 -> fail). Check the fail propagates only forward.
    rejects = {o["index"]: o["reject"] for o in out}
    assert rejects[0] is True
    assert rejects[1] is False
