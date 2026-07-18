"""Mutation-based bug injection — the Phase 2 data backbone (Amendment A1).

Take a verified-correct Python function (with tests) and deliberately break it in
exactly one place, in one of the six ways the benchmark's taxonomy names. The
un-broken originals double as the restraint suite for free.

Rules enforced here (A1):
- Every mutant must COMPILE and FAIL at least one test, else it is discarded
  (`validate_mutant` returns "broken" / "equivalent" — the equivalent-mutant trap).
- Mutant generation is deterministic (no RNG); selection (`select_mutants`) caps
  mutants per source function and prefers distinct categories (diversity over
  multiplicity, AceReason 2506.13284).
- Train/dev/held-out assignment happens at the FUNCTION level via `assign_split`,
  so mutants of one function can never straddle splits.

Execution safety note: `validate_mutant` runs code in-process. That is fine for
OUR OWN unit tests and for teacher-verified corpora processed in a Colab VM; the
GRPO reward path must still use the sandboxed runner (Phase 5), never this.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import random
from dataclasses import dataclass

TAXONOMY = (
    "operator_misuse",
    "value_misuse",
    "variable_misuse",
    "missing_logic",
    "excess_logic",
    "function_misuse",
)

_BINOP_SWAPS = {
    ast.Add: ast.Sub, ast.Sub: ast.Add,
    ast.Mult: ast.FloorDiv, ast.FloorDiv: ast.Mult,
    ast.Div: ast.Mult, ast.Mod: ast.FloorDiv,
}
_CMPOP_SWAPS = {
    ast.Lt: ast.LtE, ast.LtE: ast.Lt,
    ast.Gt: ast.GtE, ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
}
_BOOLOP_SWAPS = {ast.And: ast.Or, ast.Or: ast.And}
_CALL_SWAPS = {
    "min": "max", "max": "min",
    "sum": "len", "len": "sum",
    "sorted": "reversed",
    "append": "pop", "add": "discard",
}


@dataclass(frozen=True)
class Mutant:
    category: str
    description: str
    source: str


def _is_docstring(stmt) -> bool:
    return (isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str))


def _unparse(tree) -> str:
    return ast.unparse(ast.fix_missing_locations(tree))


# --- per-category candidate enumeration + application ------------------------
# Every generator yields (description, mutated_source). Enumeration order over
# ast.walk is deterministic, so the same input always yields the same mutants.

def _op_sites(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and type(node.op) in _BINOP_SWAPS:
            yield node
        elif isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in _CMPOP_SWAPS:
            yield node
        elif isinstance(node, ast.BoolOp) and type(node.op) in _BOOLOP_SWAPS:
            yield node


def _mutants_operator(source):
    base = ast.parse(source)
    for n in range(sum(1 for _ in _op_sites(base))):
        tree = ast.parse(source)
        node = list(_op_sites(tree))[n]
        if isinstance(node, ast.BinOp):
            old, new = type(node.op).__name__, _BINOP_SWAPS[type(node.op)].__name__
            node.op = _BINOP_SWAPS[type(node.op)]()
        elif isinstance(node, ast.Compare):
            old, new = type(node.ops[0]).__name__, _CMPOP_SWAPS[type(node.ops[0])].__name__
            node.ops[0] = _CMPOP_SWAPS[type(node.ops[0])]()
        else:
            old, new = type(node.op).__name__, _BOOLOP_SWAPS[type(node.op)].__name__
            node.op = _BOOLOP_SWAPS[type(node.op)]()
        yield Mutant("operator_misuse", f"swapped {old} -> {new}", _unparse(tree))


def _value_sites(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (bool, int, float)):
            yield node


def _mutants_value(source):
    base = ast.parse(source)
    for n in range(sum(1 for _ in _value_sites(base))):
        tree = ast.parse(source)
        node = list(_value_sites(tree))[n]
        old = node.value
        node.value = (not old) if isinstance(old, bool) else old + 1
        yield Mutant("value_misuse", f"constant {old!r} -> {node.value!r}", _unparse(tree))


def _name_candidates(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.update(a.arg for a in node.args.args)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
    return sorted(names)


def _load_sites(tree, candidates):
    cand = set(candidates)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in cand:
            yield node


def _mutants_variable(source):
    base = ast.parse(source)
    candidates = _name_candidates(base)
    if len(candidates) < 2:
        return
    for n in range(sum(1 for _ in _load_sites(base, candidates))):
        tree = ast.parse(source)
        node = list(_load_sites(tree, candidates))[n]
        old = node.id
        node.id = candidates[(candidates.index(old) + 1) % len(candidates)]
        yield Mutant("variable_misuse", f"variable {old} -> {node.id}", _unparse(tree))


def _stmt_sites(tree, min_len):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.For,
                             ast.While, ast.If, ast.With, ast.Try)):
            for field in ("body", "orelse", "finalbody"):
                lst = getattr(node, field, None) or []
                if len(lst) < min_len:
                    continue
                for i, stmt in enumerate(lst):
                    if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and field == "body" and i == 0 and _is_docstring(stmt)):
                        continue
                    yield (node, field, i)


def _mutants_missing(source):
    base = ast.parse(source)
    for n in range(sum(1 for _ in _stmt_sites(base, min_len=2))):
        tree = ast.parse(source)
        node, field, i = list(_stmt_sites(tree, min_len=2))[n]
        removed = getattr(node, field).pop(i)
        yield Mutant("missing_logic", f"deleted statement: {ast.unparse(removed)!r}", _unparse(tree))


# Excess-logic v2 (data v0 finding: naive duplication was ~always equivalent —
# recomputing a pure value is invisible. Only EFFECTFUL insertions make real bugs.)
_MUTATOR_CALLS = {"append", "add", "insert", "extend", "remove", "pop", "discard",
                  "update", "sort", "reverse", "clear"}


def _is_effectful(stmt) -> bool:
    """Would executing this statement twice differ from once?"""
    if isinstance(stmt, ast.AugAssign):
        return True
    if isinstance(stmt, ast.Assign):
        targets = {t.id for t in stmt.targets if isinstance(t, ast.Name)}
        rhs = {n.id for n in ast.walk(stmt.value) if isinstance(n, ast.Name)}
        return bool(targets & rhs)  # e.g. s = s + x
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        f = stmt.value.func
        return isinstance(f, ast.Attribute) and f.attr in _MUTATOR_CALLS
    return False


def _dup_sites(tree):
    for node, field, i in _stmt_sites(tree, min_len=1):
        if _is_effectful(getattr(node, field)[i]):
            yield (node, field, i)


def _loop_sites(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)):
            yield node


def _hoist_sites(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            start = 1 if body and _is_docstring(body[0]) else 0
            if len(body) - start >= 2 and isinstance(body[-1], ast.Return):
                yield node


def _mutants_excess(source):
    base = ast.parse(source)
    for n in range(sum(1 for _ in _dup_sites(base))):
        tree = ast.parse(source)
        node, field, i = list(_dup_sites(tree))[n]
        lst = getattr(node, field)
        lst.insert(i, copy.deepcopy(lst[i]))
        yield Mutant("excess_logic",
                     f"duplicated effectful statement: {ast.unparse(lst[i])!r}",
                     _unparse(tree))
    for n in range(sum(1 for _ in _loop_sites(base))):
        tree = ast.parse(source)
        list(_loop_sites(tree))[n].body.append(ast.Break())
        yield Mutant("excess_logic", "inserted spurious break at end of loop body",
                     _unparse(tree))
    for n in range(sum(1 for _ in _hoist_sites(base))):
        tree = ast.parse(source)
        fn = list(_hoist_sites(tree))[n]
        start = 1 if _is_docstring(fn.body[0]) else 0
        fn.body.insert(start, copy.deepcopy(fn.body[-1]))
        yield Mutant("excess_logic",
                     f"inserted premature {ast.unparse(fn.body[start])!r}",
                     _unparse(tree))


def _call_sites(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _CALL_SWAPS:
                yield node
            elif isinstance(node.func, ast.Attribute) and node.func.attr in _CALL_SWAPS:
                yield node


def _mutants_function(source):
    base = ast.parse(source)
    for n in range(sum(1 for _ in _call_sites(base))):
        tree = ast.parse(source)
        node = list(_call_sites(tree))[n]
        if isinstance(node.func, ast.Name):
            old = node.func.id
            node.func.id = _CALL_SWAPS[old]
        else:
            old = node.func.attr
            node.func.attr = _CALL_SWAPS[old]
        yield Mutant("function_misuse", f"call {old} -> {_CALL_SWAPS[old]}", _unparse(tree))


_GENERATORS = {
    "operator_misuse": _mutants_operator,
    "value_misuse": _mutants_value,
    "variable_misuse": _mutants_variable,
    "missing_logic": _mutants_missing,
    "excess_logic": _mutants_excess,
    "function_misuse": _mutants_function,
}


def generate_mutants(source: str, categories=None, max_per_category: int | None = None):
    """All candidate single-edit mutants of `source`, deterministically.

    These are CANDIDATES — they have not been validated. Run each through
    `validate_mutant` before letting it anywhere near training data.
    """
    ast.parse(source)  # raise early on bad input
    out = []
    for cat in (categories or TAXONOMY):
        produced = 0
        for m in _GENERATORS[cat](source):
            out.append(m)
            produced += 1
            if max_per_category is not None and produced >= max_per_category:
                break
    return out


# --- validation (the equivalent-mutant trap) ---------------------------------

def make_case_test(fn_name: str, cases):
    """Build a test callable from (args_tuple, expected) pairs.

    The callable takes an exec'd namespace and returns True iff every case
    matches. Any exception counts as failure (a crashing mutant IS a bug).
    """
    def run(ns):
        fn = ns.get(fn_name)
        if fn is None:
            return False
        try:
            return all(fn(*args) == expected for args, expected in cases)
        except Exception:
            return False
    return run


def _exec_source(source: str):
    ns: dict = {}
    try:
        exec(compile(source, "<candidate>", "exec"), ns)
    except Exception:
        return None
    return ns


def validate_mutant(original_source: str, mutant_source: str, test) -> str:
    """Classify a candidate mutant: 'valid' | 'equivalent' | 'broken'.

    - the ORIGINAL must pass its own tests, else ValueError (bad gold — fix the
      corpus, don't mutate garbage);
    - 'broken'     = mutant does not even execute/compile (not a training bug);
    - 'equivalent' = mutant passes all tests (either an equivalent mutant or a
      weak test suite — discard either way, never train on it);
    - 'valid'      = compiles AND fails >=1 test. This is a usable training bug.
    """
    ns = _exec_source(original_source)
    if ns is None or not test(ns):
        raise ValueError("original does not pass its own tests — bad gold, refusing to mutate")
    ns_m = _exec_source(mutant_source)
    if ns_m is None:
        return "broken"
    return "equivalent" if test(ns_m) else "valid"


# --- selection + splits ------------------------------------------------------

def select_mutants(mutants, k: int = 2, seed: int = 0):
    """Pick at most k validated mutants, preferring distinct categories."""
    pool = list(mutants)
    random.Random(seed).shuffle(pool)
    picked, seen_cats = [], set()
    for m in pool:  # distinct categories first
        if len(picked) >= k:
            return picked
        if m.category not in seen_cats:
            picked.append(m)
            seen_cats.add(m.category)
    for m in pool:  # then fill if we must
        if len(picked) >= k:
            break
        if m not in picked:
            picked.append(m)
    return picked


def assign_split(source: str, train: float = 0.8, dev: float = 0.1) -> str:
    """Deterministic function-level split: 'train' | 'dev' | 'heldout'.

    Hashes the AST-normalized source, so formatting changes don't move a
    function between splits, and every mutant of a function inherits the
    split of its ORIGINAL — call this on the original, never the mutant.
    """
    normalized = ast.unparse(ast.parse(source))
    bucket = int(hashlib.sha256(normalized.encode()).hexdigest(), 16) % 10_000
    if bucket < train * 10_000:
        return "train"
    if bucket < (train + dev) * 10_000:
        return "dev"
    return "heldout"
