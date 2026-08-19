# NET-1 — does netting change the answer, and does the volatility holon earn its place?

**Status: FROZEN 2026-08-19, before any forward observation exists.** No arm, gate, threshold,
benchmark, prediction or kill condition below may be changed after this point. If a defect is
found it is reported and recorded, not silently repaired.

**Classification: BUILD. No novelty claimed.**

---

## 1. Why this exists

ECON-1 charges a **full round trip at every 8-hourly decision**. Measured on DIR-2's
predictions, consecutive signals flip sides only **11.2%** of the time at one day — so **89% of
ECON-1's trades close a position and immediately reopen the same one.**

Netting consecutive same-side signals cuts cost per decision from **3.105 bps to 0.348 bps**.
That moves the break-even hit rate:

| execution | 1-day bar | 3-day bar |
|---|---|---|
| full round trip each decision (ECON-1) | 0.5218 | 0.5117 |
| **netted** | **0.5024** | **0.5013** |

**Netting very nearly deletes the fee barrier.** It could not be added to ECON-1 — Amendment 1
states that anything loosening the test voids it — so it is declared here instead, **before
ECON-1 reads**, so that neither contract can be shaped by the other's outcome.

## 2. The second question, and why it is now a weaker idea than it looked

Genesis built a HAR-RV volatility holon and never connected it to the bar. The bar is
`p* = 0.5 + c/(2φm)`, and a volatility forecast predicts **m** — so the holon's natural job is
to say when the prize is large enough to be worth the toll.

**That justification largely evaporates under netting.** At a 0.5024 bar the toll is almost
nothing, and **sitting out then costs edge while saving a cost that no longer exists.** The
gate may be strictly harmful.

So it is tested against an ungated control rather than assumed useful. That is the honest
design and it is why A1 exists.

**Basis declaration.** The holon is marked **FITTED, not MEASURED**, because the exploration
producing its out-of-sample figures committed a writeup but not its code. Its honest per-year
OOS R² is **0.26–0.39** (the pooled 0.5563 is inflated by between-year level variance and is
not used). **No result here may claim MEASURED basis for the volatility forecast.**

## 3. Data — the same forward stream as ECON-1

NET-1 reads **ECON-1's observation log**, `~/genesis-evidence/econ1/observations.jsonl`. Same
frozen DIR-2 specification, same predictions, same decision points from **2026-08-20**. Only the
**execution accounting** differs.

> **Two frozen contracts now sit on one forward sample.** That is legitimate because both were
> frozen before any of it existed, but it is a family of two and **any "best of ECON-1 and
> NET-1" reading must be corrected for that.** Reporting whichever comes out better, alone, is
> not permitted.

**Volatility input.** Daily realized volatility computed from **24 hourly log returns**, fed to
the HAR of `holons/volatility.py`. This differs from the holon's minute-based estimator, so its
0.26–0.39 R² **does not automatically transfer** and no claim is made that it does.

## 4. The arms and the gates

| | arm | rule |
|---|---|---|
| **A1** | netted, **ungated** | hold while the side is unchanged; trade only on a flip |
| **A2** | netted, gate at median | as A1, but hold flat unless the HAR forecast exceeds its own **trailing 60-day median** |
| **A3** | netted, gate at p70 | as A1, but hold flat unless the forecast exceeds its **trailing 60-day 70th percentile** |

Two thresholds only, fixed here, no sweep. Trailing windows end at the decision point.

**Family NET-1 = 3 arms × 2 horizons = 6 declared trials.** Fixed by this table, unable to grow.

## 5. Endpoint and benchmarks

**Primary endpoint: mean net return per DECISION, in bps** — not per trade. Per-decision is the
only unit on which a netted and a non-netted strategy are comparable, since they differ in how
many trades a decision produces.

```
net_per_decision = side × forward_return − (round_trip_cost × trades_this_decision)
```

`trades_this_decision` is 1 on a flip and 0 otherwise. Cost stack identical to ECON-1: 3.105 bps
per round trip at Hyperliquid tier 0.

Benchmarks, all four, as ECON-1 §4.2 — **B1** positive, **B2** buy-and-hold, **B3** sign
permutation at the p95 of 10,000 draws, **B4** exposure-matched constant position. All must
clear.

**Plus one comparison specific to this contract:**

- **B5 — the gate must beat the ungated arm.** A2 and A3 must each exceed A1 at the same
  horizon. A gate that does not beat no gate is decoration, and per §2 it may well be worse.

## 6. Predictions

- **N1.** A1 (netted, ungated) beats ECON-1's non-netted net-per-decision at the same horizon.
  This is close to arithmetic and I expect it to hold.
- **N2. B5 fails for both gates.** The volatility gate does **not** beat the ungated arm. With
  the fee barrier nearly gone, abstaining forfeits edge and saves almost nothing. **This is the
  prediction I most expect to be right and would most like to be wrong about.**
- **N3.** The 3-day horizon beats the 1-day on net-per-decision, because the move scales with
  the horizon while the cost does not.
- **N4.** A1 still fails **B4** — it does not beat a constant position at its own net exposure.
  If N4 holds alongside ECON-1's F7, the signal's return is exposure rather than timing, and
  netting merely made a non-edge cheaper to hold.
- **N5.** Gate coverage is roughly 50% for A2 and 30% for A3, and per-decision net falls
  roughly in proportion to coverage — the signature of a gate that removes trades without
  improving their quality.

## 7. Kill conditions

- **K1.** No read before **270 completed decisions**, matching ECON-1, and no read of NET-1
  before ECON-1's own first read. Reading the cheaper variant first would be choosing the
  answer.
- **K2.** If A1 fails B4, **netting is reported as a cost improvement to a strategy that has no
  edge**, and the netted programme closes with it. A cheaper way to hold a non-edge is not a
  finding.
- **K3.** If B5 fails for both gates, **the volatility holon is reported as not useful as a
  trading gate.** That closes the question — it does not license new thresholds, a different
  volatility estimator, or a different gate variable.
- **K4.** If the two-contract family (ECON-1, NET-1) is read jointly, the best result must
  exceed the **p95** of the corresponding zero-skill null, as DIR-2's corrected K3 requires.
- **K5.** Any change to the DIR-2 specification, the cost stack, or the gate thresholds voids
  the run.

## 8. Known limitations

**Funding is unmodelled, and it is a LEVEL effect rather than a differential one.** On
perpetuals, funding is exchanged every 8 hours against held inventory. A netted strategy holds
for ~8.9 decisions on average — about 3 days — crossing roughly 9 settlements. At a median near
1 bp per interval and a net exposure of 0.42, that is a drag of about **3.8 bps per trade**.

**It does not favour either arm.** The non-netted strategy closes and immediately reopens, so it
holds across the same settlements and pays the same funding. Netting saves roughly **24.5 bps
per trade** in fees against that shared 3.8 bps of funding, so the comparison in §1 stands.

*(An earlier draft of this section claimed funding was larger than the netting saving. That was
wrong — it compared a per-trade funding figure against a per-decision fee saving. Corrected
before freezing; recorded rather than silently deleted.)*

**What is genuinely missing:** funding is unmodelled in **both** ECON-1 and NET-1, so both
overstate absolute net return by roughly 3.8 bps per 3-day hold at this exposure. That is a
level correction to both, not a reason to prefer either. A funding-aware variant is a separate
declaration.

**The volatility estimator differs from the holon's**, per §3.

**One asset, one venue, one model form.** No claim beyond BTCUSDT on Hyperliquid pricing.

## 9. Out of scope

No sizing, no leverage, no live order, no agent, no change of model class.
