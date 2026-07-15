# EVALS_PLAYBOOK.md — the interview crosswalk

One page mapping what this project builds to the agent-evals vocabulary interviewers
use, so every line of the lab answers an evals question.

| Agent-evals concept (the interview question) | What we built here |
|---|---|
| Tool-selection accuracy (BFCL AST: name/params/type/value match) | patch graded by structural execution match (tests pass) |
| BFCL irrelevance detection / false-invocation rate on gated tools | **restraint suite: false-fix rate on clean code** (Phase 2, E2) |
| τ-bench final-state comparison; pass^k reliability (all k trials succeed) | tests-pass = state check; pass@k *and* per-seed variance reported |
| ToolRL decomposed reward (name/key/value partial credit) | layered reward: compile / partial tests / all tests (`src/reward.py`) |
| AgentDojo: utility under attack, attack success rate | hacking log + read-only sandbox + gold-sanity gate |
| Step-level vs outcome-level trajectory evals | checkpoint dev-slice curves vs final held-out table |
| Error bars / statistical rigor (arXiv 2411.00640) | clustered 95% CIs + paired McNemar / bootstrap (`eval/stats.py`) |

## The gated-MCP answer (memorize)

> "Score selection statistically — name, argument keys, argument values, BFCL-style;
> enforce permissions deterministically at the gate layer and test them as invariants —
> false-invocation rate on denial suites, zero gate-bypass by construction; grade
> multi-step outcomes by final state, τ-bench style, reporting pass^k for reliability."

## How each project artifact maps to a claim you can defend

- **`eval/pass_at_k.py`** — "I use the unbiased Codex estimator, not empirical
  max@k, and I report pass@k because greedy pass@1 hides variance."
- **`eval/stats.py`** — "Comparisons are paired on the shared benchmark; I use McNemar
  on discordant pairs, not overlapping error bars on two independent means."
- **`src/reward.py`** — "The reward is correctness-dominated with a proven invariant:
  no failing patch can out-reward a passing one, so GRPO's mean baseline can't reinforce
  'less wrong' garbage."
- **`src/variance_gate.py`** — "I gate the training set on within-group variance —
  all-pass and all-fail prompts give GRPO zero signal, so I don't pay to roll them out."
- **restraint suite (Phase 2)** — "I measure false-fix rate on verified-clean code —
  the code-repair analog of BFCL irrelevance detection. A system that can't stay quiet
  is broken."
- **`eval/contamination_report.md`** — "n-grams miss logic-preserving edits, so I add an
  embedding decontaminator and a post-cutoff slice."
