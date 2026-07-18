# LAB_NOTEBOOK.md — complete session state

*Session 1 closed 2026-07-18 (late night). This file is the full-detail handoff: read it
top to bottom and you can continue the project with zero missing context.*

---

## 0. The project in one breath

Teach **Qwen2.5-Coder-1.5B-Instruct** to fix buggy Python three ways — **SFT** (imitate
verified fixes), **DPO** (prefer passing over failing), **GRPO** (RL, reward = tests
pass) — under matched budgets, measured on **HumanEvalFix** (164 problems) with a
frozen protocol. Controls: random-reward run, 3 seeds/arm, cross-family rerun on
**Llama-3.2-3B-Instruct**. Deliverables: GitHub repo, HF models, LinkedIn posts, arXiv
preprint. **Locked target: beat OctoCoder-16B's 30.4% pass@1 with the 1.5B model**
(stretch: GPT-4 row ~47%). Full plan: `RL_Project_Master_Workflow.md` (+ Amendments
A1, A2 at its end). Reading log: `docs/READING_UPDATES.md` (3 dated passes).

## 1. Status by phase

| Phase | Status |
|---|---|
| 0 Setup | ✅ complete (incl. Milestone 0: Unsloth GRPO smoke, 250 steps T4, ~3 units) |
| 1 Baselines | ✅ complete + audited; **EVAL_PROTOCOL.md FROZEN 2026-07-18** |
| 2 Data | ✅ core complete (data v0.1 committed to repo `data/`); **1 errand left: GPU routing pass (notebook 03, not yet built)** |
| 3 SFT | ⏳ next after routing |
| 4–8 | pending |

## 2. Every number we have

**Baselines (frozen protocol: temp 0.2, top_p 0.95, n=20, bf16, L4, batch 16/8,
max_length_generation 2048, seed 0, `--prompt instruct`, harness commit
`8fc5bae6479c4fbbb28c3f8b644f6a15b3f3b5bd`):**

| Model | pass@1 | pass@10 | 95% CI (audited) | Reachable (≥1 hit in 20) | Pure-RL ceiling |
|---|---|---|---|---|---|
| Qwen2.5-Coder-1.5B-Instruct | **17.59%** | 23.50% | [12.13, 23.05] | 42/164 | ≈25.6% (**below target → SFT is load-bearing**) |
| Llama-3.2-3B-Instruct (validation arm ONLY) | **29.94%** | 47.35% | [23.78, 35.54] | 83/164 | ≈50.6% (huge RL headroom) |

- Independent re-grade agreement: Qwen gap 0.00 pts; Llama 0.28 pts (our 8s timeout vs
  harness stricter default). Llama model revision `0cb88a4f764b7a12671c53f0838cd831a0843b95`.
- Failure species (of failed attempts): Qwen 99.4% wrong_logic / 0.6% broken_syntax /
  0 stutter; Llama 98.2% / 0.4% / **1.4% stutter**. → No free format points; gains must
  come from actual repair skill.
- Full audit tables: `eval/results/phase1_audit.md`.

**Data v0.1 (commit `94b9707`, in repo `data/`):** 378 MBPP+ → 4 contamination drops
(name collisions: Mbpp/99 decimal_to_binary, Mbpp/119 search, Mbpp/309 maximum,
Mbpp/626 triangle_area) → 374 gold-pass (374/374) → 1126 candidates certified → 972
valid / 154 equivalent (13.7% discard) → **672 kept bugs** from 344 functions.
Categories: variable 184 / operator 135 / value 90 / missing 88 / function 88 /
**excess 87**. Splits (function-level hash): train 544 / dev 61 / heldout 67.
Restraint suite: 374 verified-clean originals. Validation gate v0 = MBPP `test_list`
(3–7 asserts; conservative); MBPP+ full-suite integration flagged as v1 upgrade.
Record shape: `{id, source_task, split, category, description, buggy, fixed,
test_imports, test_list}`.

## 3. Frozen / locked decisions (do not re-litigate)

- `EVAL_PROTOCOL.md` FROZEN 2026-07-18. Held-out 164 touched only at milestones.
- Target locked (pre-committed gate fired "below" branch): beat 30.4% with Qwen 1.5B.
- Llama = cross-family validation ONLY; compares vs its own 29.94%, never vs OctoCoder.
- **A1** (2026-07-14): CodeXGLUE cut (Java-only); mutation backbone (MBPP+ +
  gold-gated CommitPackFT later); equivalent-mutant rule; ≤2 mutants/function;
  function-level splits; visible/hidden test split for RL reward; teacher = DeepSeek
  (never Gemini — ToS); restraint = unmutated originals.
- **A2** (2026-07-18): traces ≤512 or none — one-seed A/B trace vs no-trace SFT on dev
  BEFORE 3-seed commit ("Through the Valley" 2506.07712); SFT early-stop/select by dev
  pass@16 + entropy (anti diversity-collapse); stage routing: all-fail→SFT,
  mixed→RL, all-pass→discard (2606.04466).
- GRPO plan (Phase 5, unchanged): Dr.GRPO default, GSPO A/B, DAPO tricks, group 8,
  conservative LR (2607.12640), reward from `src/reward.py` (CoRPO invariant proven:
  min passing 1.25 > max failing 0.30), sandbox read-only, variance gate + mid-run
  re-gating, hidden tests for reward.

## 4. Repo state (github.com/nidhi1603/post-training-lab, public, branch main)

