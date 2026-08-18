# COND-1 — when is the maker advantage real?

**Status: FROZEN 2026-08-18, before the data exists.** No measurement, grid, threshold,
prediction or kill condition below may be changed after this point. If a defect is found in
the contract it is reported and recorded, not silently repaired.

**Classification: IMPORT + BUILD. No novelty claimed.** Every conditioner below has prior art,
named in §3. Genesis's contribution is measurement on its own recording under its own
completeness labels, not the idea.

**Subject: the q5 recording**, `~/genesis-evidence/q5/btcusdt-q5.jsonl`, started
2026-08-18T15:44 UTC, seven days, Binance spot + USD-M perp on one clock
([`../recorder/run.py`](../recorder/run.py) `spot-perp`). Its SHA-256 is not yet known and is
recorded in [`EVIDENCE.md`](EVIDENCE.md) at close. **This contract is frozen before that
recording exists**, which is the strongest available form of pre-registration and the reason
it is written now rather than after.

---

## 1. The question, and what it is not

EXEC-1 measured a maker advantage of **1.83 bps at the touch**. It did not establish that this
is profit, and it did not establish when it is present.

> **COND-1 asks one question: does conditioning on observable market state separate fills
> whose markout is favourable from fills whose markout is not?**

It does **not** ask whether Genesis should trade, does not size a position, does not compute
P&L, and does not select a strategy. A conditioner that survives here has earned the right to
be an input to T3.1's quoting policy. It has earned nothing else.

### 1.1 Why this could not be run on EXEC-1

**EXEC-1 carries no trade stream** (its record, §47 and §191 — every fill there is a bracket
inferred from book evolution, not an observation). All four conditioners below require trades,
and two require a perpetual feed that EXEC-1 does not have:

| | requires | in EXEC-1 |
|---|---|---|
| A | perp mid alongside spot mid | no perp |
| B | trades, to tell a cancel from a fill | no trades |
| C | perp liquidations | none |
| D | individual trades | no trades |

This was the reason the q4 spot-only recording was stopped ten hours in and restarted as q5.
The q4 log is archived, not discarded: SHA-256
`296bd3edb025aede0acfb7009046106a6c04c30121876ba05a90c6be2e291a03`, 170,819 events, integrity
verified, unclean shutdown recorded (SIGTERM; the process ignored SIGINT as a backgrounded job).

---

## 2. The family, fixed in advance and unable to grow

**Family COND-1 = 4 conditioners × the grid in §4 = 29 declared trials** (24 conditioned cells
plus 5 reference cells; the arithmetic is shown in §4). The count is fixed
by this document. It cannot grow, and no conditioner, bucket edge or threshold may be added,
removed or moved after freezing.

> **This is the load-bearing clause.** Four conditioners with free thresholds is not a family
> of four; it is an unbounded search, and a Benjamini–Hochberg correction applied to it is
> theatre. Every free parameter is enumerated in §4 for that reason. A parameter not listed
> there may not be varied.

**Correction:** Benjamini–Hochberg at q = 0.05 across all 29, reported alongside Bonferroni
α = 0.05/29 = 0.001724. Both are reported; neither is chosen after seeing the results.

**Primary endpoint, identical for all four:** median markout in basis points at **60 s** from
the fill, in the **certain-fill pool**, on the **291 ms arm** — the same three choices EXEC-1
made, carried over unchanged so the conditioned result is comparable to the 1.83 bps
unconditioned baseline. 1 s and 300 s are recorded as secondary and are **not** eligible to
replace the primary if the primary disappoints.

---

## 3. The four conditioners

### A — Basis-conditioned toxicity

**Claim under test.** Flow driven by the spot–perp basis is mechanical rather than informed:
an arbitrageur lifting the spot ask to hedge a perp short is price-insensitive and carries no
directional information. Fills against it should therefore show **less adverse markout** than
fills taken at random.

**Measurement.** At each fill, compute the contemporaneous basis
`b = (perp_mid − spot_mid) / spot_mid` in bps, from the two books at the same venue timestamp.
Segment fills by |b| into the buckets in §4 and report the primary endpoint per bucket.

