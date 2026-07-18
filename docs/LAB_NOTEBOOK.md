# LAB_NOTEBOOK.md — complete session state

*Session 1 closed 2026-07-18 (late night); Session 2 log appended 2026-07-19 — see
"SESSION 2" section near the end, it supersedes sections 1 and 6 where they differ.
Read top to bottom and you can continue the project with zero missing context.*

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

---
---

# SESSION 2 — 2026-07-19 (supersedes sections 1 & 6 above where they differ)

## S2.1 What happened, in order

1. Morning check: repo in sync at `808b48c`, 72 tests green.
2. Built **`src/prompts.py`** — THE canonical training-side prompt, used identically by
   routing/SFT/DPO/GRPO (matched budgets ⇒ no arm gets a formatting advantage).
   Details: `REPAIR_PROMPT` (buggy code + tests in ```python fences, "Return only the
   fixed function in a Python code block"); `build_repair_prompt(buggy, test_list,
   k_visible=3)` — shows AT MOST 3 tests (A1.3 visible/hidden lite: grading always
   runs the FULL test_list); `extract_code(text)` — first ```python fence, else any
   ``` fence, else raw text. +`tests/test_prompts.py` (5 tests) → **suite now 77 green**.
3. Built + pushed **`notebooks/03_routing_pass.ipynb`** (commit `dcd93ab`): L4; k=8
   attempts/bug at temp 1.0 top_p 0.95 max_new_tokens 512 (GRPO's regime);
   PROMPTS_PER_BATCH=4 (32 seqs/forward); checkpoint-resume to Drive
   `phase2/routing_samples_ckpt.json`; grading = subprocess + 6s timeout, 4 workers.
4. **Nidhi ran it successfully.** Smoke healthy (note: model PARROTS the visible tests
   into its answers at temp 1.0 — harmless for grading, but SFT targets must stay
   clean gold fixes). Sampling took 2248s (~37 min) for 544 bugs.
5. **ROUTING RESULTS (Phase 2 finale):**
   - Piles: **sft 97 (17.8%) / rl 376 (69.1%) / easy 71 (13.1%)**
   - **Learnable fraction 69.1%** vs gate ≥30% → **GRPO variance-gate pre-flight PASSED**
   - Mean pass rate over all 4352 attempts: **51.2%** (vs 17.6% on exam — curriculum
     easier than exam, as designed; the gap IS the headroom)
   - Per-category sft/rl/easy: excess 5/49/12 · function 4/60/9 · missing 21/48/5 ·
     operator 32/65/10 · value 27/46/3 · variable 8/108/32
   - Insight for paper: on single-edit train bugs, SUBTLE (operator/value) beats
     STRUCTURAL (excess) as hardest — reversal vs the exam's excess-logic-hardest.
   - Files: Drive `phase2/routing_v0.json` (id, category, pass_count, n, pile) and
     `phase2/routing_samples_ckpt.json` (ALL 4352 attempts — flagged as a ready-made
     DPO pair source for Phase 4: per-bug passing+failing attempts side by side).
6. **Phase 2 declared COMPLETE** (commit `005c197`, README updated).
7. **DeepSeek:** Nidhi created the API account and topped up. Instructed to store the
   key as Colab Secret **`DEEPSEEK_API_KEY`** (notebook access ON) — storage not yet
   confirmed. Explained the trace-arm design to her (she independently re-derived
   rejection-sampling distillation): teacher gets SAME prompt as student, NEVER the
   gold fix (post-hoc rationalization ≠ diagnosis); short 2–4 sentence diagnosis +
   fix; verified by EXECUTION not text-match (many valid fixes exist); fails →
   discard, retry ≤2; coverage footnote (trace set ⊂ bug set, report both sizes).
8. Built + pushed **`notebooks/04_sft_notrace.ipynb`** (commit `5dd7072`) — the FIRST
   TRAINING RUN. Full spec:
   - SEED 3407. Mixture: train bugs with sft-pile ×3 (97×3=291) + rl ×1 (376) +
     easy ×1 (71) = 738, + 150 train-split restraint examples (target = function
     unchanged) ≈ **888 examples, ~17% restraint**; seeded shuffle.
   - Targets: '```python\n{fixed}\n```' (clean gold, fenced to match extract_code).
   - Model: unsloth/Qwen2.5-Coder-1.5B-Instruct, 4-bit, max_seq 1024; LoRA r=32
     α=64 dropout=0 on q/k/v/o/gate/up/down, use_gradient_checkpointing='unsloth'.
   - Masking: `train_on_responses_only(instruction_part='<|im_start|>user\n',
     response_part='<|im_start|>assistant\n')` — loss on answers only.
   - Train: SFTConfig batch 8 × accum 2, lr 2e-4 cosine, warmup 0.05, TWO separate
     1-epoch trainer.train() calls (fresh optimizer each — fine for tracer) with
     dev-eval between; save_strategy 'no', adapters saved manually.
   - Dev eval (`dev_eval`): 61 dev bugs × k=16, temp 1.0 top_p 0.95, max_new 512,
     batch_prompts=2; metrics: pass@1 = mean(c/n), pass@16 = frac(c>0), gap =
     headroom (A2 anti-collapse watch). Base eval via the untrained-LoRA≡base trick
     BEFORE training. Outputs: Drive `phase3/dev_eval_{base,ep1,ep2}_seed3407.json`,
     adapters `phase3/sft_notrace_s3407_ep{1,2}/`.
   - Verdict logic printed in notebook: gate = ep pass@1 > base pass@1; RL-init by
     highest pass@16; if ep2 gap << ep1 gap → epoch 2 ate headroom → prefer ep1.
9. **STATUS AT SAVE: notebook 04 IS RUNNING in Nidhi's Colab right now.** Verdict
   table (3 rows: base/ep1/ep2 × pass@1/pass@16/gap) NOT yet reported — it is the
   FIRST thing to collect next session.

## S2.2 Next actions (supersedes section 6)

1. **Collect notebook-04 verdict table** (or debug if it failed — likely failure
   spots: unsloth install/version drama, OOM at k=16 eval → drop batch_prompts to 1,
   train_on_responses_only signature drift).
2. Interpret per verdict logic above; declare tracer result.
3. **Build 04b_trace_gen.ipynb** (CPU, zero GPU): DeepSeek API
   (base_url https://api.deepseek.com, model 'deepseek-chat', key from Colab Secret
   DEEPSEEK_API_KEY) generates short diagnosis+fix per train bug w/ same
   build_repair_prompt; extract_code → execute vs FULL test_list → keep passers,
   retry ≤2, enforce short traces (~≤512 tok); save trace dataset to Drive/repo.
4. **04c**: SFT trace-arm, 1 seed, same everything as 04 except targets =
   "diagnosis + fenced fix" → A/B verdict on dev (pass@1 AND gap; also compare
   dataset sizes/coverage honestly).
5. Winner → 3 seeds (Phase 3 proper) + forgetting probe + held-out milestone eval
   (ONCE) with taxonomy + restraint tables.
6. Then Phase 4 (DPO — remember routing_samples_ckpt.json as pair source) and
   Phase 5 (GRPO per frozen plan + A2/A1 invariants).

## S2.3 Standing open items (rollover)

- Colab units balance: STILL unreported — ask again.
- DEEPSEEK_API_KEY in Colab Secrets: told, unconfirmed.
- eval/taxonomy.json per-problem map (E1) placeholder; contamination_report.md stub.
- v1 data upgrades: MBPP+ full suites, CommitPackFT tier, hidden-test pools for RL.
- LinkedIn post (i) fully writeable; budget ledger habit.
- Commit chain addition (session 2): dcd93ab prompts+03 → 005c197 Phase-2 complete →
  5dd7072 notebook 04 → (this save).

## S2.4 Notebook-04 VERDICT (2026-07-18, seed 3407, 61 dev bugs, k=16 @ temp 1.0)

| checkpoint | pass@1 | pass@16 | gap |
|---|---|---|---|
| base | 45.9% | 93.4% | 47.5 |
| ep1  | 58.7% | 91.8% | 33.1 |
| ep2  | 62.4% | 82.0% | 19.6 |

- **Gate PASSED**: both epochs beat base pass@1 (45.9 → 58.7 → 62.4). The teaching
  loop (mixture, response-masking, QLoRA r32/α64) works end-to-end.
- **Epoch 2 is the trap A2 predicted**: highest pass@1 but pass@16 collapsed
  91.8 → 82.0 (~7 dev bugs newly unreachable at k=16) and gap 33.1 → 19.6.
  Train loss ~0.06 flat in ep2 = memorization. Selecting by pass@1 would have
  picked it; the pre-committed pass@16 rule rejected it. (Interview gold.)
- **DECISION: no-trace recipe = 1 epoch.** Ep1 trades ~1 bug of pass@16 (within
  noise vs base 93.4) for +12.8 pass@1 — the RL-init profile we want.
- Context guard: dev ≫ exam by design (base dev 45.9 vs exam 17.6). Relative
  decisions only, never headline numbers.
- Run health: ~1:42 per epoch on L4 (56 steps, batch 8×2); warnings observed
  (max_new_tokens/max_length, AttentionMaskConverter deprecation, warmup_ratio
  deprecation) all benign. Adapters + dev evals on Drive phase3/.
- 04b_trace_gen.ipynb built & pushed (962f983): CPU, DeepSeek teacher, key via
  Colab Secrets, verified-by-execution, checkpoint-resume, runs in parallel w/ 04.
- Next: run 04b → 04c trace-arm A/B (same protocol, both epochs + dev evals) →
  winner gets 3 seeds.

## S2.5 Notebook-04b RESULTS (2026-07-18) + 04c built

- **Trace generation: 522/544 verified (96.0%)** in 341 s, $0.13 (134,694 in /
  83,925 out tokens). Mean diagnosis 57 words (cap 120).
- By pile: sft 82/97 (85%), rl 369/376 (98%), easy 71/71. By category, lowest =
  missing_logic 66/74 (reconstructing deleted code from tests alone is hardest).
- Smoke diagnoses healthy — teacher names the actual bug crisply.
- 22 uncovered bugs (15 sft-pile, 7 rl) fall back to gold-fix targets in 04c.
- Artifacts: Drive `phase3/traces_v0.json` (verified only) + `traces_ckpt.json` (all).
- **04c_sft_trace.ipynb built**: identical twin of 04 (seed 3407, same mixture
  recipe/LoRA/trainer/dev-eval) except targets = teacher diagnosis + verified fix
  (fallback gold). Restraint gets template diagnoses (3 variants via rng2 so the
  main rng stream — restraint picks + final shuffle — matches 04 exactly).
  Adds `base2` re-eval as a NOISE RULER (|base−base2| = tie threshold), and its
  final cell loads 04's dev_eval jsons from Drive to print the six-row A/B table.
- Reminded: disconnect 04's L4 runtime (idle burn); units balance still unreported.
