# 0007 — BAV-1: does Genesis's completeness label carry information? (Book Agreement Validation)

**Date:** 2026-08-10 (three runs)
**Status:** done
**Classification: BUILD — engineering validation. Not research. No novelty claimed.**
Contract: [`../../recorder/CONTRACT-book-agreement.md`](../../recorder/CONTRACT-book-agreement.md),
frozen before run 1 and byte-identical across all three runs
(`sha256 4b71c2a6272dbf8306b506f1661684e7c0813fe7ab7b9df6ca64e430dc06b530`).
Code: [`../../recorder/bav.py`](../../recorder/bav.py).
Rule under test: [`../../recorder/completeness.py`](../../recorder/completeness.py).
Checks: [`../../tests/test_bav.py`](../../tests/test_bav.py) (25),
[`../../tests/test_completeness.py`](../../tests/test_completeness.py) (13).

The first Genesis milestone to make a falsifiable claim about **live, prospectively recorded**
data. Everything before it was historical or authored.

---

## 1. The question

Two questions, pre-registered in that order:

> **A.** Does a book reconstructed from the Genesis event log agree with an independently
> fetched REST snapshot of the same venue at the same moment?
>
> **B.** Does the recorder's own `complete` / `incomplete` label **predict** that agreement?

B is the one that matters. A recorder that reconstructs well but cannot tell you when to trust
it is not an instrument — it is a hopeful guess with good numbers attached.

## 2. Protocol (frozen before run 1; unchanged across all three runs)

| | |
|---|---|
| Venue / market | Binance spot, BTCUSDT |
| Streams | `depth` diff stream, anchored by REST `depthSnapshot` |
| Probes | 60 slots, 20 s dwell |
| Controlled interruptions | 14 slots, deliberate disconnection, probe fired at +5.0 s |
| Comparison | independent REST fetch vs replayed book at the probe timestamp |
| Metrics | M1 best bid/ask agreement · M2 spread · M3 Jaccard of price levels · M4 relative size error · M5 divergent levels · M6 absolute size error |
| Exclusion | request/response skew > 2000 ms |
| Strata | skew 300–1000 ms · 1000–2000 ms · >2000 ms |
| Requirement for B | ≥ 10 usable incomplete trials |
| PASS condition | stated at skew < 300 ms |

**Declared before run 2, not discovered afterward:** the measured Nairobi→Binance latency floor
is ~291 ms with a median near 430 ms, so **no trial can fall below 300 ms**. The PASS condition
as written is structurally unevaluable from this location. It was left unamended deliberately —
changing a threshold after seeing that it cannot be met is how contracts stop meaning anything.

## 3. Provenance — what was fixed when

- **Fixed before run 1:** everything in §2. Thresholds, metrics, sampling, exclusions, strata,
  the 300 ms condition, and the connection mechanism were never modified.
- **Between runs:** only defect fixes, each preceded by a test that failed first.
- **Added after run 3:** Fisher exact tests and the M3 bootstrap interval. These are
  **post-hoc choices of test** and are reported as such. The point estimates and the
  stratification they are computed over were pre-registered.

## 4. What the three runs cost, and what each exposed

Three runs were needed. That is the honest headline, and the defects are the reason.

| Run | Outcome | Defect exposed |
|---|---|---|
| 1 | Question B unanswerable | **D-A** `depthSnapshot` carried no sequence bounds. **D-B** REST comparison keys were not canonicalised, so identical prices compared unequal. Zero usable incomplete trials. |
| 2 | Question B unanswerable | **D-C** `replay` ignored `CONNECTION_CLOSED` — the recorder reported `complete` through all 14 disconnections **it had announced itself**. Zero usable incomplete trials, for the opposite reason. |
| 3 | **Question B answered** | Two further defects were caught by tests *before* run 3: run-change pre-empting an event's own classification, and comparison probes silently restoring the completeness claim their own disconnection had invalidated. The second would have reproduced run 2's failure exactly. |

Runs 1 and 2 are the same error in two directions. Run 1 was **false humility** — the recorder
refused to claim completeness it actually had. Run 2 was **false confidence** — it claimed
completeness it did not have. Both are instances of one recurring pattern, observed six times
across this project:

> *a status claim the available evidence did not support, with the contradicting evidence
> already inside the system and never checked.*

A bounded audit of all 21 conditions bearing on completeness preceded the run-3 code, and the
rule was consolidated into a single module because it had been written twice and drifted.

## 5. Result — run 3

