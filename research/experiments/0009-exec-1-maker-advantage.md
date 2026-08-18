# 0009 — EXEC-1: does the maker advantage survive adverse selection?

**Date:** 2026-08-10 → 2026-08-17 (recording), 2026-08-17 (analysis)
**Status:** done
**Classification: BUILD — engineering measurement. Not research. No novelty claimed.**
Contract: [`../../market/CONTRACT-execution.md`](../../market/CONTRACT-execution.md), frozen
before the recording began.
Code: [`../../market/exec1.py`](../../market/exec1.py), [`../../market/fills.py`](../../market/fills.py).
Evidence: [`../../market/EVIDENCE.md`](../../market/EVIDENCE.md).
Defects found at close: [`../exec-1-recording-defects.md`](../exec-1-recording-defects.md).
Checks: [`../../tests/test_exec1.py`](../../tests/test_exec1.py),
[`../../tests/test_exec1_end_to_end.py`](../../tests/test_exec1_end_to_end.py),
[`../../tests/test_fills.py`](../../tests/test_fills.py).

The first Genesis experiment to run against its own multi-day prospective recording.

---

## 1. The question

MEASURE-1 produced a break-even table with a **maker** column, priced at 3 bps per side. That
column assumes a resting order actually earns the spread. It does not, if the people trading
against it know something — the price moves against you after you fill, and that adverse
selection eats the advantage.

> **E3 is the deliverable.** What portion of the 3 bps per-side maker advantage survives
> adverse selection at the touch at the 60 s horizon?

Four supporting questions (E1 reach and fill, E2 markout by horizon, E4 distance, E5 latency)
and seven pre-registered predictions X1–X7, all frozen in the contract before any data existed.

## 2. Protocol — frozen before the recording

| | |
|---|---|
| Venue / market | Binance spot, BTCUSDT, `depth` diff stream anchored by REST `depthSnapshot` |
| Grid | 2 sides × 3 offsets (0, 1, 5 ticks), tick $0.01, $10,000 notional |
| Decision times | every 60 s |
| Order TTL | 300 s |
| Latency arms | 291 ms (measured Nairobi floor) and 650 ms (p95) |
| Markout horizons | 1 s, 10 s, 60 s, 300 s |
| Book sampling | every 500 ms |
| Sessions | quiet 03–06 UTC, US 14–21 UTC |
| Exclusion | intervals the recorder labels incomplete |
| Kill condition | >100% of the maker advantage lost at the touch at 60 s |

**The recording carries no trade stream.** Every fill is therefore reported as CERTAIN,
OPTIMISTIC or PESSIMISTIC, and the width of that bracket is a first-class number.

## 3. Data, and what verification found

| | |
|---|---|
| Log | `~/genesis-evidence/q3/btcusdt-q3.jsonl`, 3.4 GB, **580,658 events** |
| SHA-256 | `740fc04d4cf40d81ab60090d3717266c1bc7d6f2e81d8e7880e34193e8381d63` |
| Integrity | **verified** · 0 sequence gaps · 0 malformed · 0 uninterpretable |
| Recorder runs | **1** — unbroken, no restarts, the watchdog never fired |
| Complete time | **93.4%** across 82 incomplete intervals |
| Analysis window | `2026-08-10T13:58:23.770905Z` → `2026-08-17T13:58:23.770905Z`, **168.00 h** |

Zero sequence gaps across 580,658 events is the strongest single statement about the record:
the venue's own U/u contiguity check never once found a missing message.

The recording overran the analysis window by 3 h 54 m because `--seconds` is enforced against a
monotonic clock that stops while the host sleeps (defect D-1); the host slept 6.28 h across 18
episodes. **The window excludes the overrun.** The contract's §3 states the start as 16:58 UTC;
that is EAT, and the recording began 13:58 UTC (defect D-2). The window uses the observed
first event.

## 4. E1 — reach and fill

60,480 orders per arm: 6 cells × 10,080 decision times.

