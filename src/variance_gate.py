"""Pre-flight variance gate for GRPO (Phase 5, step 3).

GRPO's advantage is group-relative: a prompt where all G rollouts pass, or all G
fail, has zero within-group variance and therefore ZERO learning signal. Spending
GPU rolling those out is wasted. Before training, sample G completions per prompt
from the init checkpoint and keep prompts whose group is *mixed*.

The sampling itself (loading the model, generating, executing) happens in Colab.
This module is the pure, testable bucketing logic that decides what the sampling
means -- so the policy stays here, not scattered through a notebook.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PromptBuckets:
    learnable: list  # 0 < passes < group_size  -> nonzero advantage, keep
    too_easy: list  # passes == group_size      -> all pass, no signal
    too_hard: list  # passes == 0               -> all fail, no signal

    @property
    def learnable_fraction(self) -> float:
        total = len(self.learnable) + len(self.too_easy) + len(self.too_hard)
        return len(self.learnable) / total if total else 0.0


def bucket_prompts(pass_counts, group_size: int) -> PromptBuckets:
    """Bucket prompts by within-group outcome.

    Args:
        pass_counts: iterable of (prompt_id, num_passing) with num_passing in
            [0, group_size] -- the count of the group's rollouts that passed all tests.
        group_size: G, the number of rollouts sampled per prompt.

    Returns:
        PromptBuckets with prompt_ids sorted into learnable / too_easy / too_hard.
    """
    if group_size < 2:
        raise ValueError("group_size must be >= 2 for group-relative advantage")
    buckets = PromptBuckets(learnable=[], too_easy=[], too_hard=[])
    for prompt_id, n_pass in pass_counts:
        if not (0 <= n_pass <= group_size):
            raise ValueError(f"num_passing {n_pass} out of range for group_size {group_size}")
        if n_pass == 0:
            buckets.too_hard.append(prompt_id)
        elif n_pass == group_size:
            buckets.too_easy.append(prompt_id)
        else:
            buckets.learnable.append(prompt_id)
    return buckets


def gate(pass_counts, group_size: int, min_learnable_fraction: float = 0.30) -> dict:
    """Decide whether the training set has enough learning signal to start GRPO.

    Returns:
        dict(pass_gate, learnable_fraction, buckets). If pass_gate is False the data
        is too easy/hard -- re-bucket, resource harder problems, or reconsider the
        init checkpoint (Phase 5 gate / risk register: "GRPO reward flat").
    """
    buckets = bucket_prompts(pass_counts, group_size)
    frac = buckets.learnable_fraction
    return {
        "pass_gate": frac >= min_learnable_fraction,
        "learnable_fraction": frac,
        "buckets": buckets,
    }
