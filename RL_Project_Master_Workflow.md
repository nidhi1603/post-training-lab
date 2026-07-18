# Post-Training Lab — The Master Workflow
### A controlled study of Supervised Fine-Tuning vs Direct Preference Optimization vs GRPO for small-model code repair — with a first-class evaluation track

*Frozen on 2026-07-08. Every claim below was verified against primary sources (arXiv abstract pages, GitHub repos, Hugging Face model cards) in this session. This is the document to keep open while you work. Nothing in it is optional unless marked OPTIONAL.*

> **Amendment A1 (2026-07-14) applies.** Phase-2 data sources are revised — see [Amendment A1](#amendment-a1-2026-07-14--phase-2-data-sources-revised) at the end of this document. The eval ruler (benchmark, protocol, targets) is unchanged.

---

## 0. The project in one paragraph

Take a small open model (**Qwen2.5-Coder-1.5B-Instruct**, Apache-2.0 licensed) and teach it to **fix buggy code** three different ways — **SFT** (supervised fine-tuning: imitate correct fixes), **DPO** (direct preference optimization: learn from pairs of better/worse fixes), and **GRPO** (group relative policy optimization: reinforcement learning where the reward is *the unit tests actually passing*). Measure every step on a published benchmark (**HumanEvalFix**, from the OctoPack paper, arXiv 2308.07124) using the paper's own evaluation code and settings, aiming to beat the paper's 16-billion-parameter flagship (OctoCoder, ~30.4% pass@1) with a model **10× smaller**. Then prove the gains are real: a random-reward control run, three training seeds, and a full rerun of the frozen recipe on a different model family (**Llama-3.2-3B-Instruct**). The evaluation harness — execution-verified, judge-free, with confidence intervals, a bug-taxonomy breakdown, and a restraint suite — is a named deliverable of its own. Outputs: a GitHub repo, Hugging Face models, 3–4 LinkedIn posts, and an arXiv preprint.

**Honest novelty statement (memorize this):** we are *not* the first to run RL with execution rewards on code repair — **Repair-R1 (arXiv 2507.22853, July 2025) did GRPO on exactly Qwen2.5-Coder-1.5B** and is our closest prior art and a baseline to cite. Our contribution is the **controlled three-arm comparison under matched budgets**, the **cross-model-family validation** (testing the Spurious Rewards concern, arXiv 2506.10947, in the code domain), and the **evaluation rigor**. Say it this way and nobody can attack it.

---

## 1. Ground rules (violating any of these invalidates the study)

1. **The ruler is frozen before training.** Benchmark, harness commit, prompt format, decode settings — all written into `EVAL_PROTOCOL.md` in Phase 1 and never edited after.
2. **Nothing derived from HumanEval ever enters training data.** Enforced by a contamination audit (Phase 2, step 7), not by good intentions.
3. **The held-out benchmark is touched only at milestones.** Day-to-day decisions use a fixed held-in development slice. (Ai2's OLMo practice: hill-climbing on a benchmark you watch daily overfits it even without training on it.)
4. **Matched budgets across arms.** SFT, DPO, and GRPO see the same training problems and comparable update counts — otherwise the comparison is meaningless.
5. **Same decode settings for every headline number.** Temperature 0.2, top_p 0.95, n=20 samples, pass@1 by the unbiased estimator — the OctoPack paper's exact settings. Never compare checkpoint A at one temperature with checkpoint B at another ("A Sober Look", arXiv 2504.07086: temperature alone moves results up to ~15 points).
6. **Correctness is graded by execution only.** No LLM judge anywhere in the correctness pipeline. (LLM judges are allowed later, only for non-verifiable extras like patch readability, and only as a labeled appendix.)
7. **Report what happened.** Failed runs, hacked rewards, and negative results go in the paper and the posts. They are content, not embarrassments.

---

## 2. Phase map

| Phase | Name | Calendar | GPU cost | Gate to pass before next phase |
|---|---|---|---|---|
| 0 | Setup | done / day 1 | ~0 | accounts + repo exist, Llama access granted |
| 1 | Foundations & baseline | week 1 | ~15 units | baseline pass@1 measured; target locked; protocol frozen |
| 2 | Data pipeline | week 2 | ~10 units + API | audited SFT/RL datasets exist; contamination report clean |
| 3 | SFT arm | week 2–3 | ~15 units | SFT beats base on dev slice; RL-init checkpoint chosen by pass@k |
| 4 | DPO arm | week 3 | ~10 units | DPO trained ×3 seeds; verdict vs SFT recorded |
| 5 | GRPO arm | week 3–4 | ~60 units | GRPO beats SFT on dev slice OR failure documented |
| 6 | Controls & validation | week 5 | ~50 units | random-reward control + Llama rerun done |
| 7 | Final eval & evals deliverable | week 5 | ~15 units | one-shot held-out results table with CIs |
| 8 | Paper, release, posts | week 6 | ~0 | arXiv submitted, models on HF, posts published |

Total ≈ 175 Colab compute units (you have ~300) + Modal/Lightning free tiers as overflow. Calendar: **6 weeks paper-grade**; a 4-week "LinkedIn-grade" shortcut exists (1 seed, skip Phase 6 extras) but forfeits the paper.

---

## Phase 0 — Setup (mostly done)

- [x] Hugging Face account + write token
- [x] Llama-3.2-3B-Instruct access requested (gated; approval usually minutes–hours)
- [x] Colab Pro confirmed (~300 compute units; T4 ≈ 1.76 units/hr, L4 ≈ 5, A100 ≈ 15)
- [x] Google Drive folder `rl-post-training/` for checkpoints (done 2026-07-14; Colab *will* disconnect; a run without checkpoint syncing is a run you will lose)
- [x] GitHub repo `post-training-lab` created (done 2026-07-14: https://github.com/nidhi1603/post-training-lab — eval + reward layer implemented and tested, ahead of schedule)
- [x] Modal account (free $30/month credits — will host the sandboxed reward execution later) and Lightning AI account (free monthly credits, backup GPU) (done 2026-07-14)
- [x] **Milestone 0:** run Unsloth's GRPO notebook unchanged on a Colab T4 (`nb/Qwen2.5_(3B)-GRPO.ipynb` from unslothai/notebooks). Success = the reward table prints and you can name what each column is. ~3 units, ~1.5 hours. You are proving the machinery, not training a model. **(done 2026-07-15: 250 steps, 1h40m, ~3 units. Observed: ~1/3 of steps had reward_std=0 → zero gradient; 200-token completion cap clipped ~90% of early rollouts → model adapted by compressing reasoning; correct-but-unit-suffixed answers ("8 GB") scored 0 under exact string match — the false-negative class execution grading eliminates.)**

**Learn block 0** (companion reading — llm-foundations site, your friend-circle's series): Modules 02–05 (tokenization, transformer, attention, positional encoding) if any feel shaky; Module 10 (decoding & sampling) *before* Phase 1, because pass@1 estimation is a sampling question.

---

## Phase 1 — Foundations & baseline (week 1)

**Goal: one honest "before" number per model, a frozen protocol, and a locked target.**

1. **Install the paper's own harness** (bigcode-evaluation-harness). Record the git commit hash — it goes in the protocol file.
2. **Pick the prompt format.** Run 20 problems with `--prompt instruct` on Qwen2.5-Coder-1.5B-Instruct; read the raw generations; if malformed, try the other formats; **freeze the winner.** (FormatSpread, arXiv 2310.11324: formatting alone can swing results massively — this is why we freeze it.)
3. **Baseline eval — Qwen2.5-Coder-1.5B-Instruct** on `humanevalfixtests-python`: temperature 0.2, top_p 0.95, n_samples 20, `--allow_code_execution`, L4 GPU (T4 lacks bfloat16). Save generations JSON + metrics JSON to Drive.
4. **Baseline eval — Llama-3.2-3B-Instruct** (its own "before" photo for Phase 6).
5. **Decision gate — lock the target now, in writing:**
   - base < 30.4% → target = beat OctoCoder-16B; stretch = GPT-4 row (~47%).
   - base ≥ 30.4% → target = GPT-4 row, or the harder language splits. No goalpost-moving later.
6. **Build the held-in dev slice:** a fixed ~100-problem slice of *training-distribution* bugs (from Phase-2 data, NOT from the benchmark) used for every checkpoint decision. The 164-problem benchmark is held-out and touched only at phase ends.
7. **Write `EVAL_PROTOCOL.md`:** benchmark + variant, harness commit, prompt format, decode settings, pass@1 estimator (unbiased Codex estimator: pass@k = 1 − C(n−c,k)/C(n,k)), targets, contamination rule, held-in/held-out policy. Commit it. This file is what makes every later claim trustworthy.

**Evals-track step E1:** extract the benchmark's own **bug taxonomy** (OctoPack Table 15: missing logic 33, excess logic 31, value misuse 44, operator misuse 25, variable misuse 23, function misuse 8) into `eval/taxonomy.json`, and script a per-category pass@1 breakdown from any generations file. From now on every eval produces a taxonomy table, not just one number. (Known paper finding to check against: excess-logic bugs — the ones requiring *deleting* code — are hardest.)

**Learn block 1:** what a token, a logit, temperature, and top_p are; why pass@1 needs 20 samples (variance of small benchmarks); what a confidence interval is. Companion: Module 10 + Anthropic's "Adding Error Bars to Evals" (arXiv 2411.00640).

**Deliverables:** two baseline numbers with 95% confidence intervals + taxonomy breakdown + frozen protocol.
**Gate:** protocol committed; target locked.

---

## Phase 2 — Data pipeline (week 2)

**Goal: three audited datasets — SFT traces, DPO pairs (generated later from the verifier), and RL training bugs with trustworthy tests. This phase decides the project's ceiling; do not rush it.**

1. **Source raw bug/fix pairs:** CommitPackFT (the OctoPack paper's own filtered commit data) and/or `google/code_x_glue_cc_code_refinement`. Filter to Python, deduplicate, length-filter. Target ~5–10k candidate problems.
2. **Attach tests to RL training problems.** Options in order of preference: keep problems that ship with tests; generate tests with a teacher model — **but every generated test must pass a gold-sanity gate: it must PASS on the known-correct fix and FAIL on the buggy version, verified by execution in a sandbox** (arXiv 2606.16062 found ~25–28% of tasks in major RL code datasets accept incorrect patches; this gate is what keeps "passes tests" meaning "correct"). Discard problems whose tests can't clear the gate.
3. **Build the SFT set by verified reasoning distillation:** teacher model (Gemini via your AI Studio, or DeepSeek) generates a `<think>` reasoning trace + proposed fix for each bug → **run the tests → keep only traces whose fix passes.** Every SFT example is provably correct. (This is the R1-style distillation idea, upgraded: your friend's project had to approximate correctness with reconciliation heuristics because reviews aren't executable; your task is executable, so you filter on truth.)
4. **Diversity over multiplicity:** spend the data budget on *many different bugs*, not many completions of the same bug (AceReason-Nemotron, arXiv 2506.13284: prompt diversity beats responses-per-prompt for downstream RL).
5. **Balance audit — including restraint:** classify targets by bug taxonomy AND include **~15–20% clean examples** — functions with *no* bug, where the correct output is "no fix needed." (Your friend's repo is the cautionary tale: 8.3% clean targets → the model flagged defects on 77% of clean inputs. Same lesson as BFCL's irrelevance-detection category: a system that can't stay quiet is broken.)
6. **Split:** train / held-in dev slice (the ~100 from Phase 1) / a small held-out sanity slice. No overlap, enforced by hashing.
7. **Contamination audit (`eval/contamination_report.md`):** 50-gram substring overlap between every training example and every benchmark problem (code-standard n-gram size); embedding near-duplicate check for rephrased leaks (LMSYS LLM Decontaminator method, arXiv 2311.04850 — n-grams demonstrably miss logic-preserving edits); grep for HumanEval function names. Anything flagged is deleted from training data, and the report is committed.

**Evals-track step E2:** build the **restraint suite** — ~100 verified-clean functions with tests. Metric: **false-fix rate** (model "fixes" code that wasn't broken). This is the code-repair analog of a gated-tool denial test, and it's a table almost no small study reports.

**Learn block 2:** what makes training data good (diversity, correctness, balance); distillation; contamination. Companion: Module 31 (synthetic data & data-centric AI — rejection sampling, dedup, contamination canaries).

**Deliverables:** `data/` with audited SFT + RL sets, restraint suite, contamination report.
**Gate:** contamination report clean; balance audit shows ≥15% restraint examples; every RL problem's tests passed the gold-sanity gate.

---

## Phase 3 — SFT arm (weeks 2–3)

**Goal: the imitation baseline, trained honestly, three times.**

1. QLoRA fine-tune Qwen2.5-Coder-1.5B-Instruct on the verified traces. Starting config: LoRA rank 32, alpha 64, learning rate 1e-4→2e-4, 2 epochs, loss masked to the completion only (the model must not be trained to predict the prompt).
2. **Checkpoint cadence:** eval on the held-in dev slice every fixed N steps; fixed slice, never re-sampled (re-sampling confounds model change with item change).
3. **Run ×3 seeds** (different random seeds, same everything else). Report mean ± standard deviation. ("A Sober Look": single-seed results at this scale are noise; recent RLVR papers use 3–5 seeds.)
4. **Forgetting check:** a 20-problem generic-chat + non-Python sanity probe, before vs after — catastrophic forgetting shows up here first.
5. **Select the RL-init checkpoint by pass@k, not pass@1** (k=16 on the dev slice). Quagmires (arXiv 2510.01624): high SFT greedy scores do NOT predict RL outcomes — held-out pass@large-k does, because RL needs the *distribution* to contain correct answers to amplify, not a sharpened point estimate.
6. Milestone eval on the held-out benchmark (once): SFT row of the results table, with CIs + taxonomy breakdown + restraint suite.

**Learn block 3:** loss functions and cross-entropy from scratch; what LoRA rank actually is (a low-rank bottleneck on the weight update); masking; overfitting vs memorization. Companion: Module 07 (fine-tuning & PEFT — has the LoRA math), Module 06 if curious about the pretraining the SFT sits on.

**Deliverables:** 3 SFT adapters + training curves + SFT results row.
**Gate:** SFT ≥ base on dev slice; RL-init checkpoint chosen by pass@k and recorded *before* Phase 5 starts.

---

## Phase 4 — DPO arm (week 3)

**Goal: the preference arm — nearly free, and an honest open question.**

1. **Generate pairs from the verifier:** sample 8 fixes per training bug from the SFT model → run tests → (passing, failing) = (chosen, rejected). Prefer pairs from the same problem; cap pairs per problem to preserve diversity.
2. Train DPO on top of the SFT checkpoint, β≈0.1 starting point, ×3 seeds, matched example budget to Phase 5.
3. **Known failure mode to watch** (it's in the DPO literature and in Module 08's deck): the log-probability of *both* chosen and rejected answers falling — the model getting worse at everything while the *gap* improves. Monitor both curves, not just the loss.
4. Milestone eval: DPO row (CIs, taxonomy, restraint).
5. **Record the verdict honestly.** The 2025–26 literature does *not* establish that a DPO stage helps before RL on verifiable tasks — it's an open question, which is exactly why your controlled version of it is a contribution. Whatever you find — helps, hurts, ties — is a result.

**Learn block 4:** preferences and the Bradley–Terry model; how DPO turns reinforcement learning into a classification-style loss ("the implicit reward"); why preference data quality is everything. Companion: Module 08's DPO section (the site's deepest math — derivation + worked gradient step).

**Deliverables:** DPO adapters ×3, pair-generation script, DPO results row + verdict paragraph.
**Gate:** none blocking — GRPO proceeds from the Phase-3 checkpoint regardless; DPO is a comparison arm, not a dependency.

---

## Phase 5 — GRPO arm (weeks 3–4) — the main event

**Goal: reinforcement learning with an executable reward, run to a defensible verdict.**

1. **Write the reward function first, test it second, train third.** Layered but **correctness-dominated**:
   - parses/compiles: +0.1
   - fraction of tests passed × 0.2
   - **ALL tests pass: +1.0**
   - mild length penalty for absurd outputs
   - **Invariant (the CoRPO lesson, arXiv 2511.04439): no failing patch may ever out-reward a passing one.** With a mean-relative baseline like GRPO's, a "less wrong" patch in a bad group gets positively reinforced unless the pass bonus dominates — check your weights against this by construction, and unit-test the reward function itself (your repo's tests are `tests/test_reward.py` before any GPU is touched).
2. **Sandbox the execution:** tests run in a subprocess with timeouts, and the test files are **read-only to the policy's code** — Meta's agentic-repair study (arXiv 2510.22075) watched models *delete the validation code* to "pass." Run the reward server on Modal (free credits) or locally in the Colab VM.
3. **Pre-flight variance gate (no GPU wasted on unlearnable data):** sample 8 completions per prompt from the init checkpoint on ~50 dev bugs; a prompt where all 8 pass or all 8 fail produces zero learning signal in GRPO (group-relative advantage = 0). Require a healthy fraction of mixed-outcome prompts; drop or re-bucket the rest. (Your friend's repo had exactly this gate — reimplement it yourself.)
4. **Algorithm config (2025–26 verified):**
   - default loss: **Dr. GRPO** (`loss_type="dr_grpo"` in TRL/Unsloth) — removes GRPO's length-normalization and std-scaling biases (arXiv 2503.20783), i.e., stops wrong answers from bloating in length;
   - **A/B one run against GSPO** (`importance_sampling_level="sequence"`, keep `loss_type="grpo"`; arXiv 2507.18071, Qwen team) — your reward is sequence-level (tests pass for the whole patch), so sequence-level ratios are the theoretically matched choice;
   - DAPO tricks (arXiv 2503.14476): clip-higher, skip zero-variance groups (dynamic sampling);
   - group size 8, KL penalty small, generation temperature ~1.0 during training rollouts (tuned once so entropy stays moderate — AceReason's exploration lesson), *frozen eval decoding unchanged at 0.2*.
5. **Reward-hacking watch (read transcripts, every run):** hardcoded test values in the patch, try/except swallowing, output length drift, dev-slice score rising while taxonomy shifts weirdly. Every confirmed hack + countermeasure goes in `docs/hacking_log.md` — this becomes a paper section and your best LinkedIn post.
6. **Run ×3 seeds** from the Phase-3 pass@k-selected checkpoint. Also OPTIONAL if time: one CISPO run (`loss_type="cispo"`) if entropy collapses; one run from the DPO checkpoint to test ordering.
7. Milestone eval: GRPO row (CIs, taxonomy, restraint).
8. **If GRPO fails to beat SFT after two honest debugging cycles: stop and write it up.** With Repair-R1 as prior art at this exact scale, success is likely — but a clean negative result with your controls is still a publishable paper and a great story. Pre-committing to this rule is what makes the positive result believable.

**Learn block 5 (the big one):** reinforcement learning from zero — reward, policy, why gradients through sampling are hard; REINFORCE → baselines → PPO's clipping → GRPO's group trick (the lineage, one step at a time); reward hacking and Goodhart's law; then Dr. GRPO/GSPO as "bug fixes to GRPO's statistics." Companion: Module 08 (RLHF/PPO/GRPO math), Module 28 (RLVR, reasoning ladder, test-time compute).

**Deliverables:** reward module + its unit tests, variance-gate script, GRPO adapters ×3, hacking log, GRPO results row.
**Gate:** a defensible verdict either way, with seeds and CIs.

---

## Phase 6 — Controls & validation (week 5) — what makes it science

1. **Random-reward control (Qwen):** one GRPO run identical to Phase 5 but rewards drawn at random. Spurious Rewards (arXiv 2506.10947): random rewards gave Qwen models large gains on math (+21 points) — clipping bias amplifies pretrained behaviors, largely Qwen-specific. If your random-reward run recovers a big chunk of your GRPO gain, the headline must be re-attributed honestly. Running this control *before* anyone asks is what separates you from the papers that got embarrassed.
2. **Cross-family validation (Llama-3.2-3B-Instruct):** the frozen recipe — same data, same SFT, same reward, same GRPO config — run once, no tuning. Compare against Llama's own Phase-1 baseline. Gains transfer → strongest claim. Gains shrink → confirmed Spurious-Rewards-style finding in the code domain → arguably *more* citable. Either way you win.
3. **OPTIONAL stretch:** same recipe on Gemma-3-1B-it (third family, instant-approval gate, Unsloth notebook exists).
4. Final held-out evaluation, **once**, for every arm and control, exact protocol: base / SFT / DPO / GRPO / random-reward / Llama-base / Llama-SFT / Llama-GRPO.

**Statistics for every comparison** (Anthropic error-bars standard, arXiv 2411.00640): mean ± 95% CI via standard error; **paired** differences on the shared 164 problems (McNemar's exact test on discordant pairs and/or paired bootstrap ~10k resamples), never two independent means; Holm–Bonferroni if you make many comparisons; on a 164-item benchmark near 50%, CIs span several points — claim nothing inside the interval.

**Deliverables:** the final results table (the paper's Table 1) + significance report.
**Gate:** all cells filled or their absence explained.

---

## Phase 7 — The evals deliverable (week 5, parallel)

Package the harness as a standalone artifact — `eval/` with its own README:

1. Execution-verified scoring + unbiased pass@k estimator + CI/paired-test utilities
2. **Taxonomy breakdown table** (6 bug types × every arm)
3. **Restraint suite** (false-fix rate × every arm)
4. Contamination report (n-gram + embedding + a LiveCodeBench-style *post-cutoff* slice if time permits — problems published after the base model's training cutoff are contamination-proof by construction)
5. Decode-sensitivity appendix: headline result at 2–3 temperatures/formats, showing the *direction* is robust
6. Hacking log + the gold-sanity test gate script
7. **`docs/EVALS_PLAYBOOK.md` — the interview crosswalk.** One page mapping what you built to the agent-evals vocabulary interviewers use, so every line of this project answers an evals question:

| Agent-evals concept (the interview question) | What you built here |
|---|---|
| Tool selection accuracy (BFCL AST: name/params/type/value match) | patch graded by structural execution match |
| BFCL irrelevance detection / false-invocation rate on gated tools | **restraint suite: false-fix rate on clean code** |
| τ-bench final-state comparison; pass^k reliability (all k trials succeed) | tests-pass = state check; pass@k *and* per-seed variance reported |
| ToolRL decomposed reward (name/key/value partial credit) | layered reward: compile / partial tests / all tests |
| AgentDojo: utility under attack, attack success rate | hacking log + read-only sandbox + gold-sanity gate |
| Step-level vs outcome-level trajectory evals | checkpoint dev-slice curves vs final held-out table |

*(And your gated-MCP interview answer, permanently: "score selection statistically — name, argument keys, argument values, BFCL-style; enforce permissions deterministically at the gate layer and test them as invariants — false-invocation rate on denial suites, zero gate-bypass by construction; grade multi-step outcomes by final state, τ-bench style, reporting pass^k for reliability.")*

**Learn block 7:** statistics of evaluation — SEM, clustered errors, paired tests, power analysis; why the field has an "evals gap." Note: the llm-foundations site has **no evals module** — this phase is you writing the missing chapter yourself.

---

## Phase 8 — Paper, release, posts (week 6)

1. **Paper** (6–9 pages, LaTeX): Intro (the SFT-vs-RL question + Spurious Rewards motivation) → Related work (Repair-R1, OctoPack, ToolRL, DAPO/Dr.GRPO/GSPO, the friend-project lesson only if he agrees to be acknowledged) → Method (three arms, matched budgets, reward design) → Evaluation (protocol, taxonomy, restraint, contamination) → Results (Table 1 + per-category) → the random-reward and cross-family analyses → Limitations (one task family, 1.5B scale, 3 seeds, Python-only) → Reproducibility statement.
2. **arXiv:** cs.LG cross-listed cs.SE; endorsement needed for first submission — the professor conversation should have started in week 2.
3. **Hugging Face:** adapters + merged best model + the datasets you're licensed to share, model cards with the results table.
4. **LinkedIn cadence (4 posts):** (i) the question + design, (ii) the reward-hacking war story, (iii) the DPO-vs-GRPO verdict, (iv) the final table + paper link. Numbers stated honestly: relative gain over base, "beats a 16B model at 1.5B," never inflated multipliers.

---

## Learning curriculum map (so "basics → advanced, every time" is structural)

| Phase | You learn (basics → advanced) | Companion module (llm-foundations site) |
|---|---|---|
| 0–1 | tokens, sampling, pass@k, confidence intervals | 02–05, 10 |
| 2 | data quality, distillation, contamination | 31 |
| 3 | loss, cross-entropy, LoRA math, masking, forgetting | 07 (+06) |
| 4 | preferences, Bradley–Terry, DPO derivation | 08 (DPO section) |
| 5 | REINFORCE → PPO → GRPO lineage, KL, reward hacking, Dr.GRPO/GSPO | 08 + 28 |
| 6–7 | experimental design, error bars, paired tests, contamination audits | *(no module exists — you're writing it)* |
| 8 | scientific writing, honest claims | — |

Each phase runs the loop: **Learn (I teach from zero) → Build (we implement, every decision explained) → Explain back (you teach it to me; I grill you interview-style; your explanation becomes the lab-notebook entry → LinkedIn post → paper paragraph).**

---

## Verified reading list (all IDs fetched and confirmed this session)

**Core:** OctoPack/HumanEvalFix 2308.07124 · GRPO (DeepSeekMath) 2402.03300 · DPO 2305.18290 · Tulu 3 (RLVR) 2411.15124 · DeepSeek-R1 2501.12948
**Recipe upgrades:** Dr. GRPO 2503.20783 · DAPO 2503.14476 · GSPO 2507.18071 · CISPO (MiniMax-M1) 2506.13585 · CoRPO 2511.04439
**Code-repair RL:** **Repair-R1 2507.22853 (closest prior art — read first)** · Meta agentic repair 2510.22075 · signal reshaping 2605.07276 · EvolveCoder 2603.12698 · reward-hackability audit 2606.16062
**The debate you're entering:** Spurious Rewards 2506.10947 · "Does RL really incentivize…" 2504.13837 · RL Squeezes/SFT Expands 2509.21128 · Quagmires 2510.01624 · AceReason-Nemotron 2506.13284
**Evals canon:** Error Bars 2411.00640 · A Sober Look 2504.07086 · EleutherAI Lessons 2405.14782 · EvalPlus 2305.01210 · FormatSpread 2310.11324 · LLM Decontaminator 2311.04850 · LiveCodeBench 2403.07974
**Tool-use evals (interview arsenal):** BFCL (ICML 2025; V4) · τ-bench 2406.12045 / τ2-bench 2506.07982 · ToolRL 2504.13958 · AgentDojo 2406.13352

---

## Risk register

| Risk | Detection | Response |
|---|---|---|
| Base model already beats 30.4% | Phase 1 | pre-committed: retarget GPT-4 row / harder splits |
| SFT below base | Phase 3 gate | masking/format bug hunt before proceeding |
| GRPO reward flat | variance gate + curves | data too easy/hard → re-bucket; check reward unit tests |
| Reward hacked | transcript reads, hacking log | patch sandbox/tests; document; it's content |
| Random-reward control recovers most of the gain | Phase 6 | re-attribute honestly; the finding IS the paper |
| Gains don't transfer to Llama | Phase 6 | report as Spurious-Rewards-in-code finding — citable |
| Colab units run out | budget tracker in README | Modal/Lightning free tiers → RunPod 4090 ~$0.34/hr |
| Timeline slips | weekly review vs phase map | cut OPTIONAL items first (Gemma, CISPO, ordering run) — never cut seeds or controls |

*End of master workflow. Next physical action: Phase 0 checklist items, then Milestone 0 tonight.*

---

## Amendment A1 (2026-07-14) — Phase-2 data sources revised

*The plan doc is frozen; changes arrive as dated amendments, never silent edits. This amendment changes TRAINING DATA only. The ruler — HumanEvalFix, harness, decode settings, targets — is untouched.*

### A1.1 CUT: `google/code_x_glue_cc_code_refinement`

Verified against the dataset card (2026-07-14): the dataset is **Java-only** with **abstracted identifiers** (`VAR_1`, `METHOD_1`, `TYPE_1`). There is no Python to filter to, and abstracted Java is useless for natural Python repair. Removed from Phase 2, step 1.

### A1.2 NEW BACKBONE: mutation-injected bugs over verified-correct functions

The training distribution must match the benchmark's shape: *single self-contained Python function + tests + one small semantic bug*. Build it directly instead of mining for it:

1. **Correct functions with tests:**
   - **MBPP+** (EvalPlus-augmented sanitized MBPP, ~400 problems, tests ~35× stronger than original MBPP) — primary seed corpus.
   - **CommitPackFT Python** filtered to single-function diffs — teacher generates tests, every test through the gold-sanity gate (unchanged from step 2). Keeps *real human bugs* in the mix alongside synthetic ones.
   - OPTIONAL: teacher-authored function+test sets, gold-gated, if volume falls short.
2. **Bug injection**, mapped 1:1 onto the OctoPack taxonomy:
   - AST mutation operators: operator swap → *operator misuse*; identifier swap (same-scope, type-compatible) → *variable misuse*; constant perturbation / off-by-one → *value misuse*; statement deletion → *missing logic*; statement insertion → *excess logic*; call substitution → *function misuse*.
   - LLM-injected subtle bugs (teacher prompt: "introduce one realistic <category> bug") for naturalness — same validation as below.
3. **Validation rule (the equivalent-mutant trap):** every mutant must **compile AND fail ≥1 test**. A mutant that passes all tests is either an equivalent mutant or a weak test suite — discard it, never train on it.
4. **Diversity caps:** ≤2 mutants per source function (AceReason: prompt diversity beats responses-per-prompt). **Split at FUNCTION level** — all mutants of one function live in the same train/dev/held-out split, or near-duplicate leakage silently inflates dev scores.
5. **Taxonomy-balanced sampling**, oversampling *excess-logic* (deletion-type — the benchmark's hardest category and the headroom).
6. **Restraint suite = the unmutated originals** (verified-clean, tests attached) — the ~100-example suite from step E2 now falls out of the pipeline for free.
7. **Contamination audit unchanged** and now also runs over all MBPP-derived data. Note for the paper's limitations: MBPP+ is itself a benchmark; training on it forfeits ever reporting MBPP numbers for these models.

### A1.3 Reward-data consequence: visible/hidden test split

Because Phase 2 now constructs the tests, construct them in two pools per problem: **K visible tests** (shown in the RL prompt, matching the benchmark's tests-in-prompt format) and **held-back hidden tests** (used by the reward alongside the visible ones). A policy that hardcodes the visible tests fails the hidden ones — this closes the one reward hack the sandbox and transcript reads cannot catch, because it isn't cheating, it's specification gaming.

### A1.4 Teacher model: DeepSeek, not Gemini

Gemini API terms restrict using outputs to train models; this project ships a public dataset + arXiv paper. DeepSeek's terms permit distillation. All teacher roles (SFT traces, test generation, LLM bug injection) use DeepSeek. Gemini may be used for private analysis only.

### A1.5 Unchanged

Benchmark, harness, prompt-format freeze, decode settings, targets, gold-sanity gate, matched budgets, all ground rules, all phase gates. Phase-2 GPU/API budget unchanged (~10 units + API); mutation injection is CPU-cheap and *reduces* teacher-API spend vs. generating tests for every commit-mined problem.

---

## Amendment A2 (2026-07-18) — SFT-stage refinements, triggered by the Phase-1 audit

*Trigger: the audit (eval/results/phase1_audit.md) showed Qwen's pure-amplification
ceiling (~25.6%, 42/164 reachable) sits BELOW the locked 30.4% target — SFT is
load-bearing, so its design corner earned a targeted literature pass. Nothing frozen
is touched; all changes live in not-yet-executed Phases 2–3.*

1. **Trace policy hardened (Phase 2/3):** SFT traces stay SHORT (≤512 think tokens),
   now backed by "Through the Valley" (arXiv 2506.07712, EMNLP 2025): ≤3B models
   (incl. Qwen2.5-1.5B) suffer Long-CoT Degradation on limited long-trace data (up to
   −75%). Add a one-seed dev-slice A/B *before* the 3-seed run: short-trace SFT vs
   direct-fix (no-trace) SFT; commit the winner.
2. **SFT early-stopping by headroom, not loss (Phase 3):** stop/select checkpoints by
   dev pass@16 + entropy, explicitly to avoid the SFT entropy/diversity collapse that
   shrinks the pass@k−pass@1 gap RL feeds on (CurioSFT 2602.02244, SED-SFT
   2602.07464, overtraining→rank-inversion 2606.18487, divergence choice 2509.07430).
   We adopt the *monitoring/stopping rule only* — no custom SFT losses (arm integrity).
3. **Stage-specific data routing (Phase 2):** when sampling the base model on training
   bugs (already required for the variance gate), route by outcome: all-fail → weighted
   into SFT set (expansion), mixed-outcome → RL set (learnable signal), all-pass →
   restraint/discard (Stage-Specific Data, 2606.04466).
4. **Counterpoint logged for the paper:** RL can genuinely exceed SFT-reachable
   coverage in some regimes (2604.01302) — the audit's 25.6% ceiling is indicative,
   not a law; frame accordingly.
