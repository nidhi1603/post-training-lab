"""Tests for the canonical training prompt + code extraction."""
from prompts import build_repair_prompt, extract_code

BUGGY = "def add(a, b):\n    return a - b"
TESTS = ["assert add(1, 2) == 3", "assert add(0, 0) == 0",
         "assert add(-1, 1) == 0", "assert add(5, 5) == 10"]


def test_prompt_contains_code_and_caps_visible_tests():
    p = build_repair_prompt(BUGGY, TESTS, k_visible=3)
    assert BUGGY in p
    assert "assert add(1, 2) == 3" in p
    assert "assert add(5, 5) == 10" not in p  # 4th test stays hidden


def test_extract_python_fence():
    text = "Here is the fix:\n```python\ndef add(a, b):\n    return a + b\n```\nDone."
    assert extract_code(text) == "def add(a, b):\n    return a + b"


def test_extract_generic_fence():
    text = "```\ndef f():\n    return 1\n```"
    assert extract_code(text) == "def f():\n    return 1"


def test_extract_prefers_first_python_fence():
    text = "```\nnot this\n```\n```python\ndef g():\n    return 2\n```"
    assert extract_code(text) == "def g():\n    return 2"


def test_extract_falls_back_to_raw_text():
    text = "def h():\n    return 3"
    assert extract_code(text) == "def h():\n    return 3"
