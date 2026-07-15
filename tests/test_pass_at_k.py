"""Tests for the unbiased pass@k estimator and clustered CIs."""
import math

import numpy as np
import pytest

from pass_at_k import aggregate_pass_at_k, mean_and_ci, pass_at_k


def test_pass_at_1_is_c_over_n():
    # pass@1 reduces to the empirical success rate.
    assert pass_at_k(20, 5, 1) == pytest.approx(5 / 20)
    assert pass_at_k(20, 0, 1) == pytest.approx(0.0)
    assert pass_at_k(20, 20, 1) == pytest.approx(1.0)


def test_all_correct_is_one():
    assert pass_at_k(10, 10, 3) == 1.0


def test_none_correct_is_zero():
    assert pass_at_k(10, 0, 5) == 0.0


def test_matches_closed_form_binomial():
    # pass@k = 1 - C(n-c, k)/C(n, k)
    n, c, k = 20, 4, 5
    expected = 1 - math.comb(n - c, k) / math.comb(n, k)
    assert pass_at_k(n, c, k) == pytest.approx(expected)


def test_pass_at_k_monotonic_in_k():
    n, c = 20, 3
    vals = [pass_at_k(n, c, k) for k in range(1, n + 1)]
    assert all(a <= b + 1e-12 for a, b in zip(vals, vals[1:]))


def test_pass_at_k_monotonic_in_c():
    n, k = 20, 5
    vals = [pass_at_k(n, c, k) for c in range(0, n + 1)]
    assert all(a <= b + 1e-12 for a, b in zip(vals, vals[1:]))


def test_invalid_args_raise():
    with pytest.raises(ValueError):
        pass_at_k(10, 11, 1)
    with pytest.raises(ValueError):
        pass_at_k(10, 5, 0)
    with pytest.raises(ValueError):
        pass_at_k(10, 5, 11)


def test_aggregate_and_ci():
    counts = [(20, 10), (20, 20), (20, 0), (20, 5)]
    mean, pp = aggregate_pass_at_k(counts, 1)
    assert mean == pytest.approx(np.mean([0.5, 1.0, 0.0, 0.25]))
    ci = mean_and_ci(pp)
    assert ci["ci_low"] <= ci["mean"] <= ci["ci_high"]
    assert ci["n_problems"] == 4


def test_ci_zero_width_for_single_problem():
    _, pp = aggregate_pass_at_k([(20, 10)], 1)
    ci = mean_and_ci(pp)
    assert ci["se"] == 0.0
    assert ci["ci_low"] == ci["ci_high"] == ci["mean"]
