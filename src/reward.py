"""Execution-verified reward for GRPO code repair (Phase 5).

DESIGN INVARIANT (the CoRPO lesson, arXiv 2511.04439): no failing patch may ever
out-reward a passing one. With GRPO's mean-relative baseline, a "less wrong" patch
in an all-bad group is positively reinforced unless the all-pass bonus *strictly*
dominates every partial-credit + shaping term. We guarantee this by construction
and prove it in tests/test_reward.py -- written and green before any GPU is touched.

This module is deliberately PURE: it maps an already-computed execution result to a
scalar. Sandboxed execution (subprocess, timeouts, test files read-only to the
policy's code -- Meta's agentic-repair study, arXiv 2510.22075, watched models delete
the validation code to "pass") lives in the reward server, not here, so the scoring
logic stays trivially unit-testable.

Reward layering (correctness-dominated):
    compiles/parses            -> +0.10
    fraction of tests passed   -> +0.20 * frac
    ALL tests pass             -> +1.00
    length penalty (absurd out)-> up to -0.05, capped so the invariant cannot break
"""
from __future__ import annotations

from dataclasses import dataclass

COMPILE_BONUS = 0.10
PARTIAL_WEIGHT = 0.20  # multiplied by fraction of tests passed
ALL_PASS_BONUS = 1.00
LENGTH_PENALTY_CAP = 0.05  # hard cap; see invariant proof below


@dataclass
class ExecResult:
    """Outcome of running a candidate patch against a problem's test suite."""

    compiles: bool
    num_passed: int
    num_tests: int
    output_tokens: int = 0

    def __post_init__(self):
        if self.num_tests < 1:
            raise ValueError("num_tests must be >= 1")
        if not (0 <= self.num_passed <= self.num_tests):
            raise ValueError("num_passed out of range [0, num_tests]")

    @property
    def all_pass(self) -> bool:
        return self.num_passed == self.num_tests

    @property
    def frac_passed(self) -> float:
        return self.num_passed / self.num_tests


def _length_penalty(output_tokens: int, length_budget: int) -> float:
    """Mild, capped penalty for absurdly long generations.

    Linear in the overage past `length_budget`, saturating at LENGTH_PENALTY_CAP once
    the output is >= 2x the budget. Capped so a passing patch can never be pushed
    below a failing one (see invariant proof in the module test).
    """
    if length_budget <= 0:
        return 0.0
    overage = max(0, output_tokens - length_budget)
    return min(LENGTH_PENALTY_CAP, LENGTH_PENALTY_CAP * overage / length_budget)


def reward(result: ExecResult, length_budget: int = 1024) -> float:
    """Scalar reward for a single candidate patch.

    Args:
        result: execution outcome (compiles, tests passed/total, output length).
        length_budget: token budget above which the length penalty kicks in.

    Returns:
        A float. By construction, min over passing patches (>= 1.25) strictly exceeds
        max over failing patches (< 0.30).
    """
    r = 0.0
    if result.compiles:
        r += COMPILE_BONUS
    r += PARTIAL_WEIGHT * result.frac_passed
    if result.all_pass:
        r += ALL_PASS_BONUS
    r -= _length_penalty(result.output_tokens, length_budget)
    return r


# Analytic bounds used by the invariant test. Keeping them here means any change to
# the weights above is immediately checked against the CoRPO invariant.
def max_failing_reward() -> float:
    """Supremum of reward over all FAILING patches (not all tests pass), no penalty."""
    # Best failing case: compiles, all-but-one test passes, no length penalty.
    # frac < 1, so this is a strict upper bound as num_tests -> inf.
    return COMPILE_BONUS + PARTIAL_WEIGHT  # 0.30 (not attained; frac -> 1^-)


def min_passing_reward() -> float:
    """Infimum of reward over all PASSING patches (all tests pass)."""
    # Worst passing case: all tests pass but max length penalty applied.
    return COMPILE_BONUS + PARTIAL_WEIGHT + ALL_PASS_BONUS - LENGTH_PENALTY_CAP  # 1.25
