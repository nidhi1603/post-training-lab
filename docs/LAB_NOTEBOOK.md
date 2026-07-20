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

## S2.6 A/B VERDICT — no-trace WINS (2026-07-18, notebook 04c)

Full table (61 dev bugs, k=16 @ temp 1.0, seed 3407):

| arm | ckpt | pass@1 | pass@16 | gap |
|---|---|---|---|---|
| no-trace | base | 45.9% | 93.4% | 47.5 |
| no-trace | ep1 | **58.7%** | **91.8%** | 33.1 |
| no-trace | ep2 | 62.4% | 82.0% | 19.6 |
| trace | base2 | 45.9% | 93.4% | 47.5 |
| trace | ep1 | 48.9% | 90.2% | 41.3 |
| trace | ep2 | 51.6% | 91.8% | 40.2 |

- **Pre-committed rule applied**: best-epoch vs best-epoch → pass@16 TIES at 91.8
  (no-trace ep1 vs trace ep2) → tie-break by pass@1 → no-trace ep1 wins by 7.1 pts
  (≫ analytic sampling noise ~2–3 pts on 61 bugs). **WINNER: no-trace, 1 epoch.**
- **Negative result (content, per ground rule 7)**: short teacher traces did NOT
  expand the reachable set (pass@16 no better) and slowed repair learning at
  matched budget (train loss 0.35–0.44 vs 0.10; pass@1 +5.7 after 2 ep vs +12.8
  after 1). Observed trace-quality caveat: sampled diagnosis was partially wrong
  (claimed capitalize() issue that wasn't one) even though the fix verified —
  noisy rationales plausibly hurt a 1.5B student.
- **Interesting secondary effect**: traces act as an anti-collapse regularizer —
  trace ep2 kept pass@16 at 91.8 where no-trace ep2 collapsed to 82.0. Slower but
  gentler; still loses at matched budget.
- **Noise-ruler design flaw discovered (honest note)**: base2 == base EXACTLY
  (45.9/93.4/47.5) because both notebooks replay seed 3407 → same RNG stream →
  same samples. We accidentally proved end-to-end determinism across two fresh
  VMs (nice), but measured reproducibility, not noise. Real noise ruler = cross-
  seed spread from notebook 05.
- **DECISION**: SFT arm recipe = no-trace × 1 epoch. `sft_notrace_s3407_ep1` is
  also the shared init for the DPO and GRPO arms (same-init design). Trace-arm
  adapters kept on Drive for the writeup.

## S2.7 Rank ablation queued (2026-07-18)

- Nidhi asked about r=16/α=32 → built `notebooks/05b_rank_ablation.ipynb`:
  one knob (r 32→16, α kept at 2r), seed 3407, winning recipe otherwise,
  ~20 min L4. Verdict cell compares vs the r32 cross-seed spread from 05.
- **Prediction on record: within noise ("rank didn't matter; epochs did").**
  Study config stays r=32/α=64 regardless — this is a write-up ablation only.
- Run order: 05 FIRST (produces the noise ruler), then 05b.

## S2.8 Rank ablation result (2026-07-18, run on A100 — note hardware confound)

| config | params | pass@1 | pass@16 | gap |
|---|---|---|---|---|
| r=32/α=64 (study, L4) | 36.9M | 58.7% | 91.8% | 33.1 |
| r=16/α=32 (A100) | 18.5M | 56.8% | 93.4% | 36.7 |

- Δpass@1 = −1.9, Δpass@16 = +1.6 — both within analytic noise (~2–3 pts / 61
  bugs). **Provisional: prediction held — rank didn't matter, epochs did.**
  Final call after notebook 05's cross-seed spread (the real ruler).
- CONFOUND (honest): rank AND hardware changed together (L4 vs A100 numerics).
  Acceptable for a dev-slice ablation; frozen exam runs stay L4/bf16.
- Direction consistent with capacity story (smaller adapter drifted less from
  base, pass@16 back at 93.4) — noted, not claimed.
- A100 timing: 56 steps in 51 s (2× L4). Adapter saved:
  Drive `phase3/sft_notrace_r16_s3407_ep1`, eval `dev_eval_r16_ep1_seed3407.json`.
- Notebook 05 (3 seeds + restraint probe) still TO RUN — the critical path.

## S2.9 Notebook-05 RESULTS — Phase 3 dev-side COMPLETE (2026-07-18, A100)

Cross-seed table (61 dev bugs, k=16 @ temp 1.0):

| tag | pass@1 | pass@16 | gap |
|---|---|---|---|
| base | 45.9% | 93.4% | 47.5 |
| ep1_seed3407 (L4) | 58.7% | 91.8% | 33.1 |
| ep1_seed42 | 60.2% | 93.4% | 33.2 |
| ep1_seed1234 | 59.5% | 90.2% | 30.6 |

- **SFT arm dev result: pass@1 59.5% ± 0.8 (sd), pass@16 91.8% ± 1.6.** Gate
  passed on every seed (+13–14 pts over base). Recipe is STABLE across seeds
  (pass@1 spread just 1.5 pts) and across L4-vs-A100 hardware.
- **NOISE RULER (official): pass@1 spread 1.5 pts / sd 0.8; pass@16 spread 3.3 /
  sd 1.6.** This is the tie threshold for all future dev-slice comparisons.
- **RL-init (pre-committed rule = highest dev pass@16): seed 42**
  (`phase3/sft_notrace_s42_ep1`, 93.4 pass@16, also top pass@1 60.2).
- **Rank ablation FINAL verdict — my prediction was WRONG**: r16 pass@1 56.8 is
  1.9 pts below the worst r32 seed (58.7) and ~3.4 sd below the r32 mean →
  OUTSIDE the ruler. Halving rank has a small but real pass@1 cost (~2.7 pts),
  pass@16 unaffected (93.4, within range). Hardware confound now largely
  excluded (r32 seeds 42/1234 also ran on A100 and matched the L4 seed).
  Study config r=32/α=64 vindicated. Honest note for write-up: "rank mattered
  a little; epochs mattered a lot."
- **Restraint probe (32 correct dev functions, k=4 @ temp 1.0)**: still-passes
  68/75/68%, returned-unchanged 28/31/32% across seeds. I.e. shown CORRECT code,
  the SFT model breaks it ~25–30% of the time at exploration temperature.
  CAVEATS: no BASE-model probe run yet (missing control — open item), exam
  decode is temp 0.2 (far more conservative), and every exam item has a real
  bug. Matters most for GRPO reward-hacking watch. TODO: base restraint probe.
- A100 note: dev evals ~2× faster than L4; ~51 s/epoch training.

## S2.10 Environment drift incident (2026-07-18, notebook 06 fresh L4 VM)

- `pip install unsloth` now pulls a torchao release built for a newer torch than
  Colab's preinstalled 2.10 → `AttributeError: '_c10d_functional' ... no
  attribute '_wrap_tensor_autograd'` at `from unsloth import FastLanguageModel`
  (import chain: unsloth_zoo → transformers.quantizers → quantizer_torchao →
  torchao.nf4tensor). We never use torchao (bitsandbytes handles 4-bit).
- FIX: `!pip uninstall -y torchao` + Runtime → Restart session → Run all.
  Notebook 06's install cell now does the uninstall automatically for fresh VMs.
- No units lost (failed pre-GPU). Lesson for write-up: the harness commit is
  frozen but the Python dep stack is not fully pinned — record drift incidents.

## S2.11 Second drift incident, same session (notebook 06)

- After harness install (`pip -e .` + `-U transformers accelerate`), the harness
  subprocess died at import: torchaudio ABI mismatch (`undefined symbol:
  torch_dtype_float4_e2m1fn_x2`) — compiled torch add-on no longer matches the
  shuffled torch stack; new transformers imports it merely because it exists.
- FIX: `pip uninstall -y torchaudio torchvision` (both are matched-build add-ons;
  vision would be the next domino). No restart needed — crash was in the
  subprocess. Notebook 06's harness cell now removes torchao/torchaudio/
  torchvision automatically post-install.
- Merge stage had SUCCEEDED before this (merged_s3407 exists on the VM).
- Protocol note: transformers version is not pinned by the harness install (was
  5.5.0 era in Phase 1 per unsloth banners); decode params are all explicit
  flags, but record transformers version with each exam run going forward.
- S2.11 addendum: third domino — with torchvision gone, `accelerate` CLI crashed
  because Colab-preinstalled `timm` hard-imports torchvision. Full strip list is
  now `torchao torchaudio torchvision timm` (all unused by our text-only
  pipeline); notebook 06 updated. Root pattern: "import-if-installed" guards all
  over the HF stack turn any stale preinstalled package into a landmine.

## S2.12 PHASE 3 COMPLETE — held-out milestone (2026-07-18, notebook 06, L4)

| model | pass@1 | pass@10 |
|---|---|---|
| base (Phase 1) | 17.59% | 23.50% |
| SFT s3407 | 23.63% | 32.43% |
| SFT s42 | 21.31% | 27.02% |
| SFT s1234 | 29.51% | 38.35% |
| **SFT mean** | **24.82% (sd ~4.2)** | **32.60%** |

- **STRATEGIC RESULT: the ceiling moved.** Base reachable set (pass@10 23.5%)
  was below the 30.4% target; SFT mean pass@10 = 32.6% (2 of 3 seeds clear the
  target individually; s1234 = 38.35%). SFT-expands confirmed on held-out; RL
  now has room to convert pass@10 into pass@1 past the target. Remaining gap
  for RL: 24.82 → 30.4 = 5.58 pts (mean), with ~7.8 pts of headroom (gap
  pass@10−pass@1).
- +7.23 pts pass@1 from the 672-bug synthetic curriculum. Best seed 29.51
  (0.9 from OctoCoder-16B) — reported as distribution, never cherry-picked.
- **Exam variance ≫ dev variance** (spread 8.2 vs 1.5 pts; sd 4.2 vs 0.8):
  seeds equal in-distribution, very different OOD generalization. Dev ranking
  ANTI-predicted exam ranking (s42 dev-best → exam-worst). Lesson logged.
- **Amendment A3 adopted** (see master workflow): paired-lineage init — DPO/GRPO
  seed i starts from SFT seed i. Supersedes S2.9's "RL-init = seed 42".
- Smoke healthy (clean full-function rewrites; harness extraction fine).
- Cost: ~15 min generation/seed on L4 (~4–5 units total for the milestone).
  Artifacts: Drive phase3/ metrics_sft_s*.json + gens_sft_s*.json (full
  per-attempt generations — reusable for audits/taxonomy breakdown).
- Env note: exam ran on transformers 5.5-era stack post strip-list (S2.10/11).

## S2.13 PHASE 4 RESULTS — DPO = dev-slice TIE (2026-07-19, notebook 07, A100)

| lineage | SFT p@1/p@16 | DPO p@1/p@16 | Δp@1 |
|---|---|---|---|
| s3407 | 58.7 / 91.8 | 61.3 / 93.4 | +2.6 |
| s42 | 60.2 / 93.4 | 60.2 / 93.4 | 0.0 |
| s1234 | 59.5 / 90.2 | 58.9 / 86.9 | −0.6 |

- Means: SFT 59.5 ± 0.8 → DPO 60.1 ± 1.2. **Δ = +0.6 < 1.5-pt ruler → TIE.**
  Inconsistent per-seed signs = noise signature. No pass@16 collapse. Restraint
  same-or-better (s42 probe improved to 78.1/36.7).
- Training itself textbook-healthy: loss 0.693 (log 2) → ~0.63, reward acc
  0.3 → 0.75–0.87, margins growing. Length bias mild (chosen 242 vs rejected
  277 chars). 473 pairs (376 rl + 97 sft-pile gold-vs-fail). ~1.2 min/seed
  train on A100. Pairs cached: Drive phase4/pairs_v0.json.
- s42 DPO row EXACTLY equals its SFT parent (rounding coincidence most likely —
  margins moved during training; noted, not hidden).
- **Mechanistic interpretation (write-up)**: pairs are OFF-policy (base-model
  samples) while the policy starts from SFT — rejected samples showcase
  mistakes the SFT policy largely no longer makes. On-policy GRPO does not have
  this defect → clean three-arm narrative if GRPO now separates.
- **Pre-committed budget decision**: NO separate DPO held-out milestone (dev tie
  + exam sd 4.2 makes +0.6 undetectable; saves ~15 units). DPO takes its one
  exam shot in the Phase-7 final.

## S2.14 Notebook 08 built — GRPO tracer design (seed 3407)

- Init merged SFT s3407 + fresh LoRA r32/α64; KL ref = merged SFT (β=0.04).
  Data = RL pile only (376). 250 steps, G=8, temp 1.0, lr 5e-6 cosine, no vLLM
  (env-drift robustness). ~1.5–2 h on A100, ~20–25 units — most expensive
  notebook yet; tracer-first before 3 seeds.
- **Reward-hacking hole found & closed BEFORE training**: passes()-style
  "returncode==0" grading is exploitable by `sys.exit(0)` (model code runs
  before the asserts in the same file). Hardened runner: per-test try/except
  harness prints a RUN-LOCAL RANDOM SENTINEL + count after tests execute;
  no sentinel → 0 passed. Runner cell self-tests good/bad/hack candidates
  (hack must show passed=0). Uses canonical src/reward.py (CoRPO bounds
  0.30 < 1.25) with output_tokens ≈ chars/4.
- Pre-flight: variance gate ON THE INIT (40 rl-pile bugs × G=8, src/variance_gate)
  — base-model gate was 69% but SFT solves more; STOP if <30%.
- Hacking watch: per-call mean reward + best/worst snippets stream to Drive
  phase5/hacking_watch_s3407.jsonl.
- Caught in authoring: JSON-escaping broke two regexes (sentinel parser, probe
  normalizer) → replaced with escape-proof string ops + added runner self-test.

## S2.15 GRPO TRACER RESULTS — healthy, modest win, best pass@16 yet (2026-07-19)

- Gate on SFT init: **52% learnable** (≥30% ✓). Runner self-test passed (hack
  candidate scored 0). Train: 250 steps, 1h11m on A100, ~2.7 epochs over RL pile.
- Health: reward bounded 1.08–1.26 (flat-to-slight-drift), reward_std 0.05–0.44,
  KL ≈ 0.00005–0.0013 (whisper-quiet), completions ~35–65 tok stable, clipped ≈ 0.
  **No hacking signature.** Hack log clean (phase5/hacking_watch_s3407.jsonl).
- Dev verdict (s3407 lineage): SFT 58.7/91.8/33.1 → DPO 61.3/93.4/32.2 →
  **GRPO 61.0/95.1/34.1**. GRPO = +2.3 pass@1 (just past 1.5 ruler) AND
  pass@16 95.1% (58/61 — best of ANY model incl. base 93.4). The predicted
  on-policy profile: squeeze pass@1 WITHOUT shrinking the reachable set —
  contrast SFT-ep2 (collapse) and offline DPO (tie).
- Restraint probe: 73.4/32.0 (improved vs SFT 68.0/28.1) — execution reward
  implicitly punishes breaking code.
- HONEST CAVEAT: policy moved very little (tiny KL; mean reward ~1.2 → many
  low-variance groups; lr 5e-6 + β 0.04 conservative). Under-trained, the safe
  tracer failure. DECISION: recipe FROZEN as-is for seeds 42/1234 (lineage
  comparability > squeezing the tracer); tuning temptation resisted, logged.
- Tracer result COUNTS as seed 3407's GRPO run (identical recipe). Notebook 09
  = seeds 42 + 1234 only. Est. ~1.5h/seed on A100 (~20 units/seed).

## S2.16 PHASE 5 COMPLETE — full 3-arm × 3-seed dev table (2026-07-19)

| arm | s3407 | s42 | s1234 | mean p@1 (sd) | mean p@16 |
|---|---|---|---|---|---|
| SFT | 58.7/91.8 | 60.2/93.4 | 59.5/90.2 | 59.5 (0.8) | 91.8 |
| DPO | 61.3/93.4 | 60.2/93.4 | 58.9/86.9 | 60.1 (1.2) | 91.3 |
| GRPO | 61.0/95.1 | 60.7/95.1 | 60.3/91.8 | **60.7 (0.3)** | **94.0** |

- **GRPO beats SFT with UNANIMOUS paired signs**: Δp@1 = +2.3/+0.5/+0.8,
  Δp@16 = +3.3/+1.7/+1.6 (6/6 positive). DPO deltas mixed-sign (noise).
- GRPO also CUT cross-seed sd to 0.3 (vs 0.8/1.2) and is the only arm whose
  mean reachable set (94.0) exceeds base (93.4). Held seed-1234's p@16 at 91.8
  where DPO dropped it to 86.9.
- HONEST: mean +1.2 p@1 < 1.5 unpaired ruler — the claim rests on paired
  consistency, not magnitude. Exam decides.
- Seeds 42/1234 runs healthy: gates 40%/50%, rewards bounded 1.08–1.28, KL tiny,
  lengths stable, clipped ≈ 0 (one 0.6% blip s42@175), probes 70.3/71.1
  still-passes. No hacking. ~1h10/seed train on A100 (s1234 47 min).
- Next: notebook 10 = random-reward control (seed 3407, dev-only verdict);
  notebook 11 = Phase-7 FINAL EXAM (DPO+GRPO × 3 seeds on held-out, L4 frozen;
  SFT exam rows already exist from notebook 06). Llama cross-family rerun:
  decision pending units balance (still unreported).

## S2.17 Literature pass 4 (2026-07-19) — "how to beat 30.4"

Papers read (targeted, gap-driven):
- **Repair-R1** (2507.22853, closest prior, same 1.5B model): trains on 5,421
  samples from HumanEval+MBPP+CodeForces+CodeContests w/ GPT-4o-generated
  defects (≥10/sample). Their SFT caused FORGETTING on under-represented
  benchmarks; RL did not. NOTE: they train on HumanEval-derived bugs —
  contamination by OUR rules; their numbers are non-comparable protocol.
- **QiMeng-PRepair** (2604.05963, 2026): EA-GRPO = edit-aware penalty applied
  only to CORRECT samples when group accuracy ≥ α. Qwen2.5-Coder-3B jumped
  +26.7 pts (their protocol) — small models over-edit, and penalizing
  over-editing among correct fixes is a huge small-model lever. "Self-Breaking":
  LLM generates its own buggy variants (10k pairs from 2,869 LeetCode tasks).
- **RAFT/RFT line** (2504.11343 etc.): iterative generate → keep execution-
  passers → SFT is a "surprisingly strong baseline" matching PPO/iter-DPO.
- **DAPO small-model case study**: clip-higher/dynamic-sampling/token-loss can
  HURT tiny models → do NOT adopt DAPO wholesale.

Convergent diagnosis with our own data: (1) our OOD gap (dev 60 vs exam 25) =
data too easy/narrow (672 MBPP-style, no docstrings, single-op AST bugs);
(2) our restraint probe (~30% break-correct-code) = over-editing, exactly what
EA-GRPO targets; (3) our GRPO under-trained (KL ~5e-4) = room for more steps
once data gives more mixed groups.

**V2 PUSH PLAN (post-Phase-7, ordered by expected points/unit):**
1. **Data v1**: 3–5k bugs from HARDER, docstring-style sources (LeetCode-style
   tasks + MBPP+ suites; contamination-screened) with **DeepSeek self-breaking**
   (diverse multi-line semantic bugs, ≥2/function) + keep the execution-
   certification gate. API cost ~$2–5.
2. **SFT v2** on data v1 (1 epoch, frozen recipe) → new lineages.
3. **GRPO v2**: re-gated pile + **edit-aware penalty** (capped to preserve the
   CoRPO invariant) + 500 steps (2× — our KL says under-trained).
4. **RAFT round** if still short: sample k=8 on train bugs w/ best model, keep
   passers, SFT, once or twice. All infra exists.
5. (Optional) Repair-R1's test-generation-first as an auxiliary task — bigger
   surgery, only if 1–4 stall.
SEQUENCING: current controlled study finishes FIRST (notebooks 10+11 as built —
the three-arm result stays clean); v2 push is a separate extension phase.

## S2.18 Notebook 12 built — data v1 factory (v2 push step 1)

- CPU notebook (parallel-safe with notebook 10), DeepSeek self-breaking per
  S2.17: per gold function (374-function v0-restraint pool, MBPP+ suites,
  pre-screened), (1) add docstring — must still pass FULL suite, else fall
  back to original; (2) 6 buggy variants (3 subtle single-line + 3 multi-line/
  compound), taxonomy-labeled; (3) certify compile + fail>=1-of-full-suite
  (timeout = bug), AST-normalize dedupe vs fixed and each other.
- SPLIT RULE: reuse each function's v0 split verbatim — re-hashing forbidden
  (docstring changes the code hash) → zero v0/v1 split leakage. Gold pool
  already contamination-screened in v0; nothing HumanEval-derived.
- Output Drive phase8/: data_v1_bugs.json (= 672 v0 + new, target ~2.5-2.9k
  total; new records tagged gen:'deepseek_v1' + tier), data_v1_restraint.json
  (docstringed clean suite). Checkpoint-resume; est $2-4, 45-90 min.
- Authoring note: sanity-checked the .format() brace escaping by actually
  rendering the template (first check inspected the wrong cell and false-
  alarmed; commit a9bf8a8 landed the notebook, this entry landed after).
- Next: 13 = SFT v2 (frozen recipe, data v1) + routing v1 pass; 14 = GRPO v2
  (re-gated pile, EA-penalty capped under the CoRPO gap, 500 steps). v2 push
  stays clearly separated from the controlled three-arm result (10/11 as-is).

## S2.19 ⭐ CONTROL RESULT — GRPO's dev gain was SPURIOUS (2026-07-19, notebook 10)

| model (3407 lineage) | pass@1 | pass@16 |
|---|---|---|
| SFT | 58.7 | 91.8 |
| GRPO real reward | 61.0 | 95.1 |
| **GRPO RANDOM reward** | **61.1** | **95.1** |

- Coin-flip reward reproduced the real GRPO gain EXACTLY (+2.4/+3.3). Per the
  pre-committed prediction table: **the execution signal contributed nothing
  detectable at this budget** — the gain comes from the RL process itself
  (temp-1.0 sampling + KL-anchored updates + clipping bias concentrating mass
  on the model's own majority behavior). True-pass watch flat (~0.88–1.0):
  noise didn't damage the model either.
- **This is a Spurious-Rewards (2506.10947) replication in code repair at 1.5B**
  — the study's most publishable single finding. It also retroactively explains
  the under-trained symptoms (flat reward ~1.2, KL ~5e-4): the signal never had
  leverage. Reframe for write-up: "RL-shaped training helps; reward CONTENT did
  not matter at this scale/budget/data-difficulty."
- ACTIONS TAKEN: (1) notebook 11 updated — grpo_random_s3407 added to the final
  exam ('grporand' run) so attribution is settled on held-out; (2) GRPO v2 will
  carry a MATCHED random-reward twin from day one (harder data v1 = the regime
  where the signal gets its chance to prove causality).

## S2.20 Data v1 factory RESULTS (2026-07-19, notebook 12)

- **1,879 new certified bugs**, 374/374 functions covered → data v1 = 2,551
  total (3.8× v0). Splits: train 1,532/dev 157/heldout 190 (v0 splits reused,
  no leakage). Tiers: 987 subtle / 892 compound. Categories spread (compound
  379 top; function_misuse 39 rare). Docstringed restraint suite: 374.
- Cost $0.34, ~10 min. Smoke bugs realistic (operator swap, off-by-one, dup-
  variable). Benign SyntaxWarnings from regex-bearing generated code.
- Artifacts: Drive phase8/ data_v1_bugs.json, data_v1_restraint.json,
  v1_factory_ckpt.json. TODO: copy data_v1 files into repo data/ when convenient.
- **Notebook 13 built** — SFT v2 tracer (s3407): plain mixture (2,076 bugs +
  303 restraint ≈ 13%), no routing upweight (v2.0), ctx 1280 for docstrings,
  two-epoch verdict on the v0 61-bug ruler + 60-new-dev view + probes.

## S2.21 SFT v2 tracer verdict — REGRESSED on the v0 ruler; judgment SUSPENDED

Notebook 13 (s3407, v0-dev 61 ruler): v2 ep1 55.1/88.5 (v1: 58.7/91.8 →
−3.6/−3.3, outside the 1.5 band); ep2 56.9/83.6 (pass@16 collapse pattern
CONFIRMED a third time). More data made the old ruler worse.

- CONFOUND flagged before concluding: the v0 ruler is docstring-FREE while v2
  trained 74% docstring-style — the ruler is now partially OOD for v2, and the
  EXAM is docstring-style (looks like the NEW distribution). The v0-dev table
  cannot distinguish "v2 worse" from "v2 shifted toward exam format."
- MISSING outputs requested from Nidhi: both sftv2 newdev eval lines, both
  restraint probes, formatted-example head, and WHICH EPOCH the pasted loss
  table (start ~0.017) belongs to — fine for ep2, red flag if ep1 (04's ep1
  started ~0.23; would suggest a data-path/masking problem).
- **Notebook 13b built**: cross-eval of base + v1-SFT on the SAME 60 new-dev
  bugs (k=8, identical sample via seed) → completes the {base, v1, v2} ×
  {v0-dev, new-dev} matrix. Decision rule pre-stated: v2≫v1 on new-dev while
  v1>v2 on v0-dev = format trade → REBALANCE mixture (e.g. upweight v0-style
  + restore sft-pile×3), not abandon; v1≥v2 on BOTH = v2 recipe genuinely
  worse → investigate before GRPO v2.
- Candidate fixes if rebalancing: v0 bugs ×2-3 upweight (restores old-format
  share + hard-pile emphasis), or mixed-format corpus (strip docstrings from
  half the DeepSeek bugs).

## S2.22 Drift incident #4 — unsloth REMOVED from the exam notebook (2026-07-19)

- Fresh L4 VM, notebook 11: `from unsloth import FastLanguageModel` crashed at
  import — a NEW unsloth_zoo release (traceback shows new gemma4 patch modules)
  triggers torch.compile at import time → inductor chain →
  `ImportError: CUSTOM_KEY from torch.ao.quantization` on Colab's torch build.
- STRUCTURAL FIX instead of another patch: notebook 11 no longer imports
  unsloth AT ALL. Merge chain rewritten in pure peft/transformers
  (PeftModel.from_pretrained + merge_and_unload, bf16, tokenizer copied from
  adapter dir with base-id fallback). Same math as unsloth merged_16bit;
  protocol comparability unaffected. The study's most important notebook now
  depends only on its most stable packages.
- Nidhi given a paste-in replacement cell (no restart needed — failed import
  left no harmful state). Repo copy updated to match.
- Running tally of environment incidents for the write-up: torchao ABI (S2.10),
  torchaudio/torchvision ABI (S2.11), timm hard-dep (S2.11 addendum),
  unsloth_zoo release breakage (this).

## S2.23 ⭐⭐ CONTROLLED STUDY COMPLETE — final exam results (2026-07-19, nb 11)

| model | p@1 | p@10 | | model | p@1 | p@10 |
|---|---|---|---|---|---|---|
| base | 17.59 | 23.50 | | dpo s3407 | 23.45 | 32.11 |
| sft s3407 | 23.63 | 32.43 | | dpo s42 | 21.28 | 27.57 |
| sft s42 | 21.31 | 27.02 | | dpo s1234 | 29.97 | 39.20 |
| sft s1234 | 29.51 | 38.35 | | grpo s3407 | 23.87 | 32.24 |
| grpo-RAND s3407 | 23.29 | 31.49 | | grpo s42 | 22.32 | 29.29 |
| | | | | grpo s1234 | **29.97** | 39.57 |

Means: SFT 24.82 (4.23) | DPO 24.90 (4.52) | GRPO 25.39 (4.04); target −5.01.
- SFT = the entire lift (+7.2). DPO = nothing (deltas −0.18/−0.03/+0.46).
  GRPO = +0.24/+1.01/+0.46 — 3/3 positive AGAIN (9/9 paired across dev+exam)
  but mean +0.57 ≪ exam noise, and the CONTROL (23.29) sits in the same
  cluster → attribution on held-out CONFIRMS dev: process effect, not signal.
- Best singles: dpo s1234 & grpo s1234 both 29.97 — 0.43 from OctoCoder-16B.
- Study verdict: design worked as intended (matched budgets, paired lineages,
  control caught a publishable-looking spurious effect). Llama rerun: LOW ROI
  now (ties + spurious) — recommend skip/defer; v2 push is the live thread.
- TODO next session: McNemar/paired bootstrap on saved gens (local, free).

## S2.24 ⭐ 13b matrix — Story A CONFIRMED + v1-SFT DAMAGE finding

| model | v0-dev p@1/p@16 | new-dev p@1/p@8 |
|---|---|---|
| base | 45.9/93.4 | 54.2/88.3 |
| SFT v1 | 58.7/91.8 | **46.2/76.7 — BELOW BASE** |
| SFT v2 ep1 | 55.1/88.5 | 72.9/83.3 |
| SFT v2 ep2 | 56.9/83.6 | **73.5/91.7** |

- **v1-SFT damaged the model on docstring-style inputs** (−8 p@1 vs base):
  Repair-R1's SFT-forgetting replicated in-house. Retro-explains the exam
  ceiling of the controlled study (~24.8 was format-throttled).
- **Data lever worked**: v2 +19 over base, +27 over v1 on the exam-like slice.
  v0-dev drop was the format trade, not a regression.
- **Epoch decision (A2 rule on the distribution GRPO v2 will train on):
  ep2 wins** (new-dev 91.7 vs 83.3 pass@8; also higher p@1). v2 checkpoint =
  phase8/sft_v2_s3407_ep2.
- Still missing from nb-13 output: restraint probes ×2, which-epoch for the
  ~0.017 loss table, formatted example (asked again).
- Next: notebook 14 = v2 milestone exam (ONE held-out run, sftv2 ep2, L4,
  peft-merge) → go/no-go + budget-set for GRPO v2 (+ random twin).
- S2.22 addendum (incident #5): peft's LoRA dispatcher RAISES on stale
  preinstalled torchao 0.10.0 (< its 0.16 minimum) — opposite failure mode of
  incident #1 (there: too new for torch; here: too old for peft). Strip list
  now rides WITH the peft install cell in notebooks 11 and 14 (my miss: the
  new peft-only cells had dropped it; the strip lived only in the later
  harness cell). Fix for running session: uninstall + re-run merge cell, no
  restart. Standing rule: ANY cell that imports the HF stack gets the strip.
