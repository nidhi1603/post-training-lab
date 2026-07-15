# hacking_log.md — reward-hacking war log (Phase 5)

Read transcripts every GRPO run. Log every confirmed hack + its countermeasure here.
This becomes a paper section and the best LinkedIn post. Empty is fine now; fill during
Phase 5.

## What to watch for

- Hardcoded expected values pasted into the patch instead of a real fix.
- `try/except` that swallows the test failure.
- Output-length drift (patches ballooning to game a metric).
- Dev-slice score rising while the taxonomy breakdown shifts weirdly.
- Attempts to **delete or edit the test files** (Meta agentic-repair study, arXiv
  2510.22075). Tests are read-only to the policy's code; log any attempt anyway.

## Log

| Date | Run / seed | Hack observed | Evidence (transcript id) | Countermeasure | Fixed? |
|---|---|---|---|---|---|
| | | | | | |

## Gold-sanity gate (Phase 2) failures

Problems whose generated tests failed the gate (must PASS on the known-correct fix and
FAIL on the buggy version) are discarded, not fixed. Record counts here for the paper.

| Date | Source dataset | Candidates | Passed gate | Discarded | Notes |
|---|---|---|---|---|---|
| | | | | | |
