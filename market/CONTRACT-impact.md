# IMPACT-1 — what does it cost to close a position into the book that is actually there?

**Status: DRAFT, AMENDED 2026-08-22 before freezing — see §0. Awaiting declaration by Gabana.** Frozen on declaration; nothing below may be
changed afterwards. Written *before* any claim is published, and immediately after the feasibility
run, because the feasibility run came back positive and that is exactly the moment a contract
stops being optional.

**Classification: MEASUREMENT.** Market impact is a fifty-year-old literature — Kyle, Almgren-Chriss,
the square-root law. **No novelty is claimed for the relationship.** What is claimed is narrower and
checkable: that it can be estimated from free public data, conditioned on depth that we measured
rather than assumed, and attached to a wallet whose exact size and free collateral we already hold.


---

## 0. Amendment, 2026-08-22 — P1 was written before it was tested, and it was wrong

P1 below asserts that minute aggregation **understates** the cost of a single sweep. It was run
the same day (`market/impact2.py`, 221,778 bursts) and it **overstates** it, by an order of
magnitude: 0.1–3.7 bps at burst level against 16–44 bps at minute level. The minute-level outcome
was the whole minute's high-low excursion — everyone's trading — not what one taker paid.

The original wording is left standing below. This is recorded here rather than corrected in place
because the contract was not yet frozen and the error is still worth keeping: a pre-condition that
predicted the wrong sign is exactly the kind of thing a contract exists to catch.

**Two consequences, both larger than the amendment.**

**The relationship survives at burst resolution.** Within each prior-volatility band the rows are
not flat, so K1 does not fire. What IMPACT-1 set out to measure is real.

**And it is commercially negligible on BTC.** F-0014 measures the ±1% book at $247.6M on Binance
and $225.6M on Hyperliquid. A $2.1M close is 0.9% of that — about **1 bp, roughly $200**. The
retail execution-cost product this contract was written to license does not exist at this asset.

**P2 is therefore rewritten in effect, though not in text.** The tail census it demands is no
longer a data-sufficiency check; it is the whole experiment. IMPACT-1 continues **only** in the
three regions F-0014 identifies as unmeasured — thin Hyperliquid books, stressed depth regimes,
and the p99 cluster at 38% of the book. A figure quoted from calm BTC is forbidden outright,
not merely bounded.

**P4 gets easier.** Depth parity between the two venues within 9% removes the largest reason to
doubt Binance→Hyperliquid transfer. It does not settle F-0006, which is about behaviour under
stress, and the `estimated, Binance-derived` label stays until it does.

---

## 1. Why this contract exists

Everything else this project proposed to sell has been refuted **by this project**:

| | claimed | outcome |
|---|---|---|
| F-0010 | clusters move price | lost to a volatility-matched control |
| F-0012 | vulnerability ranks clusters | ~100% for 71% of clusters — no contrast |
| F-0013 | survivors differ from casualties | outcome variable is unmeasurable |

Each of those was a **prediction about the market**. IMPACT-1 is a different object: **the cost of
the trader's own action**, verifiable by that trader the moment they trade. It is the one category
`BUSINESS-PLAN §7` permits, and the reason the permission exists is that it is not a forecast.

## 2. The question

> **Given the notional standing within ±1% of mid, how far does price move when aggressive volume
> of a given size arrives — and does that relationship survive conditioning on volatility already
> in progress?**

The second clause is the whole contract. The first clause alone is how CASCADE-1 died.

## 3. What the feasibility run found, stated as evidence and not as a claim

`market/impact.py`, 450 days of Binance `bookDepth` joined to 1m klines, **635,682 minutes**.

**Uncontrolled** (median excursion, bps), which on its own proves nothing:

| volume / depth(±1%) | n | median | p75 | p95 |
|---|---|---|---|---|
| 0 – 0.05 | 614,854 | 3.9 | 7.3 | 15.5 |
| 0.05 – 0.1 | 14,836 | 17.7 | 25.0 | 46.6 |
| 0.1 – 0.2 | 4,589 | 28.4 | 39.8 | 74.4 |
| 0.2 – 0.35 | 1,042 | 47.8 | 66.9 | 117.2 |
| 0.35 – 0.6 | 282 | 73.8 | 101.2 | 191.8 |

**Controlled on the PREVIOUS minute's range** — volatility already in progress, which cannot be
caused by this minute's volume. Median bps, cell counts in thousands:

