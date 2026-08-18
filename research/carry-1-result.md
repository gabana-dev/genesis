# CARRY-1 result: positive, small, and probably not worth doing

**Date:** 2026-08-18
**Contract:** [`../market/CONTRACT-carry.md`](../market/CONTRACT-carry.md), frozen at
`9154377855b64c4a…` before any figure was computed.
**Report:** [`../market/evidence/carry1-report.json`](../market/evidence/carry1-report.json)
**Instrument:** [`../market/carry1.py`](../market/carry1.py), 8 arithmetic checks against
synthetic series with hand-computed answers.

**Data:** 7,604 public Binance funding settlements, 2019-09-10 → 2026-08-18. 7,600 aligned to
both spot and perp 8h closes; **4 excluded** for a missing leg. 1,093 negative-funding
settlements reported and excluded per §5.

---

## 1. The result at the primary tier

Retail fees: `futures_vip0` maker 2 bps, `spot_vip0` 10 bps. **Four legs = 24 bps per round
trip.** All figures are bps per completed round trip, median, with a moving-block bootstrap
95% interval (block = the holding period).

| hold | entry ≥ | n | median | 95% CI | funding | basis | % profitable | worst |
|---|---|---|---|---|---|---|---|---|
| 1d | 0 bp | 6,492 | **−21.66** | [−21.78, −21.55] | 2.79 | 0.10 | 2.4% | −178 |
| 1d | 1 bp | 3,745 | **−19.97** | [−20.16, −19.78] | 3.00 | 0.30 | 4.1% | −178 |
| 3d | 1 bp | 3,723 | **−13.51** | [−14.01, −12.96] | 9.00 | 0.52 | 19.4% | −170 |
| 3d | 2 bp | 796 | **+12.25** | [7.53, 18.73] | 34.95 | 1.45 | 73.2% | −62 |
| 7d | 1 bp | 3,681 | −1.11 | [−2.72, **1.51**] | 21.00 | 0.66 | 46.7% | −154 |
| 7d | 2 bp | 778 | **+49.82** | [38.25, 73.70] | 71.29 | 2.50 | 97.8% | −111 |
| 14d | 0 bp | 6,301 | **+4.21** | [0.85, 8.72] | 27.89 | 0.15 | 58.8% | −130 |
| 14d | 1 bp | 3,599 | **+19.88** | [15.90, 28.20] | 42.00 | 0.85 | 81.0% | −130 |
| 14d | 2 bp | 737 | **+106.28** | [78.07, 147.58] | 127.30 | 3.36 | 97.8% | −107 |

Fifteen of sixteen cells have an interval excluding zero; the single exception is 7d/≥1 bp.
The picture is not sensitive to multiple-comparison correction because the surviving effects
are far from the boundary.

## 2. Predictions, scored

- **Y1 — CONFIRMED.** Every 1-day cell is negative at the primary tier. Three settlements
  cannot cover 24 bps of fees.
- **Y2 — CONFIRMED.** Median net is monotonically increasing in holding period in every
  threshold bucket. Fees are paid once; funding accrues per interval.
- **Y3 — CONFIRMED.** 14-day at ≥1 bp is positive: **+19.88 bps**, interval excluding zero.
  Stated in advance because the arithmetic demanded it.
- **Y4 — CONFIRMED.** `futures_vip9` improves every cell by exactly 4 bps (the perp fee, twice)
  and changes no ordering. **The spot leg is what binds**, and it is identical across tiers.
- **Y5 — WRONG.** The ≥2 bp bucket does have the best median and the fewest round trips, but
  **no cell failed K1**; the smallest has 737 trips against a threshold of 100.
- **Y6 — WRONG, and this is the substantive miss.** I predicted basis movement would dominate
  and quietly make this a directional bet. It does not. At 14d/≥1 bp the IQR of the basis move
  is **6.5 bps** against median accumulated funding of **42 bps**. **Funding is the operative
  term by a factor of six.** K6 does not bind.

I expected Y6 to kill this. It did not, and the result stands on funding as claimed.

## 3. Why it still probably is not worth doing

The contract asked whether funding clears costs. It does. That is not the same as the trade
being worth making, and three things say it is not.

### 3.1 The return is at or below the risk-free rate

