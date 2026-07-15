"""Per-category pass@1 breakdown of a generations/results file.

Evals-track step E1: from now on every eval produces a taxonomy table, not just one
number. This turns a per-problem results file plus the problem->category map in
taxonomy.json into a pass@k breakdown by bug type, with confidence intervals.

Results-file contract (JSON): a list of records, one per problem, each with
    {"task_id": <str>, "n": <int>, "c": <int>}
where n = samples drawn and c = samples whose fix passed all tests. This is the
minimal, harness-agnostic shape; adapt your bigcode-evaluation-harness output to it.
"""
from __future__ import annotations

import json
from pathlib import Path

from pass_at_k import aggregate_pass_at_k, mean_and_ci


def load_taxonomy(taxonomy_path):
    tax = json.loads(Path(taxonomy_path).read_text())
    bug_type = tax.get("problem_bug_type", {})
    # Drop the placeholder key if the map hasn't been filled yet.
    bug_type = {k: v for k, v in bug_type.items() if not k.startswith("_")}
    return tax, bug_type


def breakdown(results_path, taxonomy_path, k: int = 1) -> dict:
    """Compute overall and per-category pass@k with CIs.

    Returns:
        dict(overall=<ci dict>, by_category={cat: <ci dict + n_problems>},
             unmapped=[task_ids without a category]).
    """
    records = json.loads(Path(results_path).read_text())
    _, bug_type = load_taxonomy(taxonomy_path)

    by_cat_counts: dict[str, list] = {}
    all_counts = []
    unmapped = []
    for r in records:
        counts = (int(r["n"]), int(r["c"]))
        all_counts.append(counts)
        cat = bug_type.get(str(r["task_id"]))
        if cat is None:
            unmapped.append(r["task_id"])
            continue
        by_cat_counts.setdefault(cat, []).append(counts)

    _, overall_pp = aggregate_pass_at_k(all_counts, k)
    result = {"overall": mean_and_ci(overall_pp), "by_category": {}, "unmapped": unmapped}
    for cat, counts in sorted(by_cat_counts.items()):
        _, pp = aggregate_pass_at_k(counts, k)
        result["by_category"][cat] = mean_and_ci(pp)
    return result


def format_table(result: dict, k: int = 1) -> str:
    """Render breakdown() output as a fixed-width table for the lab notebook."""
    lines = [f"category           pass@{k}    95% CI            n"]
    lines.append("-" * 52)
    o = result["overall"]
    lines.append(f"{'OVERALL':<18} {o['mean']*100:6.2f}%  [{o['ci_low']*100:5.2f}, {o['ci_high']*100:5.2f}]  {o['n_problems']:>4}")
    for cat, ci in result["by_category"].items():
        lines.append(f"{cat:<18} {ci['mean']*100:6.2f}%  [{ci['ci_low']*100:5.2f}, {ci['ci_high']*100:5.2f}]  {ci['n_problems']:>4}")
    if result["unmapped"]:
        lines.append(f"\n[warn] {len(result['unmapped'])} problems had no category mapping.")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Per-category pass@k breakdown.")
    ap.add_argument("results", help="JSON results file: [{task_id, n, c}, ...]")
    ap.add_argument("--taxonomy", default=str(Path(__file__).parent / "taxonomy.json"))
    ap.add_argument("--k", type=int, default=1)
    args = ap.parse_args()
    print(format_table(breakdown(args.results, args.taxonomy, args.k), args.k))
