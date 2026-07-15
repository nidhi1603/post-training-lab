"""Reward unit tests -- the CoRPO invariant is proved here BEFORE any GPU is touched.

If any test in this file fails, do not train: the reward can positively reinforce a
failing patch relative to a passing one, and GRPO will happily exploit that.
"""
import itertools

import pytest

from reward import (
    ExecResult,
    max_failing_reward,
    min_passing_reward,
    reward,
)


def test_all_pass_beats_partial():
    passing = reward(ExecResult(compiles=True, num_passed=3, num_tests=3))
    partial = reward(ExecResult(compiles=True, num_passed=2, num_tests=3))
    assert passing > partial


def test_partial_credit_is_monotonic():
    r1 = reward(ExecResult(compiles=True, num_passed=1, num_tests=4))
    r2 = reward(ExecResult(compiles=True, num_passed=2, num_tests=4))
    r3 = reward(ExecResult(compiles=True, num_passed=3, num_tests=4))
    assert r1 < r2 < r3


def test_compile_bonus_applies():
    compiles = reward(ExecResult(compiles=True, num_passed=0, num_tests=3))
    no_compile = reward(ExecResult(compiles=False, num_passed=0, num_tests=3))
    assert compiles > no_compile


def test_length_penalty_capped_and_signed():
    base = reward(ExecResult(compiles=True, num_passed=3, num_tests=3, output_tokens=0))
    long = reward(ExecResult(compiles=True, num_passed=3, num_tests=3, output_tokens=10_000),
                  length_budget=1024)
    assert long < base
    assert base - long <= 0.05 + 1e-9  # capped


def test_invariant_min_passing_exceeds_max_failing():
    """The analytic bound: worst passing patch strictly beats the best failing one."""
    assert min_passing_reward() > max_failing_reward()


@pytest.mark.parametrize("num_tests", [1, 2, 3, 5, 8, 20])
@pytest.mark.parametrize("out_tokens", [0, 512, 1024, 4096, 100_000])
def test_invariant_holds_over_grid(num_tests, out_tokens):
    """Exhaustive check: NO failing patch out-rewards ANY passing patch.

    Failing patches get to be as favourable as possible (compiles, longest partial
    pass, zero length penalty); passing patches get the worst case (max length
    penalty). The min passing must still dominate the max failing.
    """
    # Every failing outcome for this num_tests, most favourable length (no penalty).
    failing_rewards = [
        reward(ExecResult(compiles=c, num_passed=p, num_tests=num_tests, output_tokens=0))
        for c, p in itertools.product([True, False], range(0, num_tests))  # p < num_tests
    ]
    # Worst-case passing patch: all pass but heavily penalised for length.
    worst_passing = reward(
        ExecResult(compiles=True, num_passed=num_tests, num_tests=num_tests, output_tokens=out_tokens)
    )
    assert worst_passing > max(failing_rewards)


def test_exec_result_validates_inputs():
    with pytest.raises(ValueError):
        ExecResult(compiles=True, num_passed=5, num_tests=3)
    with pytest.raises(ValueError):
        ExecResult(compiles=True, num_passed=0, num_tests=0)
