#!/usr/bin/env python3
"""Build data v0.x: MBPP+ through the bug factory (mirrors notebooks/02_data_pipeline).

CPU-only. Outputs into the repo's data/ directory (committed, versioned):
    data/data_v0_bugs.json         certified training bugs
    data/data_v0_restraint.json    verified-clean originals (restraint suite)
    data/contamination_drops.json  functions excluded by the exam screen

Run:  python scripts/build_data_v0.py   (needs `pip install datasets`)
"""
import ast
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from mutate import generate_mutants, select_mutants, assign_split  # noqa: E402

from datasets import load_dataset  # noqa: E402

OUT = ROOT / "data"


def def_names(src):
    try:
        return [n.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef)]
    except SyntaxError:
        return None


def normalize(src):
    try:
        return ast.unparse(ast.parse(src))
    except SyntaxError:
        return None


def run_with_tests(source, row, timeout=6):
    prog = "\n".join(list(row["test_imports"]) + [source] + list(row["test_list"]))
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(prog)
        path = f.name
    try:
        r = subprocess.run([sys.executable, path], capture_output=True, timeout=timeout)
        return "pass" if r.returncode == 0 else "fail"
    except subprocess.TimeoutExpired:
        return "timeout"
    finally:
        os.unlink(path)


def certify(row, budget=3, max_per_cat=4):
    """Round-robin across categories, validating until `budget` real bugs found."""
    stats = Counter()
    try:
        cands = generate_mutants(row["code"], max_per_category=max_per_cat)
    except SyntaxError:
        return [], stats
    by_cat = defaultdict(list)
    for m in cands:
        by_cat[m.category].append(m)
    valid = []
    while len(valid) < budget and any(by_cat.values()):
        for cat in sorted(by_cat):
            if len(valid) >= budget or not by_cat[cat]:
                continue
            m = by_cat[cat].pop(0)
            try:
                compile(m.source, "<mutant>", "exec")
            except (SyntaxError, ValueError):
                stats["broken"] += 1
                continue
            v = run_with_tests(m.source, row)
            if v == "fail":
                stats["valid"] += 1
                valid.append(m)
            elif v == "timeout":
                stats["timeout_bug"] += 1
                valid.append(m)  # an infinite loop IS a bug
            else:
                stats["equivalent"] += 1
    return valid, stats


def main():
    mbpp = load_dataset("evalplus/mbppplus", split="test")
    exam = load_dataset("bigcode/humanevalpack", "python", split="test")
    print(f"{len(mbpp)} candidate functions | {len(exam)} exam problems")

    # contamination screen
    exam_names = {row["entry_point"] for row in exam}
    exam_solutions = {normalize(row["prompt"] + row["canonical_solution"]) for row in exam}
    problems, dropped = [], []
    for row in mbpp:
        names = def_names(row["code"])
        if not names:
            dropped.append((row["task_id"], "unparseable"))
        elif set(names) & exam_names:
            dropped.append((row["task_id"], f"name collision: {sorted(set(names) & exam_names)}"))
        elif normalize(row["code"]) in exam_solutions:
            dropped.append((row["task_id"], "solution overlap"))
        else:
            problems.append(row)
    print(f"{len(problems)} pass the contamination screen; {len(dropped)} dropped: {dropped}")

    # gold-sanity gate
    with ThreadPoolExecutor(max_workers=4) as pool:
        verdicts = list(pool.map(lambda row: run_with_tests(row["code"], row), problems))
    gold = [row for row, v in zip(problems, verdicts) if v == "pass"]
    print(f"gold-sanity gate: {len(gold)}/{len(problems)} pass")

    # factory
    records, totals = [], Counter()
    for i, row in enumerate(gold):
        valid, stats = certify(row)
        totals.update(stats)
        picked = select_mutants(valid, k=2, seed=int(row["task_id"]))
        split = assign_split(row["code"])
        for j, m in enumerate(picked):
            records.append({
                "id": f"Mbpp/{row['task_id']}-{m.category}-{j}",
                "source_task": f"Mbpp/{row['task_id']}",
                "split": split,
                "category": m.category,
                "description": m.description,
                "buggy": m.source,
                "fixed": row["code"],
                "test_imports": list(row["test_imports"]),
                "test_list": list(row["test_list"]),
            })
        if (i + 1) % 50 == 0:
            print(f"{i+1}/{len(gold)} functions, {len(records)} bugs")

    # report
    checked = sum(totals.values())
    print("\n=== CERTIFICATION ===")
    for k in ("valid", "equivalent", "broken", "timeout_bug"):
        print(f"  {k:<12} {totals[k]:>5}  ({totals[k]/max(checked,1)*100:.1f}% of {checked})")
    print(f"\n=== KEPT: {len(records)} certified bugs ===")
    for cat, n in Counter(r["category"] for r in records).most_common():
        print(f"  {cat:<18} {n:>4}")
    for sp, n in Counter(r["split"] for r in records).most_common():
        print(f"  {sp:<18} {n:>4}")
    print("source functions contributing:", len({r["source_task"] for r in records}))

    # save
    restraint = [{
        "id": f"Mbpp/{row['task_id']}-clean",
        "source_task": f"Mbpp/{row['task_id']}",
        "split": assign_split(row["code"]),
        "code": row["code"],
        "test_imports": list(row["test_imports"]),
        "test_list": list(row["test_list"]),
    } for row in gold]
    OUT.mkdir(exist_ok=True)
    json.dump(records, open(OUT / "data_v0_bugs.json", "w"), indent=1)
    json.dump(restraint, open(OUT / "data_v0_restraint.json", "w"), indent=1)
    json.dump([{"task_id": t, "reason": r} for t, r in dropped],
              open(OUT / "contamination_drops.json", "w"), indent=1)
    print(f"\nSaved to {OUT}/: data_v0_bugs.json, data_v0_restraint.json, contamination_drops.json")


if __name__ == "__main__":
    main()
