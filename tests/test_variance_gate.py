"""Tests for the GRPO pre-flight variance gate."""
import pytest

from variance_gate import bucket_prompts, gate


def test_buckets_split_correctly():
    counts = [("a", 0), ("b", 8), ("c", 4), ("d", 1), ("e", 7)]
    buckets = bucket_prompts(counts, group_size=8)
    assert buckets.too_hard == ["a"]
    assert buckets.too_easy == ["b"]
    assert sorted(buckets.learnable) == ["c", "d", "e"]


def test_learnable_fraction():
    counts = [("a", 0), ("b", 8), ("c", 4), ("d", 4)]
    buckets = bucket_prompts(counts, group_size=8)
    assert buckets.learnable_fraction == pytest.approx(0.5)


def test_gate_passes_and_fails():
    good = [("p%d" % i, 4) for i in range(10)]  # all mixed
    assert gate(good, group_size=8)["pass_gate"] is True

    bad = [("p%d" % i, 0) for i in range(9)] + [("p9", 4)]  # 10% learnable
    out = gate(bad, group_size=8, min_learnable_fraction=0.30)
    assert out["pass_gate"] is False
    assert out["learnable_fraction"] == pytest.approx(0.1)


def test_group_size_must_be_at_least_two():
    with pytest.raises(ValueError):
        bucket_prompts([("a", 0)], group_size=1)


def test_pass_count_out_of_range_raises():
    with pytest.raises(ValueError):
        bucket_prompts([("a", 9)], group_size=8)
