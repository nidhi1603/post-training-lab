"""Canonical TRAINING-side prompt for the repair task (Phases 2-5).

One format, used identically by the routing pass, SFT, DPO pair generation, and
GRPO rollouts — so no arm ever gets an accidental formatting advantage.

NOT the eval prompt: the frozen benchmark prompt is the harness's `instruct`
template at commit 8fc5bae (EVAL_PROTOCOL.md) and never changes. Training-side
formatting is free — but must be consistent across arms (matched budgets).

Visible/hidden test split (Amendment A1.3): the prompt SHOWS at most
`k_visible` tests; grading always runs the FULL suite. A policy that hardcodes
what it can see still fails what it cannot.
"""
from __future__ import annotations

import re

REPAIR_PROMPT = """Below is a buggy Python function and tests it must pass. \
Rewrite the complete, fixed function.

Buggy code:
```python
{buggy}
```

Tests:
```python
{tests}
```

Return only the fixed function in a Python code block."""


def build_repair_prompt(buggy: str, test_list, k_visible: int = 3) -> str:
    """Render the repair prompt showing at most k_visible tests."""
    tests = "\n".join(list(test_list)[:k_visible])
    return REPAIR_PROMPT.format(buggy=buggy.rstrip(), tests=tests)


def extract_code(text: str) -> str:
    """Pull the model's code out of a response.

    Preference order: first ```python fence, then any ``` fence, else the raw
    text (some models skip fences at high temperature).
    """
    m = re.search(r"```python\s*\n(.*?)```", text, re.S)
    if m is None:
        m = re.search(r"```\s*\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()