| prior range | 0+ | 0.05+ | 0.1+ | 0.2+ |
|---|---|---|---|---|
| 0–5 bps | 2 (365k) | 15 (0k) | — | — |
| 5–10 bps | 6 (158k) | 15 (2k) | — | — |
| 10–20 bps | 10 (74k) | 16 (6k) | 26 (1k) | — |
| 20–40 bps | 16 (14k) | 21 (4k) | 27 (2k) | 44 (0k) |
| 40+ bps | 24 (1k) | 35 (1k) | 41 (0k) | 50 (0k) |

**Rows are not flat.** Holding prior volatility fixed, the ratio still separates outcomes. This is
the test CASCADE-1 failed, and it is the only reason this contract exists rather than a fourteenth
refutation.

**It is feasibility, not a finding.** §4 lists the four reasons it may still be wrong.

## 4. Pre-conditions — each can stop the experiment before any number is published

**P1 — THE UNIT IS WRONG, AND MUST BE FIXED.** A minute in which volume equalled 20% of the book
is **not** one order eating 20% of the book. It is hundreds of orders against a book that
replenished between them. The quantity a customer needs is the cost of *one* sweep, and minute
aggregation systematically **understates** it. Until impact is estimated from `aggTrades` —
reconstructing executed VWAP against mid at the start of a contiguous same-side burst — no
number may be quoted to a user in currency or basis points. Binance publishes aggTrades free.
**This is the single largest gap and it is not optional.**

**P2 — TAIL CENSUS.** The region customers care about is the tail, and the tail is thin: 96.7% of
minutes sit in the lowest bucket, and the highest reported uncontrolled bucket holds **282**
observations. Before publication, every cell backing a published figure must hold ≥1,000
observations, or the figure is reported as an interval with its n stated inline, or not at all.

**P3 — INDEPENDENCE.** Minutes are not independent; volatility clusters. The effective sample is
far below 635,682 and must be stated. The unit of observation is a **burst episode**, not a
minute, and confidence intervals are computed by block bootstrap over days, never by treating
minutes as i.i.d.

**P4 — VENUE TRANSFER.** This is measured on Binance. Isobath's wallets are on Hyperliquid.
F-0006 is still ASSUMED and `hl2` is recording to settle it. Until it settles, any Hyperliquid-facing
figure is labelled **estimated, Binance-derived** on the surface it appears on — never `observed`.

## 5. The measurement, once P1 is met

- **predictor**: burst notional ÷ standing notional within ±1% at burst start (last snapshot before)
- **outcome**: executed VWAP against mid at burst start, in bps, signed against the taker
- **control**: the prior minute's range, and separately a matched control — a same-side burst of
  similar size in the same symbol in the same hour. **A result that beats a permutation null but
  loses to a matched control is a failure.** That rule is inherited from CASCADE-1 and is not
  negotiable.
- **stress conditioning**: F-0002 measured near-book depth falling to 0.846 in the largest moves
  and 0.657 in the worst quarter. The published cost must be conditioned on the depth regime, not
  on the quiet-market average, because the quiet-market average is precisely when nobody needs it.

## 6. Kill conditions

Any one ends IMPACT-1 and is published as a refutation.

| | |
|---|---|
| **K1** | At aggTrades resolution the rows go flat within prior-volatility bands — the minute-level result was aggregation artefact |
| **K2** | The relationship loses to the matched same-hour control |
| **K3** | After block bootstrap over days, the CI on adjacent ratio buckets overlaps enough that the estimate cannot distinguish costs worth acting on |
| **K4** | The relationship reverses or vanishes in the stressed-depth regime — i.e. it holds only when it is useless |
| **K5** | F-0006 resolves against transfer, and the Hyperliquid book behaves differently enough that a Binance-derived estimate misleads |

## 7. What may be published either way

**Permitted:** the estimated cost of a stated trade size against the depth actually present, with
its interval, its sample, its venue, and its regime. The statement that the relationship survives
— or does not survive — a volatility-matched control.

**Forbidden regardless of outcome:** any statement about where price will go, any implication that
a large position *will* be closed or liquidated, and any figure presented without its venue label
while F-0006 is unresolved. IMPACT-1 answers "what would this cost you". It does not answer
"what will happen", and a positive result here must not be allowed to relicense the price claim
F-0010 already refuted.

## 8. First read

After P1 is satisfied — aggTrades ingested and burst-level impact estimated — and not before.
The minute-level table in §3 is a reason to do that work. It is not a result.