| | 291 ms | 650 ms |
|---|---|---|
| Reached | 39,485 (65.29%) | 39,492 (65.30%) |
| Certain fills | 39,473 | 39,480 |
| Optimistic-only | 2 | 2 |
| Fill-rate bracket | 65.27% – 65.27% | 65.28% – 65.28% |
| **Ambiguity width** | **0.0033 pp** | **0.0033 pp** |

The bracket is effectively zero, as §3 predicted for the touch — and it stays zero away from
it. Outcome mix at the touch: 13,217 certain, 1 optimistic-only, 4 expired, 6,938 never
reached.

Reach by offset (291 ms): **65.58%** at 0t, **65.28%** at 1t, **65.00%** at 5t.
Reach by side at the touch: buy 64.45%, sell 66.71%.

## 5. E2 — adverse selection by horizon

Median markout, certain pool, 291 ms arm:

| horizon | median bps | fraction negative |
|---|---|---|
| 1 s | −0.6014 | 98.9% |
| 10 s | −0.8550 | 92.5% |
| 60 s | **−1.1871** | 77.0% |
| 300 s | −1.1722 | 62.5% |

It grows to 60 s and then stops. The fraction-negative decay is the more informative column:
nearly every fill is adverse one second later, only 62% still are five minutes later.

## 6. E3 — the deliverable

**At the touch, 60 s horizon, 291 ms, certain pool, n = 13,217 fills:**

```
fraction of the maker advantage lost   0.3907
95% CI                                 [0.3676, 0.4139]
Bonferroni 98.75% CI (family of 4)     [0.3592, 0.4195]
contains the 1.0 kill threshold        No
```

**60.93% of the maker advantage survives — 1.828 bps of 3.000.**

Per day (§9 requires it; a figure unstable across days is not a figure):

| day | 08-10 | 08-11 | 08-12 | 08-13 | 08-14 | 08-15 | 08-16 | 08-17 |
|---|---|---|---|---|---|---|---|---|
| lost | 0.3990 | 0.4164 | 0.3542 | 0.4176 | 0.4574 | 0.3168 | 0.3702 | 0.4134 |

Range 0.3168–0.4574. Every day agrees in direction and magnitude; none approaches 1.0.

## 7. Pre-registered predictions — scored

| # | Prediction | Outcome |
|---|---|---|
| X1 | AS grows with horizon and stabilises past 60 s | **confirmed** — 0.60 → 0.86 → 1.19 → 1.17 bps; 300 s is 1.3% smaller than 60 s, not materially |
| X2 | 20–50% lost at 60 s, at the touch, 291 ms | **confirmed** — 39.07%, mid-band |
| X3 | Ambiguity ~0 at the touch and **rises** away | **falsified** — 0.00496 pp at 0t and 1t, **0.0** at 5t |
| X4 | Reach >60% at the touch, **<20% at 5 ticks** | **falsified** — 65.58% → **65.00%** |
| X5 | Worse in quiet hours than the US session | **falsified** — quiet 0.3636, US 0.4155; quiet is *better* |
| X6 | Doubling latency worsens AS measurably | **falsified** — 0.3907 vs 0.3910 |
| X7 | Worse further from the touch | **direction consistent, separation not established** — 0.3907 / 0.3968 / 0.4011, intervals overlap |

Two confirmed, four falsified, one directional-without-separation.

## 8. The kill condition — §6

> If more than 100% of the maker advantage is lost at the touch at 60 s, the maker column of
> the MEASURE-1 break-even table is withdrawn.

**Not triggered.** 39.07% lost, and both the 95% and Bonferroni-corrected intervals exclude
1.0. The maker column stands. Per §6, passing licenses nothing: a surviving maker advantage
says execution is affordable, not that there is anything worth executing.

## 9. The limitation that governs X3, X4, X6 and X7

Found after the run, before the trials were recorded.

At the median order price of **$63,476.05** with `TICK = 0.01`:

