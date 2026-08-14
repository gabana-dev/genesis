# Perpetual funding: who pays, how much, and where it went

**Date:** 2026-08-14
**Status:** exploration — **descriptive measurement, not a trial.** No hypothesis is tested,
nothing accepted or rejected, no strategy proposed or evaluated.
**Data:** Binance USD-M BTCUSDT funding rate archive, 2020-01-01 → 2026-07-31.
**7,212 observations**, 8-hour interval throughout.

---

## 1. Why this one

Every candidate signal in this project has failed the same question: *who is on the other side,
and why are they losing?* Without an answer, an apparent edge is either noise or a sign that
Genesis is the one being harvested.

Perpetual funding is the rare case with a mechanical answer. When the perpetual trades above
spot, longs pay shorts every 8 hours; below, the reverse. Nobody is being outsmarted — one side
is paying a fee for leverage, openly and by design.

## 2. What it pays

| | |
|---|---|
| Mean 8h rate | **+0.01083%** → **+11.86% / year** |
| Median | +0.00942% |
| Standard deviation | 0.02109% |
| Range | −0.300% to +0.300% (the cap) |
| **Periods where longs paid** | **85.7%** |

Longs pay shorts nearly six times out of seven, across six and a half years. That is a
persistent structural flow, not a pattern in prices.

It is also **highly forecastable** — far more so than direction:

| lag | 8h | 24h | 72h | 1 week | 30 days |
|---|---|---|---|---|---|
| ρ | +0.799 | +0.698 | +0.618 | +0.465 | +0.326 |

## 3. A third of it is not market pressure at all

The 75th percentile sits at exactly `+0.01000%`. That is not a coincidence: it is Binance's
default rate, applied when the premium index is neutral.

**2,460 of 7,212 observations — 34.1% — are pinned at exactly that value.**

So a large share of the "funding longs pay" is a mechanical interest-rate component baked into
the formula, not evidence of crowded positioning. Anyone reading the headline 11.86% as a
measure of leverage demand is reading a number that is one-third constant by construction.

Excluding the pinned observations moves the mean only slightly (+12.32%/yr), but the share
pinned collapses over time — and that turns out to be the story.

## 4. It has decayed, and 2026 barely exists

| year | share pinned at default | mean of the rest | annualised gross carry |
|---|---|---|---|
| 2020 | 50.5% | +0.02151% | **+17.19%** |
| 2021 | 43.1% | +0.04155% | **+30.61%** |
| 2022 | 30.8% | +0.00105% | +4.16% |
| 2023 | 38.5% | +0.00542% | +7.87% |
| 2024 | 42.1% | +0.01154% | +11.92% |
| 2025 | 17.2% | +0.00358% | +5.13% |
| 2026 | 3.9% | +0.00143% | **+1.94%** |

In 2021 the perpetual paid **30.6% a year** to anyone willing to be short it against spot. In
2026 so far it pays **1.94%**, and longs paid in only 67.3% of periods against 85–93% in every
earlier year.

**This is the same shape as the other two exploration studies.** Study 1: minute-scale
mean reversion strong in 2020–21, gone by 2024. Study 2: volatility predictability 0.5–0.6 in
2020–22, 0.26–0.39 since. Three unrelated measurements, one pattern — **the obvious things are
being competed away.**

## 5. Cost arithmetic — deliberately not a backtest

Capturing the carry requires holding spot and shorting the perpetual, then unwinding: two legs,
established and closed. Using MEASURE-1's measured round-trip costs — spot 0.20%, futures taker
0.10% — one full cycle costs **0.30%**.

| year | gross carry | one round trip, expressed in days of carry |
|---|---|---|
| 2021 | +30.61% | 3.6 days |
| 2024 | +11.92% | 9.2 days |
| **2026** | **+1.94%** | **56.4 days** |

In 2021 the entry cost was recovered in under four days. In 2026 it takes nearly two months,
and what remains is comparable to a savings account while carrying liquidation risk on the
short leg.

**This is arithmetic on two measured quantities. It is not a backtest, no positions were
simulated, and it says nothing about whether the trade was executable at those prices** —
margin requirements, borrow, funding on the spot leg and slippage are all unmeasured.

## 6. What is deliberately NOT here

**No predictive test.** The obvious next question — does funding predict subsequent returns —
is a fitted model evaluated on data, which the ledger defines as a **trial**. Running it here
under the heading "exploration" would be exactly the laundering the trial counter exists to
prevent. If it is worth asking, it gets declared first.

Also unmeasured: one instrument, one venue; whether spot borrow is available at a rate that
leaves the carry intact; and the 2026 figure covers seven months, not a year.

## 7. What this establishes

That the counterparty question **has** an answer here, which is rare — and that the answer paid
handsomely five years ago and pays almost nothing now.

A third of the headline number is a constant. Most of the rest has been arbitraged away. The
one place in this project where "who is losing, and why" was mechanically answerable is also a
place where the answer stopped being worth much, and the decay is visible year by year.