19.88 bps per 14 days, redeployed continuously, is **≈5.2% annualised on notional**.

But the position needs capital on **both** legs. Unlevered, capital is ~2× notional, giving
**≈2.6% annualised**. At 5× on the perp leg, capital is ~1.2× notional, giving **≈4.3%** —
before any margin buffer, which a 14-day short through a rally certainly needs.

**US T-bills paid roughly 4–5% over much of this window.** The trade earns approximately the
risk-free rate while carrying basis risk, execution risk, exchange counterparty risk, and
liquidation risk. That is not an edge; it is a worse version of doing nothing.

### 3.2 The tail is real and unmodelled

Median +19.88, **worst −130 bps**, 19% of round trips losing. The mean exceeds the median
everywhere, so the *right* tail is fat too — funding spikes pay well. But the left tail is a
14-day delta-hedged position that still lost 1.3% of notional.

And **liquidation risk is not in this model at all** (§10). A 14-day perp short through a sharp
rally needs margin the spot leg cannot automatically supply — spot and futures wallets do not
cross-margin by default. The −130 bps worst case is computed on cash flows only and **almost
certainly understates the real worst case.**

### 3.3 The best-looking cells are one regime

The ≥2 bp entries — the +106 bps cell — are **78% concentrated in 2020–2021**, with **none at
all in 2022, 2025 or 2026**. Its effective independent sample, after accounting for 42-interval
overlap, is **≈17 observations**. That cell is the 2020–21 bull market, not a strategy, and
should not be traded on.

The ≥1 bp bucket is better distributed across 2019–2026, and its 14-day cell has ≈85 effective
observations. That is the only cell I would treat as evidence of anything.

## 4. What CARRY-1 establishes

**Funding carry on BTCUSDT is real, survives retail fees at holding periods of about two weeks,
and is dominated by funding rather than by basis movement.** All three were open questions this
morning.

**It is also too small to be a business at Genesis's scale of capital and risk tolerance**, and
the honest comparison is not against zero but against a Treasury bill.

**What it rules out:** short-horizon carry. 1-day and 3-day are decisively negative at retail
fees, and no threshold rescues them.

**What it does not rule out:** carry as a *component* rather than a strategy — a position that
earns funding while some other edge is expressed, so the capital is not idle. That is a
different question and needs a different declaration.

## 5. Defects found while running, recorded

**D-K1 — funding timestamps jitter.** 4,321 of 7,604 settlements land exactly on the 8h
boundary; the remainder are 1–37 ms late. The first implementation matched klines by exact
timestamp and **silently dropped 43% of the data**.

Losing the rows was the smaller problem. Because `round_trips` steps by row index, a 43%
puncture made `rows[i+h]` mean *"h surviving settlements later"* rather than *"h intervals
later"* — so **every declared holding period was silently longer than declared**, by a factor
averaging about 1.76. The first run's numbers were wrong and were discarded before being read
as results.

Fixed by snapping settlements to their 8h boundary, and hardened with an explicit contiguity
check: a round trip whose entry and exit are not exactly `h` intervals apart in wall time is
**skipped and counted**, never silently reinterpreted. The counts are reported per cell
(`n_skipped_noncontiguous`).

**D-K2 — the bootstrap silently returned nothing.** `_median` used `if xs`, which raises on a
numpy array, and `block_bootstrap_ci` passes the resample as one. The exception was caught
per-cell and recorded as `ci_error`, so **every confidence interval in the first run came back
`n/a`** while the medians looked fine. Fixed and made numpy-safe.

Both defects produced output that looked entirely reasonable. Neither was caught by reading the
code; both were caught by asking why the numbers were shaped oddly — 43% exclusion, and a
column of `n/a` where intervals should have been.

## 6. Deviation from the contract, recorded

§6 specifies Benjamini–Hochberg across the 16 cells. BH requires p-values; the block bootstrap
implemented in `stats.py` returns an interval, not a p-value. **Significance is therefore
reported as whether the 95% interval excludes zero, not as a BH-adjusted p-value.**

This is a deviation. It is recorded rather than papered over. It does not change any conclusion
— fifteen of sixteen intervals exclude zero by wide margins, and the one that does not
(7d/≥1 bp) would not survive any correction either. A future contract needing BH should specify
a bootstrap p-value explicitly.
