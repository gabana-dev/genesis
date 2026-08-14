# Volatility is predictable; direction is not

**Date:** 2026-08-14
**Status:** exploration — **descriptive measurement, not a trial.** No hypothesis is tested,
nothing accepted or rejected, no strategy proposed. Recorded as CONTEXT.
**Data:** BTCUSDT 1m spot, 2019-01-01 → 2026-07-31, cached. 2,758 near-complete days
(≥1,300 of 1,440 minutes present).
**Method:** 1-minute returns kept **only** where consecutive bars are exactly 60,000 ms apart,
so no return spans a halt or gap. Daily realized variance is the sum of squared 1m returns.

---

## 1. The question

The research journal named volatility as a lever on the grounds that it has more effective
observations than direction. This measures whether that is true on this data, using the same
machinery for both so the comparison is like for like.

The baseline is Corsi's HAR-RV (2009): predict tomorrow's log realized volatility from
yesterday's, the last week's average, and the last month's average. It is a three-term linear
regression, and it is the standard against which volatility forecasts are judged.

## 2. Volatility has long memory

Autocorrelation of log daily realized volatility:

| lag | 1d | 2d | 5d | 10d | 22d | 66d | 132d |
|---|---|---|---|---|---|---|---|
| ρ | +0.730 | +0.582 | +0.495 | +0.378 | +0.378 | +0.183 | +0.189 |

Still +0.19 at six months. Compare with returns, where MEASURE-1 found the linear signal
exhausted within an hour.

## 3. The contrast

All figures are **out-of-sample**, walk-forward: fit on everything before day *t*, predict day
*t+1*, never refit on the future. 2,235 predictions.

| Predicting | Model | OOS R² |
|---|---|---|
| next-day log volatility | HAR (day + week + month) | **+0.5563** |
| next-day log volatility | yesterday's volatility alone | +0.4426 |
| next-day log volatility | long-run mean | −0.1901 |
| **next-day return** | **same three features** | **−0.0037** |

**Same data, same features, same procedure. Volatility: 56%. Direction: nothing at all** —
negative, meaning worse than predicting the average.

That is the cleanest statement of the asymmetry this project has produced.

## 4. But the pooled number flatters — again

Study 1 found that pooling across years hid sign flips. Here pooling inflates R², for a
different reason: it includes *between-year* variation in the level of volatility, which is
trivially predictable. Within a single year the task is harder.

| year | n | HAR | yesterday-only |
|---|---|---|---|
| 2020 | 200 | +0.5956 | +0.5360 |
| 2021 | 362 | +0.4980 | +0.3669 |
| 2022 | 365 | +0.5092 | +0.4093 |
| 2023 | 365 | +0.2868 | +0.0877 |
| 2024 | 366 | +0.2604 | +0.0540 |
| 2025 | 365 | +0.3311 | +0.1431 |
| 2026 | 212 | +0.3926 | +0.2318 |
| **pooled** | 2,235 | **+0.5563** | +0.4426 |

**The pooled 0.5563 is higher than any individual year since 2022.** The honest figure for
recent conditions is roughly **0.26–0.39**.

Two things survive that correction, and both matter:

- **It never goes to zero.** The direction signal decayed to nothing (study 1); volatility
  predictability weakened but stayed clearly positive in every single year.
- **The weekly and monthly terms matter more now, not less.** In 2024 yesterday-alone managed
  +0.054 while HAR managed +0.260 — nearly five times as much. Whatever has decayed, it is the
  very short memory, not the long one.

## 5. What this does NOT establish

**Predictability is not profit, and the gap is the whole question.**

The market already forecasts volatility and prices it — in options, and in perpetual funding.
To make money you must beat *the market's* forecast, not the historical mean. This study
compares HAR against a naive baseline, not against implied volatility, because no options data
was used and none is held.

So the correct reading is: **there is real, persistent, out-of-sample structure in volatility
on this instrument.** Whether any of it is *unpriced* is untested, and is a much harder
question than the one answered here.

Also unestablished:

- **No instrument.** Expressing a volatility view needs options or a variance product at
  accessible cost. None has been assessed.
- **Linear, three-term.** HAR is a deliberately simple baseline. This says nothing about
  whether richer models do better, and the point of using it is that it is hard to overfit.
- **One instrument, one venue.**
- Realized volatility from 1-minute bars is itself an estimate, and it is noisy.

## 6. Why it is worth recording

Study 1 established that the direction signal at minute scale is decaying toward nothing.
This establishes that on the same data, over the same period, the volatility signal is not.

That is a genuine asymmetry in where structure survives, measured rather than assumed — and
if any future work is proposed at the affordable horizons, this is the first place the
evidence says to look.