Commit `887cda7` · seed `20260810` · 3,487 events · integrity verified · 60/60 probes fired ·
14/14 controlled interruptions executed · 0 probe failures.

**Cells**

| Cell | n |
|---|---|
| `complete` / natural | 46 |
| `incomplete_with_book` / deliberate | **11** (requirement: ≥ 10) |
| `skew_excluded` / deliberate | 3 (2393, 2437, 6453 ms) |
| `incomplete_no_book` | 0 |

Exclusions are 5% of attempts, inside the 25% limit. Zero sequence gaps, zero malformed
messages, zero invalid anchors, one ERROR. Every incomplete trial carries the same reason:
*connection closed — Genesis was not observing the venue.*

**Question A — agreement**

| | complete (n=46) | incomplete, 5 s stale (n=11) |
|---|---|---|
| M1 best bid/ask | 97.8% | 72.7% |
| M2 spread | 100% | 100% |
| M3 Jaccard, median | 0.9871 | 0.9224 |
| M4 relative size error, median | **0.000000** | **0.000000** |
| M6 absolute size error, median | **0.000000** | **0.000000** |
| M5 divergent levels, median | 5 | 40 |

**Question B — does the label predict agreement?**

| Test | Result |
|---|---|
| M1, all usable trials | 45/46 vs 8/11 — Fisher exact **p = 0.0201** |
| M1, pre-registered 300–1000 ms stratum | 39/40 vs 6/9 — Fisher exact **p = 0.0165** |
| M3 median difference | **0.0647**, bootstrap 95% [0.0273, 0.1191] |
| 1000–2000 ms stratum | n=6 vs n=2 — no separation visible, and n=2 supports no inference |

**Yes.** Books the recorder labelled `complete` matched the independent channel 97.5% of the
time in the dominant stratum; books it labelled `incomplete` matched 66.7%. The interval on the
Jaccard difference excludes zero. This is not an informative null.

## 6. Two claims that must not be merged

Fidelity and self-knowledge are separate properties, and this experiment separates them
cleanly:

- **Reconstruction fidelity is high in both strata.** M4 and M6 are exactly zero everywhere —
  every price level present in both representations matched to the last digit. Staleness does
  not corrupt the numbers.
- **What staleness costs is *which levels exist*.** Divergent levels rise roughly eightfold.
  The book stays accurate and stops being current.

Run 2 is the proof that these are independent: fidelity was high (M3 ≈ 0.98, M4/M6 zero) while
the completeness label was wrong for **every** controlled probe.

## 7. What this does not establish

- **The PASS condition is unevaluable**, not passed. No trial occurred below 300 ms and none
  can from this location.
- **All incompleteness here is deliberate.** Zero natural interruptions occurred in three
  hours of recording. This is evidence about an artificially created 5-second boundary, not
  about how the venue fails on its own.
- **The null scope is narrow.** A null on the controlled condition would have been a null
  *at the pre-registered 5-second staleness interval only*.
- **Neither channel is ground truth.** This validates consistency between two
  Binance-delivered representations. Binance REST is not an oracle.
- **n = 11.** One arm is thin, and the 1000–2000 ms stratum is uninformative at n = 2.
- **One symbol, one venue, one hour, one geography.**

## 8. What it changes

Genesis can state whether its own record is trustworthy, and the statement carries measurable
information. That is the precondition for every later claim the project might make: a decision
recorded against an untrustworthy book is not evidence of anything.

**Phase 0 — trustworthy observation — is complete.** Further refinement of the observation
layer now falls under the standing kill criterion *"the system grows more complex without
producing evidence — stop and simplify."*

No connection is drawn here to hypothesis 0001. Any implication for it is a separate
observation and is not recorded as a result of this experiment.

## 9. What the instrument revealed about the process

Reconstruction was excellent from run 1 onward. **Self-assessment was the unreliable part** —
and self-assessment is precisely what a research instrument is for. Three runs and six defects
bought one sentence that can be defended: *the label means something.*

The defects were not found by reasoning about the code. They were found by pointing an
independent channel at it and looking at the disagreement.

---

## Evidence

Raw logs are hash-chained and integrity-verified. Their checkpoints and SHA-256 digests are
committed with this record; the logs themselves are archived outside the repository for size
(see [`../../recorder/EVIDENCE.md`](../../recorder/EVIDENCE.md)). The committed checkpoint is
sufficient to detect any modification of the archived log, which is what the hash chain was
built for.