**Note on direction, recorded because the intuition is easy to get backwards.** A wide basis
means arbitrageurs are *buying* spot. A maker on the ask is therefore *more* likely to be
filled and ends up short into a market being pushed up. The claim is not that this is safe; it
is that the *information content* of that flow is low. Those are different, and only the second
is tested here.

**Prior art:** cash-and-carry basis arbitrage in crypto is extensively documented; conditioning
markout on informed-vs-uninformed flow is standard microstructure. Import.

### B — Cancellation without trade

**Claim under test.** A burst of one-sided size disappearing from the book *without* matching
trades is liquidity withdrawing rather than being consumed, and predicts worse markout on fills
taken shortly afterwards.

**Measurement.** Binance's diff-depth stream cannot distinguish a cancel from a fill — a level
going to zero is ambiguous. With trades on the same clock it becomes decidable: **size removed
at a price with no trade at that price inside the same window is a cancellation.** Compute the
one-sided cancellation volume over the lookback in §4, normalise by visible same-side depth,
and segment fills by whether that ratio exceeds the threshold.

**Not tested:** *why* the cancellations happened. The proposition that they reflect foreign
venues moving is unfalsifiable without foreign venue data, is not claimed, and must not be
written into any interpretation of this result.

**Prior art:** order-flow imbalance and cancellation-rate predictors — Cont, Kukanov & Stoikov.
Import.

### C — Inferred liquidation cascades, validated against an answer key

**Claim under test.** A cascade is detectable from the trade stream alone, and the **silence
after** it — engine finished, makers not yet returned — is when a passive fill is cheap.

**Detector.** A cascade fires when one-sided taker volume consumes more than the depletion
fraction in §4 of same-side visible depth within the burst window in §4. The *quiet* is the
first interval in §4 with no trades following a fire.

**Validation, and the honest limit of it.** `!forceOrder@arr` is used **exclusively as an
out-of-sample answer key** and never as a detector input. But the venue publishes **only the
largest liquidation per symbol per 1000 ms window** — its own documented sampling rule. So:

> **Absence of a `forceOrder` message does not mean no liquidation occurred.** The "no
> liquidation" cell of a 2×2 is therefore unreliable, and a Fisher exact test on the full table
> would be biased by an amount Genesis cannot quantify.

**Consequently: precision is the declared primary** — of the windows in which the detector
fired, the fraction in which at least one liquidation was published. It is clean, because
*presence* in the key is reliable. **Recall is reported as a lower bound only** and is not
tested. A Fisher exact test is reported for completeness with this bias stated beside it, and
**is not the basis of any conclusion.**

**Prior art:** liquidation-cascade mean reversion is well documented in crypto. Import.

### D — Taker-order reconstruction

**Claim under test.** The informative unit of flow is the **parent taker order**, not the
individual print, and markout conditioned on reconstructed sweep size separates informed from
uninformed flow better than raw trade size.

**Measurement.** Consecutive trade ids (`t == previous t + 1`), same aggressor side, arriving
within the window in §4, spanning one or more price levels, are one taker order sweeping the
book. Aggressor side is **read** from Binance's `m` flag and never inferred. Segment fills by
the size of the most recent reconstructed sweep.

**Why this is not aggTrade.** `aggTrade` merges same-price fills from one taker order, so a
single sweep across four levels appears as four records. Reconstruction from individual trades
recovers the parent. The zero-gap continuity of `t` was verified on the live venue before this
contract was written.

**Prior art:** trade-size informativeness and stealth trading — Barclay & Warner (1993),
Chakravarty (2001), which find *medium*-sized trades most informative. That prediction is
recorded in §5 as a scoring opportunity, not assumed.

---

## 4. The grid — every free parameter, enumerated

No value here may be changed, and no value not listed here may be varied.