- **72 tests, all green** (`python3 -m pytest -q` at repo root).
- `eval/`: pass_at_k.py, stats.py (McNemar/bootstrap/Holm), taxonomy.json (Table 15;
  `problem_bug_type` map still placeholder — pending E1), taxonomy_breakdown.py,
  results/phase1_audit.md, contamination_report.md (stub).
- `src/`: reward.py, variance_gate.py, **mutate.py (excess v2: effectful-only dup,
  spurious break, premature-return hoist)**.
- `scripts/build_data_v0.py` — regenerates data v0.1 deterministically.
- `notebooks/`: 01_baseline_eval (two-stage smoke/full), 02_data_pipeline (hardened:
  rm-rf + reload + FACTORY VERSION print), 02a_failure_audit (CPU re-grade + species).
- `docs/`: EVALS_PLAYBOOK.md, READING_UPDATES.md (3 passes), hacking_log.md (empty,
  Phase 5), this file.
- Commit chain (chronological): a4b01fc scaffold → bc31f8e A1 → d553567 reading →
  f1b0438/91044a2 Phase-0 → b32f8af Qwen baseline+target → 1adb353 Llama+freeze →
  d8888e3 audit → b957d49 A2 → 01a8b94 pass-3 → 1fb1279 02-notebook → 74a5d27
  excess-v2 → ea48843 harden → 94b9707 data v0.1.

## 5. Accounts / infra facts

- GitHub `nidhi1603`, gh CLI authed (keyring); git identity Nidhi Rajani
  <nidhirajani1603@gmail.com>. Pushes just work.
- HF account **nrajani16**; token stored as Colab Secret `HF_TOKEN` (notebook-access
  ON); Llama-3.2-3B access GRANTED. Login recipe (fresh VM): set
  `os.environ['HF_TOKEN']` + `login(token)` + probe `hf_hub_download(config.json)`.
- Llama loads via `snapshot_download` → pass LOCAL PATH as `--model` (harness chokes
  on hub sharded weights: "does not appear to have a file named pytorch_model.bin").
- Google Drive owner **nidhirajani1626@gmail.com**, folder `rl-post-training/`
  (shared-link editable): `phase1/` has gens/metrics/results/failures for qwen_base +
  llama_base + harness_commit.txt. `phase2/` Drive copies are SUPERSEDED — repo
  `data/` is canonical. Access from this Mac: claude-in-chrome → drive.google.com.
- Colab Pro ~300 units start; spent ≈ 11–15 (M0 ~3, Phase 1 ~8–12); **exact balance
  unknown — ask Nidhi to read it from Colab's resources panel (standing open item)**.
- Local venv with `datasets` lives in the session scratchpad (ephemeral — rebuild
  with `python3 -m venv && pip install datasets` if needed).

## 6. Immediate next actions (in order)

1. **Build notebook 03 (routing pass, GPU L4, ~30 min, ~2 units):** load repo
   `data/data_v0_bugs.json`; Qwen base samples k=8 fixes per TRAIN-split bug at temp
   1.0 (training-style decoding); grade vs test_list in-VM; route: 0/8 solved →
   SFT-emphasis pile, 1–7/8 → RL pile, 8/8 → discard-from-RL (keep for SFT lite/
   restraint); save routed sets to repo via download or Drive; ALSO this doubles as
   the GRPO variance-gate pre-flight data.
2. **Phase 3 SFT arm:** notebook 04. QLoRA on Qwen (r=32, α=64, lr 1e-4→2e-4, loss
   masked to completion), A2 one-seed A/B (short-trace via DeepSeek teacher vs
   no-trace direct-fix) on dev slice, then 3 seeds of the winner; early-stop by dev
   pass@16 + entropy; forgetting probe; milestone eval on held-out (once).
3. Then DPO (pairs from verifier) and GRPO per plan.

## 7. Teaching state (how to work with Nidhi)

- Mode: **ground floor** — plain words, one idea at a time, define jargon on first
  use, she says "next" to advance. She often skips explain-back questions → fold
  checks into doing rather than quizzing repeatedly.
- Concepts covered so far: next-word prediction + dials; training = nudging dials;
  the three teaching styles; temperature/top_p/sampling; why n=20 (pass@1 as a
  probability); pass@k headroom = amplification room; exam-leakage/contamination;
  transformer at block level; LoRA-as-glasses; GRPO grade-book columns (reward,
  reward_std=signal, lengths, kl); 401 vs 403; dict key-vs-value; GPU choice rules
  (fit / bf16 / price); CPU-for-grading; VM disposability ("only Drive/repo is real");
  import-cache + browser-cache staleness ("print the version of what's running").
- Her hands-on wins: ran Milestone 0, both baselines, both audits; debugged HF auth;
  she reads outputs when prompted with specific things to look for.
- Interview gold accumulated: grader-verification story (0.00 gap), the 25.6%-ceiling
  → SFT-necessity argument, the excess-logic 2→87 gate-catches-its-builder story,
  reward-invariant proof, LinkedIn post (i) fully writeable.

## 8. Open items / loose ends

- Colab units balance: unreported (ask).
- `eval/taxonomy.json` per-problem map (E1) still placeholder — fill from
  humanevalpack bug_type field when convenient; enables per-category tables.
- Contamination report doc (`eval/contamination_report.md`) still a stub — Phase 2
  screen results live in data/contamination_drops.json; write up when corpus final.
- v1 data upgrades flagged: MBPP+ full-suite validation; CommitPackFT real-bug tier;
  visible/hidden test pools for RL reward.
- DPO pair generation + DeepSeek teacher account: not yet set up (needed Phase 3/4).
- Weekly budget-ledger habit + LinkedIn post (i): suggested, not yet done.
