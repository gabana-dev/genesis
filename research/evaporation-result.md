# The order book thins by 15% exactly when a cascade would be running

**Date:** 2026-08-20
**Data:** Binance USD-M `bookDepth`, BTCUSDT, **1,324 days** (2023-01-01 → 2026-08-19),
**3,733,943 snapshots**, **0 missing days**. Free and public.
**Code:** `market/bookdepth.py`, `market/evaporation.py`, `market/evaporation_run.py`

---

## 1. The result

Depth **after** a window divided by depth **before** it, bucketed by how large the move was, on
non-overlapping observations.

### Near book, ±0.2–1% of mid

| horizon | quiet market | largest moves | worst quarter (p25) | distinct days |
|---|---|---|---|---|
| **1 min** | 1.0003 | **0.9773** | 0.8700 | 313 |
| **5 min** | 1.0015 | **0.8462** | **0.6573** | 160 |
| **15 min** | 1.0030 | **0.8586** | 0.6646 | 85 |

### Far book, ±2–5% of mid

| horizon | quiet market | largest moves | worst quarter |
|---|---|---|---|
| 1 min | 1.0001 | 0.9866 | 0.9345 |
| 5 min | 1.0006 | **0.8870** | 0.7612 |
| 15 min | 1.0017 | **0.8586** | 0.7522 |

**In quiet markets the book is unchanged to four decimal places, across 1,320 distinct days.**
That is the control working — no drift, no normalisation artefact. The effect appears only where
it is claimed to appear.

## 2. Three things in the structure

**Withdrawal takes minutes, not seconds.** At a 1-minute horizon the book barely flinches
(0.977). At 5 minutes it has fallen to 0.846. Liquidity does not vanish on impact; it leaves over
the following minutes.

**The consequence for cascade modelling is direct and nobody models it:** a fast cascade meets a
nearly full book, a slow grinding one meets a book that is leaving. Identical forced flow,
materially different outcome depending on how long the move takes to play out.

**Withdrawal is concentrated near the touch.** At 5 minutes the near book falls to 0.846 while the
far book holds at 0.887 — the liquidity disappears exactly where the first forced flow lands.

**The tail is worse than the median.** A quarter of large moves see the near book fall to
**0.657**. A cascade estimate built on the median understates the bad cases by half again.

## 3. What this overturns

Every liquidation heatmap on the market — Coinglass, HyperPerps, 0xArchive's projected levels —
computes cluster impact against a **static book**. That assumption is worth 1.000, and it is
correct in quiet markets to four decimals.

**It fails by 15% precisely when a cascade would be running**, and by 34% in the worst quarter.

The direction matters: a static-book model is **optimistic**. It tells a trader the cascade stops
sooner than it does.

## 4. What it does not show

**Not causation.** Depth falling during a move is equally consistent with makers withdrawing
quotes and with quotes being consumed. Both make a cascade travel further — which is what the
model needs — but *"market makers pull liquidity"* is a story this measurement does not test.

**Not Hyperliquid.** This is Binance. Applying it to Hyperliquid is
[`F-0006`](../findings/F-0006-binance-physics-transfer.md), which is `ASSUMED` and carries a
publication ban until `hl2` settles it.

**Not a forecast.** It is a conditional description: *given* a move of this size, the book was
this much thinner. It says nothing about predicting the move.

## 5. How the earlier number changes

The 30-day preliminary reported **0.894** for moves of 0.475–1.271%. Against the full history:

| | 30 days | 1,324 days |
|---|---|---|
| moves 0.53–1.09% | — | 0.9613 |
| moves >1.09% | — | **0.8462** |

The direction was right and the bucketing was too coarse. **The real effect is sharper and
concentrated in genuinely large moves** rather than smeared across medium ones — which is exactly
what more data should do to a real effect and would not do to noise.

## 6. Method notes that matter

**Non-overlapping.** Snapshots are 30 s apart against horizons of 1–15 minutes, so raw rows share
most of their window. Striding at the horizon took 879,117 rows to 117,160 at 15 minutes. An
earlier version of this analysis reported **0.726** for the largest bucket — the most dramatic
number in the table — and **that bucket vanished entirely** once overlap was removed. It was 26
views of the same few minutes.

**Normalised by hour-of-day** in the relative-depth path, because liquidity has a strong diurnal
cycle and an unnormalised comparison would measure the clock. The ratio measure used here needs
no normalisation — before and after are minutes apart, so the cycle divides out.

**`distinct_days` reported on every bucket.** Volatility clusters, so 313 observations drawn from
three days would be three observations in a costume. The extreme buckets span 85–313 distinct days
across 3.6 years.

**Levels are per-offset, not cumulative.** The venue reports notional AT each offset; treating
them as cumulative would silently rescale everything.
