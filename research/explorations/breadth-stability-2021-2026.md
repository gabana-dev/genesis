# Cross-sectional breadth, 2021–2026: the one thing that did not collapse

**Date:** 2026-08-14
**Status:** exploration — **descriptive measurement, not a trial.** No hypothesis tested,
nothing accepted or rejected, no strategy proposed.
**Data:** Binance USD-M perpetual futures, 4h bars, 2021-01-01 → 2026-07-31.
**Universe:** 28 perps with continuous history from January 2021, held **fixed** across every
window so that changes measure the market and not the sample.
**Instrument:** [`../../market/breadth.py`](../../market/breadth.py), tested in
[`../../tests/test_breadth.py`](../../tests/test_breadth.py).

---

## 1. The question

[`crypto-cross-section-breadth-study.md`](../crypto-cross-section-breadth-study.md) measured
one year and found 33 perps carrying ~2 independent bets directionally, ~24 once the market
factor is removed. It listed a caveat: *"breadth over long samples is lower than 24.06"*,
because the instruments contributing independence are the newest.

Three exploration studies since have found the same shape in unrelated places — minute-scale
reversion, volatility predictability and funding carry were all strong in 2020–21 and are
weak or gone now. So: **did the cross-sectional independence decay too?**

## 2. Results

| window | k | bars | mean ρ | PC1 | breadth | residual |
|---|---|---|---|---|---|---|
| 2021H1 | 28 | 940 | 0.604 | 62.8% | 2.49 | 22.19 |
| 2021H2 | 28 | 1103 | 0.593 | 62.0% | 2.55 | 22.36 |
| 2022H1 | 28 | 1055 | 0.718 | 73.2% | 1.85 | 22.61 |
| 2022H2 | 28 | 1103 | 0.669 | 68.4% | 2.11 | 22.93 |
| 2023H1 | 28 | 1085 | 0.681 | 69.6% | 2.05 | 23.36 |
| 2023H2 | 28 | 1103 | 0.549 | 57.1% | 2.98 | 21.62 |
| 2024H1 | 28 | 1091 | 0.654 | 67.2% | 2.19 | 21.48 |
| 2024H2 | 28 | 1103 | 0.656 | 67.5% | 2.16 | 18.55 |
| 2025H1 | 28 | 842 | 0.710 | 74.5% | 1.79 | 20.07 |
| 2025H2 | 26 | 1103 | 0.731 | 74.8% | 1.77 | 15.66 |
| 2026H1 | 26 | 1085 | 0.618 | 65.0% | 2.33 | 18.97 |

`breadth` = eigenvalue participation ratio. `residual` = the same after removing the first
principal component. FTMUSDT stopped trading during 2025H2 and is excluded from that window
onward, along with one further instrument lost at the alignment step.

## 3. What it says

**Directional breadth did not change.** It sits between 1.77 and 2.98 across five and a half
years, with no trend: 2.49 at the start, 2.33 at the end. **Thirty crypto perps have been
roughly two bets the entire time.** Whatever else changed, that did not.

**Residual breadth declined, but did not collapse.** From ~22–23 in 2021 through 2023H1, to
~16–19 in 2024H2 through 2026H1 — a fall of roughly 20–25%. The market factor strengthened over
the same period, with PC1 rising from 62% to a peak of 74.8%.

**This is the first of the four exploration studies where the answer is "weakened, not gone".**

| measurement | 2020–21 | now |
|---|---|---|
| minute-scale mean reversion | 8.4 se below random walk | ~0.5 se |
| volatility predictability | R² 0.50–0.60 | 0.26–0.39 |
| funding carry | 30.6%/yr | 1.94%/yr |
| **residual breadth** | **22–23** | **16–19** |

The first three fell by an order of magnitude or to nothing. This one fell by a fifth.

## 4. It also confirms the earlier caveat

Yesterday's study measured residual breadth of **24.06** using 33 perps over the most recent
twelve months, and predicted that a longer window would give less because the independence
comes from the newest instruments.

This study, on a universe with five years of history and none of those newer names, gives
**15.66–18.97** over the same recent period. The caveat was correct, and the size of the gap —
roughly 5 to 8 effective bets — is the contribution of instruments too young to have history.

That is a real tension for any long-sample work: **the instruments that provide independence
are the ones you cannot test over a long sample.**

## 5. Limitations

- **Survivorship.** The universe is 28 perps that were listed in January 2021 *and* still
  traded in 2026. Instruments delisted in between are absent, which biases the sample toward
  survivors. FTMUSDT dropping out mid-study is a visible instance of what is otherwise invisible.
- **Eigenvalue bias.** With k=28 and n≈1,100, `k/n ≈ 0.025`, so Marchenko–Pastur bias is modest
  — noise eigenvalues spread roughly over [0.71, 1.34] rather than sitting at 1. The levels are
  therefore approximate. Since k and n are near-constant across windows the bias is near-constant
  too, which is why this study reads **trends** and not magnitudes.
- **In-sample PC removal** flatters the residual figure, as before. It is an upper bound.
- **Correlation is regime-dependent** and rises in stress — half-year windows average across
  regimes rather than isolating them.
- 2026H2 is one month and was excluded as insufficient.
- Breadth is **necessary, not sufficient**: it measures room, not that anything occupies it.

## 6. A note on how the dead ticker surfaced

FTMUSDT stopped trading and its returns went to exactly zero variance, which produced `NaN` in
the correlation matrix and crashed the eigenvalue decomposition. The crash was the good
outcome. Had the `NaN` propagated quietly it would have silently corrupted two windows, and
nothing in the output would have looked unusual.

The fix drops instruments with zero variance in a window and names them, so an instrument
leaving the universe is visible in the result rather than absorbed into it.
