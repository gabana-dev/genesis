# FOLLOW-1 — does riding persistently profitable wallets pay?

**Status: FROZEN 2026-08-19, before any wallet has been scored.** Frozen at the same moment as
[`CONTRACT-fade.md`](CONTRACT-fade.md), so neither can be shaped by the other's outcome. No
score, window, threshold, benchmark, prediction or kill condition may be changed after this
point.

**Classification: IMPORT + BUILD. No novelty claimed.** Copy trading is a large commercial
industry — eToro, Bybit, Binance and Hyperliquid all sell it. Nothing here is a new idea. What
is different is that Genesis can identify the cohort from **realised profit** rather than from
a platform's leaderboard, and can test it against benchmarks that industry does not report.

---

## 1. The mirror

FOLLOW-1 is FADE-1 with the sign reversed and the cohort taken from the **top** decile. Every
definition in §4–§7 of [`CONTRACT-fade.md`](CONTRACT-fade.md) — the data, the sampling bias, the
`skill_w` score, the 200-fill minimum, the position reconstruction, the hourly decisions, the
1-day horizon, the cost stack, and benchmarks B1–B4 — applies unchanged.

Two differences, and only two:

1. **The cohort is the TOP decile of `skill_w` in W1.**
2. **The position takes the cohort's sign**, not its opposite.

Both contracts are declared together so that reporting whichever wins is not available. **They
are a family of two**, and K5 requires the joint correction.

## 2. Why this is the weaker of the two, and it is declared as such

**Most high-profit wallets on a perp DEX are market makers.** Their profit is spread capture
under tight inventory control. Following a market maker's *trades* means taking the other side
of the flow they earn from — you become the adverse selection they price against. F6 tests for
this directly and K4 closes the contract if it holds.

**A winner's edge may be uncopyable.** If it comes from latency Genesis cannot match, or from
leverage and collateral structure it cannot replicate, or from a hedge on another venue that is
invisible here, the positioning signal carries information that cannot be monetised at 291 ms
and a daily horizon.

**Winners are less persistent than losers.** Skill is hard to separate from luck in any finite
sample, and a top decile selected on 30 days of realised profit contains an unknown fraction of
wallets that were simply fortunate. FADE-1's F4 and this contract's G4 test the same property
on opposite tails, and the tails are not symmetric.

**This is not a reason to skip it.** It is the industry's own hypothesis, it is cheap to test
alongside its mirror, and if the two disagree that difference is itself the finding.

## 3. Endpoint and benchmarks

Identical to FADE-1 §7: **mean net return per decision in bps**, not accuracy, against B1
(positive), B2 (buy-and-hold), B3 (sign permutation at the p95), and **B4 (exposure-matched
constant position)** as the primary passive benchmark.

The exposure objection cuts the *other* way here. If the profitable cohort is persistently
long — likely, in a sample where the asset rose — then following them is persistently long, and
**B4 is what separates skill from beta.** Clearing B1 while failing B4 means the cohort simply
held the asset.

## 4. Predictions

- **G1.** The profitable cohort is persistently **long**, net exposure above +0.5 z across W2.
- **G2.** B1 clears; following produces a positive mean net return per decision.
- **G3. B4 FAILS**, for the same reason FADE-1's F3 is expected to fail: the return is exposure
  in a rising market, not timing.
- **G4.** Cohort persistence is **weaker** than FADE-1's: fewer than 40% of the W1 top decile
  remain in the top quintile when W2 is scored independently, against FADE-1's F4 threshold of
  40% for the bottom.
- **G5.** **FADE-1 outperforms FOLLOW-1** on the primary endpoint. Stated in both contracts, so
  it is one prediction rather than two chances.
- **G6.** More than half the top decile's fills are **maker** (`crossed == false`) — they are
  market makers, and K4 then applies.

## 5. Kill conditions

- **K1.** No read until the harvest covers 60 days, as FADE-1.
- **K2.** Fewer than 50 wallets in the cohort or fewer than 500 decision points: **unevaluable**.
- **K3.** B1 clearing while B4 fails is reported as **exposure, not skill**, and the contract
  closes.
- **K4.** If G6 holds — the cohort is predominantly maker — FOLLOW-1 reports that **the
  profitable cohort is market-making and its edge is structurally uncopyable**, and closes. This
  is the most likely single outcome and it is declared as such.
- **K5. Joint correction.** FADE-1 and FOLLOW-1 are a **family of two frozen at the same
  moment**. Any reading of "the better of the two" must clear the p95 of the corresponding
  zero-skill null, in DIR-2's corrected form. **Reporting whichever came out ahead, alone, is
  not permitted.**
- **K6.** The sampling bias of FADE-1 §4 is restated on every figure.
- **K7.** Any change to score, cohort, windows or cost stack voids the run.

## 6. Known limitations

As FADE-1 §11, in full: one venue, one asset, position reconstruction dependent on complete
`startPosition` history, hedges on other venues invisible, and latency unsimulated.

**One addition.** The public leaderboards that commercial copy-trading products rank by are
computed on returns, not on realised profit per unit traded, and are not survivorship-corrected.
FOLLOW-1's cohort is **not** those leaderboards and no result here speaks to their performance.

## 7. Out of scope

No sizing, no leverage, no live order, no per-wallet trading, no agent.
