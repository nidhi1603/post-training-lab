# eval/ — the evaluation deliverable

Packaged as a standalone artifact (Phase 7). Execution-verified, judge-free, with
confidence intervals, a bug-taxonomy breakdown, and (built in Phase 2) a restraint
suite. The llm-foundations site has no evals module — this is that missing chapter.

## Contents

| File | What it is | State |
|---|---|---|
| `pass_at_k.py` | Unbiased pass@k estimator + problem-level (clustered) 95% CIs | done, tested |
| `stats.py` | Paired significance: McNemar exact, paired bootstrap, Holm–Bonferroni | done, tested |
| `taxonomy.json` | OctoPack Table 15 bug taxonomy (6 categories, counts sum to 164) | done |
| `taxonomy_breakdown.py` | Per-category pass@k table from a results file | done, tested |
| `contamination_report.md` | n-gram + embedding + function-name audit | Phase 2 |

## Results-file contract

Adapt bigcode-evaluation-harness output to a JSON list, one record per problem:

```json
[{"task_id": "Python/0", "n": 20, "c": 7}, {"task_id": "Python/1", "n": 20, "c": 20}]
```

`n` = samples drawn, `c` = samples whose fix passed all tests.

## Usage

```bash
# Overall + per-category pass@1 with CIs
python3 taxonomy_breakdown.py results/qwen_base.json --k 1

# In code:
python3 - <<'PY'
from pass_at_k import aggregate_pass_at_k, mean_and_ci
from stats import mcnemar_exact
_, pp = aggregate_pass_at_k([(20, 7), (20, 20), (20, 0)], k=1)
print(mean_and_ci(pp))
PY
```

## Still to build

- **Restraint suite** (Phase 2, E2): ~100 verified-clean functions; metric = false-fix rate.
- **Per-problem taxonomy map**: fill `problem_bug_type` in `taxonomy.json` from the
  dataset's bug-type field (Phase 1).
- **Decode-sensitivity appendix** (Phase 7): headline result at 2–3 temperatures/formats.