```
1 tick   = 0.001575 bps
5 ticks  = 0.007877 bps
measured adverse move at 60 s = 1.1871 bps
```

**The declared 0–5 tick offset grid spans 151× less than the effect it was built to
modulate.** All three offsets are economically the same order on this instrument. The two
latency arms differ by 359 ms against a 300 s TTL — 0.12% of an order's lifetime.

X3, X4 and X7 inherited tick-intuition from instruments where a tick is economically
meaningful; on BTCUSDT it is not. X6 inherited the same error in the time dimension.

Those nulls are properties of the declared grid at least as much as of the market. They are
**recorded rather than withdrawn** — a declared trial cannot be un-declared, and the honest
count includes them — but they must not be cited as evidence that distance from the touch or
latency do not matter to execution.

## 10. Interpretation — kept separate, as §8 requires

> **AUTHORSHIP NOTE: this section is a proposal, not adopted.** Everything above is measured
> and belongs to the record. What follows is reading, and per `ai/collaboration.md` the
> researcher authors it. Edit or delete freely.

- The affordability half of the MEASURE-1 picture holds. Resting is meaningfully better than
  crossing on this instrument, by roughly 1.8 bps per side, and that figure was stable across
  every day of the week observed.
- The experiment answered its deliverable and failed to answer three of its four supporting
  comparisons — not because the market was silent, but because the grid could not speak. That
  asymmetry is the most useful thing here for designing the next one.
- A grid should be specified in **economic** units (bps, or multiples of the measured adverse
  move) and converted to venue units at run time, rather than specified in ticks. The same
  applies to latency arms, which should be specified as a fraction of TTL.

## 11. What this cannot establish

- **Nothing about whether an edge exists.** Execution being affordable is necessary, never
  sufficient.
- **No trade stream**, so fills are inferred from book evolution and bracketed rather than
  observed. The bracket is 0.0033 pp wide, but it is not zero.
- **No queue position.** The hypothetical order never exists in the book, so it displaces
  nobody and changes nothing about what others do.
- **One symbol, one venue, seven days, one geography.** BTCUSDT is the deepest crypto market
  in existence; every liquidity conclusion is a best case.
- **Fees are a snapshot** taken 2026-08-10.
- **X3, X4, X6, X7 are uninformative about the market**, per §9.

## 12. Trial accounting

Family `EXEC-1`, size fixed in advance by the grid and unable to grow. Bonferroni α = 0.0125.

| Trial | Question | Recorded outcome |
|---|---|---|
| `3488b1e1` E3 | >100% survives at the touch at 60 s? | No — 39.07% lost; kill condition not triggered |
| `ad6c400b` X5 | Worse in quiet hours? | No, and opposite in direction; not separated |
| `a4cd747a` X6 | Doubling latency worsens AS? | No measurable difference; structurally limited |
| `c228c389` X7 | Worse further from the touch? | Direction consistent; not separated; structurally limited |

**4 declared, 4 recorded, 0 outstanding.** Ledger chain verified. Descriptive measurements
(E1, E2, X3/X4 scoring, the correction itself, recording provenance) recorded as CONTEXT, not
trials, per §7.

No trial's conclusion changes under the multiple-comparison correction, because none rested on
a marginal separation.

## 13. What the instrument revealed about the process

The recording was excellent — one unbroken run, zero sequence gaps, integrity verified. The
**experiment design** was the weaker part: four of seven predictions were falsified, and three
of those failed because the grid was specified in units that are economically meaningless on
this instrument.

That was not visible until the numbers came back and someone checked what a tick was worth.
It is the same lesson as BAV-1 §9 in a different costume: reconstruction was never the problem;
knowing what the reconstruction could and could not tell you was.

Three engineering defects surfaced at close, recorded in
[`../exec-1-recording-defects.md`](../exec-1-recording-defects.md). D-3 — a documented
integrity command that read nothing and exited 0 — is fixed with regression checks. D-1 and D-2
are open.