| Conditioner | Parameter | Declared values | Cells |
|---|---|---|---|
| **A** | \|basis\| buckets, bps | `[0,0.5)`, `[0.5,1.5)`, `[1.5,3)`, `[3,∞)` | 4 |
| **A** | sign | basis > 0 and basis < 0, reported separately | ×2 = 8 |
| **B** | lookback | 1 s, 5 s | 2 |
| **B** | cancel-to-depth threshold | 0.25, 0.50 | ×2 = 4 |
| **C** | depletion fraction | 0.50, 0.80 | 2 |
| **C** | burst window | 200 ms, 1000 ms | ×2 = 4 |
| **C** | quiet interval | 500 ms (single value, fixed) | ×1 = 4 |
| **D** | sweep-size buckets, BTC | `[0,0.1)`, `[0.1,1)`, `[1,5)`, `[5,∞)` | 4 |
| **D** | max inter-print gap | 1 ms, 50 ms | ×2 = 8 |
| | | **conditioned cells** | **24** |

Plus **5 reference cells**: the unconditioned primary endpoint recomputed on q5 (1), and each
conditioner's pooled result ignoring its own buckets (4). **Total family = 29.**

**Every cell is declared in the trial ledger before any of them is computed.** A cell that
turns out to be empty or degenerate is reported as such; it is not replaced.

---

## 5. Predictions, recorded before the data

Scored as stated. Being wrong is the point of writing them down.

- **P1 (A).** Median 60 s markout is *less negative* in the widest \|basis\| bucket than in the
  narrowest, by at least 0.5 bps.
- **P2 (B).** Median 60 s markout is *more negative* following high cancellation-to-depth than
  following low, by at least 0.5 bps.
- **P3 (C).** Detector precision against the answer key exceeds 0.60.
- **P4 (C).** Median 60 s markout for fills in the declared quiet interval is *less negative*
  than the unconditioned baseline.
- **P5 (D).** Markout is worst — most adverse — in the `[0.1,1)` and `[1,5)` sweep buckets
  rather than in `[5,∞)`, following the stealth-trading literature. **This prediction is
  imported, and scoring it against Genesis's own data is a check on the import, not a
  discovery.**

---

## 6. Kill conditions, declared before the data

- **K1.** If fewer than 200 fills land in a cell, that cell reports **insufficient data** and
  is excluded from BH correction with its exclusion recorded. It is not merged with a
  neighbour to reach the threshold.
- **K2.** If **no** conditioner survives BH at q = 0.05, COND-1 is reported as **negative** and
  T3.1 proceeds with an unconditioned quoting policy. A negative result closes the question; it
  does not license a further search.
- **K3.** If C's precision falls below 0.30, the inferred detector is **abandoned**, not tuned.
  The grid in §4 is the whole of its permitted variation.
- **K4.** If q5's completeness labels mark more than 25% of the recording incomplete, the
  analysis window is restricted to complete intervals and the restriction is reported on every
  result. It is not silently applied.
- **K5.** If the spot and perp venue clocks are found to disagree by more than 50 ms —
  the assumption in §7 — **A is void**, because the basis would be computed across two
  differently-timestamped books. B and D are unaffected; C is unaffected.

---

## 7. Assumptions carried, unverified

**The cross-venue clock assumption.** Conditioner A compares two books by `venue_ts_ms`.
Genesis has **not** verified that Binance's spot and USD-M futures matching engines timestamp
against synchronised clocks, and currently has no way to. Recorded as an assumption, not a
finding. K5 is its kill condition.

**`received_at` is not used for cross-venue ordering** anywhere in this contract. It was
briefly believed unreliable from this location; that belief was traced to a recorder defect
(D-5) rather than to the link, and corrected — see §9 of
[`../research/binance-futures-stream-availability.md`](../research/binance-futures-stream-availability.md).
It is nonetheless not used, because venue timestamps are the right clock for this question.

**Fills remain inferred.** Genesis has no order in the book. Fills are simulated against
observed book evolution and reported in EXEC-1's ambiguity brackets. **The certain pool is
used throughout**, and no result here is a claim about realised profit.

---

## 8. What is out of scope by construction

No strategy, no signal search outside §4, no position sizing, no P&L, no Sharpe, no capacity
estimate, no live order. Those are T1.2, T3.1 and T3.3, and none of them may borrow authority
from a COND-1 result that has not been corrected under §2.
