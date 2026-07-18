"""Tests for the mutation-based bug factory (Amendment A1)."""
import pytest

from mutate import (
    TAXONOMY,
    Mutant,
    assign_split,
    generate_mutants,
    make_case_test,
    select_mutants,
    validate_mutant,
)

ADD_SRC = "def add(a, b):\n    return a + b\n"
ADD_TEST = make_case_test("add", [((2, 3), 5), ((0, 0), 0), ((-1, 1), 0)])

TOTAL_SRC = (
    "def total(xs):\n"
    "    s = 0\n"
    "    for x in xs:\n"
    "        s = s + x\n"
    "    return s\n"
)
TOTAL_TEST = make_case_test("total", [(([1, 2, 3],), 6), (([],), 0), (([5],), 5)])

BIGGEST_SRC = "def biggest(xs):\n    return max(xs)\n"
BIGGEST_TEST = make_case_test("biggest", [(([1, 2],), 2), (([3, 1, 2],), 3)])

CLAMP_SRC = (
    "def clamp(x, lo, hi):\n"
    "    if x < lo:\n"
    "        return lo\n"
    "    if x > hi:\n"
    "        return hi\n"
    "    return x\n"
)
# Deliberately boundary-blind tests: cannot tell < from <= at x == lo.
CLAMP_WEAK_TEST = make_case_test("clamp", [((5, 0, 10), 5), ((0, 0, 10), 0), ((11, 0, 10), 10)])


def test_generation_is_deterministic():
    a = generate_mutants(TOTAL_SRC)
    b = generate_mutants(TOTAL_SRC)
    assert a == b
    assert all(isinstance(m, Mutant) for m in a)


def test_operator_mutant_is_valid_bug():
    ms = [m for m in generate_mutants(ADD_SRC, categories=["operator_misuse"])]
    assert len(ms) == 1  # the single '+' swaps to '-'
    assert validate_mutant(ADD_SRC, ms[0].source, ADD_TEST) == "valid"


def test_variable_mutant_is_valid_bug():
    ms = generate_mutants(ADD_SRC, categories=["variable_misuse"])
    # loads of a and b each swap to the other name
    assert len(ms) == 2
    verdicts = {validate_mutant(ADD_SRC, m.source, ADD_TEST) for m in ms}
    assert "valid" in verdicts


def test_missing_and_excess_logic_on_loop():
    missing = generate_mutants(TOTAL_SRC, categories=["missing_logic"])
    excess = generate_mutants(TOTAL_SRC, categories=["excess_logic"])
    assert missing and excess
    assert any(validate_mutant(TOTAL_SRC, m.source, TOTAL_TEST) == "valid" for m in missing)
    assert any(validate_mutant(TOTAL_SRC, m.source, TOTAL_TEST) == "valid" for m in excess)


def test_value_mutant_off_by_one():
    ms = generate_mutants(TOTAL_SRC, categories=["value_misuse"])
    assert any(
        validate_mutant(TOTAL_SRC, m.source, TOTAL_TEST) == "valid" for m in ms
    )  # s = 0 -> s = 1 breaks total([]) == 0


def test_function_misuse_swaps_call():
    ms = generate_mutants(BIGGEST_SRC, categories=["function_misuse"])
    assert len(ms) == 1 and "max -> min" in ms[0].description
    assert validate_mutant(BIGGEST_SRC, ms[0].source, BIGGEST_TEST) == "valid"


def test_equivalent_mutant_is_caught_by_weak_tests():
    # x < lo -> x <= lo is invisible to boundary-blind tests: MUST be discarded,
    # exactly the trap the A1 rule exists for.
    ms = generate_mutants(CLAMP_SRC, categories=["operator_misuse"])
    lt_swap = next(m for m in ms if "Lt -> LtE" in m.description)
    assert validate_mutant(CLAMP_SRC, lt_swap.source, CLAMP_WEAK_TEST) == "equivalent"


def test_broken_mutant_is_flagged():
    assert validate_mutant(ADD_SRC, "def add(a, b:\n    return", ADD_TEST) == "broken"


def test_bad_gold_refuses_to_mutate():
    with pytest.raises(ValueError):
        validate_mutant(ADD_SRC, ADD_SRC, make_case_test("add", [((1, 1), 99)]))


def test_select_caps_and_diversifies():
    ms = generate_mutants(TOTAL_SRC)
    picked = select_mutants(ms, k=2, seed=7)
    assert len(picked) == 2
    assert len({m.category for m in picked}) == 2  # two distinct categories
    assert select_mutants(ms, k=2, seed=7) == picked  # deterministic


def test_split_is_deterministic_and_format_insensitive():
    s1 = assign_split(ADD_SRC)
    s2 = assign_split("def add(a, b):\n\n    return a + b\n")  # extra blank line
    assert s1 == s2
    assert s1 in ("train", "dev", "heldout")


def test_split_covers_all_buckets():
    buckets = {
        assign_split(f"def f{i}(x):\n    return x + {i}\n") for i in range(300)
    }
    assert buckets == {"train", "dev", "heldout"}


def test_all_categories_reachable():
    src = (
        "def process(xs, threshold):\n"
        "    total = 0\n"
        "    for x in xs:\n"
        "        if x > threshold:\n"
        "            total = total + x\n"
        "    return max(total, 0)\n"
    )
    cats = {m.category for m in generate_mutants(src)}
    assert cats == set(TAXONOMY)
