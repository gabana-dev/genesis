# DIR-1 result: nothing predicts direction at a reachable horizon

**Date:** 2026-08-18
**Contract:** [`../market/CONTRACT-direction.md`](../market/CONTRACT-direction.md), frozen at
`0e319d3630e1c3d8…` before any predictive figure was computed.
**Report:** [`../market/evidence/dir1-report.json`](../market/evidence/dir1-report.json)
**Instrument:** [`../market/dir1.py`](../market/dir1.py), 7 harness checks including a positive
and a negative control.

**Data:** 8,307 eight-hourly decision points, 2019-01-01 → 2026-08-01, built from 3,983,271
one-minute BTCUSDT bars plus the CARRY-1 funding and basis archive. 22 purged walk-forward
windows per cell, ~5,940 out-of-sample predictions each.

---

## 1. The result

**K2 fires. No cell in the declared grid clears its bar.**

| feature set | horizon | accuracy | bar (φ=0.5) | 95% CI | window SD |
|---|---|---|---|---|---|
| F4 momentum | 1d | **0.5111** | 0.5281 | [0.4951, 0.5269] | 0.048 |
| F1 funding | 1d | 0.5032 | 0.5281 | [0.4880, 0.5192] | 0.044 |
| F2 basis | 1d | 0.5007 | 0.5281 | [0.4852, 0.5163] | 0.043 |
| F6 combined | 1d | 0.4995 | 0.5281 | [0.4833, 0.5152] | 0.038 |
| F5 trade size | 1d | 0.4981 | 0.5281 | [0.4818, 0.5138] | 0.042 |
| F3 HAR-RV | 1d | 0.4970 | 0.5281 | [0.4800, 0.5128] | 0.042 |
| F4 momentum | 3d | 0.4934 | 0.5151 | [0.4689, 0.5192] | 0.082 |
| F2 basis | 3d | 0.4896 | 0.5151 | [0.4650, 0.5147] | 0.087 |
| F1 funding | 3d | 0.4879 | 0.5151 | [0.4625, 0.5133] | 0.075 |
| F3 HAR-RV | 3d | 0.4860 | 0.5151 | [0.4593, 0.5116] | 0.085 |
| F5 trade size | 3d | 0.4860 | 0.5151 | [0.4594, 0.5114] | 0.087 |
| F6 combined | 3d | 0.4848 | 0.5151 | [0.4616, 0.5089] | 0.059 |

**Every 95% interval contains 0.50. Not one contains its bar.** The best cell in the entire
grid is 1.7 percentage points short of the threshold it had to clear.

**K4 also fires, in all twelve cells.** Per-window accuracy standard deviation runs 0.038 to
0.087, against edges over a coin flip of 0.0005 to 0.011. **The regime-to-regime variation is
between four and one hundred times the size of the effect.** Per K4, no cell may be reported as
tradeable whatever its pooled accuracy — and none clears its bar anyway.

## 2. The harness was bracketed before it was trusted

An accuracy near 50% is what almost any bug produces, so the harness was tested at both ends
before the real run:

- **Positive control:** an oracle feature equal to the forward return scored **1.000** across
  5 windows. The harness does not destroy signal that is present.
- **Negative control:** pure noise scored **0.498**. The harness does not manufacture signal.

Plus three leakage checks: training labels cannot reach into the test window (purge), test
labels cannot reach into the training window (embargo), and trailing z-scores at index *i* are
bit-identical when every observation after *i* is violently changed.

Without the positive control this null would be indistinguishable from a harness that silently
discarded everything.

## 3. Predictions, scored — I was wrong about most of the details

- **D1 — CONFIRMED.** No single feature clears 52.8% at 1 day.
- **D2 — WRONG.** I predicted momentum would be the *weakest* at 1 day, at or below 50%,
  because it is the most crowded effect in the most liquid crypto asset. It is the **best cell
  in the grid** at 0.5111. Still fails, but for the opposite reason to the one I gave.
- **D3 — WRONG.** I predicted funding would be the best single feature at both horizons,
  because it is the only one carrying positioning rather than price. It is second at 1 day and
  third at 3 days. **The one feature I had a mechanism for was not the one that did best.**
- **D4 — CONFIRMED on its out-of-sample half.** F6 combined fails to beat F1 funding out of
  sample at both horizons (0.4995 vs 0.5032 at 1d; 0.4848 vs 0.4879 at 3d). Eleven correlated
  features on a weak signal made it worse, exactly as predicted.
- **D5 — CONFIRMED, in every cell.** See §1.
- **D6 — WRONG.** I predicted the 3-day horizon would clear its lower bar somewhere the 1-day
  did not. **Every 3-day cell is worse than every 1-day cell**, and all six are below 50%.

Four of six predictions wrong on the mechanism, and the headline conclusion right anyway. The
mechanism guesses were worth writing down precisely because they were falsifiable.

## 4. A defect in the contract, found by running it — D-D1

**K3 as written is a weak test, and I did not notice until it produced an answer.**

K3 says a best cell is noise unless it exceeds the **expected** best-of-12 accuracy under zero
skill. That expectation is the **mean** of the null distribution of the maximum — and beating
the mean of a distribution is roughly a coin flip. K3 as specified rejects only half of pure
noise.

The measured null: best-of-12 at n=5,940 has **mean 0.5106** and **p95 0.5170**.

The best cell scored **0.5111**. It exceeds the mean by 0.0005 — so `exceeds_zero_skill_
expectation` reports **True** — and sits far below the 95th percentile. **The correct reading
is that the best cell is comfortably inside the zero-skill distribution: it is noise.**

Recorded, not repaired. The conclusion is unaffected because K2 and K4 both fire independently,
but a future contract must compare against the **p95 of the null maximum**, not its mean.

Note also what the null itself says: with twelve trials at this sample size, **the best of
twelve coin flips averages 51.06% and reaches 51.70% one time in twenty.** The 3-day bar is
51.51%. **A grid of twelve trials would clear the 3-day bar by chance alone more than 5% of the
time.** Pre-registration is what makes that visible rather than exciting.

## 5. The inversion trap, named so it stays closed

All six 3-day cells score **below** 50%. Inverted, F6 combined at 3 days would be 0.5152 —
fractionally above its 0.5151 bar.

**This may not be reported as a finding and is not one.** The contract declared the prediction
as the sign of the fitted value. Flipping that sign after seeing it fail is a second hypothesis
tested on the same data, chosen because it worked — the exact forking path the freeze exists to
prevent. It also clears the bar by 0.0001, against a null whose best-of-twelve reaches 0.5170
one time in twenty.

It is written here because it is tempting, someone will think of it, and the honest place for
it is a **new declaration on data this experiment did not touch** — not a footnote in this one.

## 6. What DIR-1 establishes

**Directional prediction at reachable horizons is CLOSED for this feature set**, on 3.98M
minute bars spanning 2019–2026, two full market cycles, under purged walk-forward validation
with a harness verified at both ends.

Combined with the two earlier closures:

| direction | status | why |
|---|---|---|
| Market making | **closed** | spread 0.00154 bps against 5.19 bps of cost; 0% maker fee does not rescue it |
| Carry | **positive, not worth doing** | ≈2.6–4.3% annualised on capital against a 4–5% risk-free rate |
| Direction, 1d/3d | **closed** | best cell 0.5111 against a 0.5281 bar, inside the zero-skill distribution |

**What is NOT closed**, and needs its own declaration rather than an extension of this one:

- **VPIN and true order-flow imbalance.** Excluded from DIR-1 because the archived bars carry
  no aggressor side (§4.1 of the contract). It remains the strongest untested candidate, and
  testing it requires Binance's historical aggTrade dumps.
- **Non-linear models**, which per §3 may only be declared *after* a linear model clears the
  bar. No linear model cleared it, so this stays shut.
- **Other assets.** Pindza (2026) found no cross-asset transfer, and Genesis's cross-section
  holon measured effective breadth 1.03 across 25 instruments. Extrapolation is not available.

## 7. What this cost, and what it bought

Three candidate directions, three contracts frozen before the data, three answers. Two closed
with evidence and one closed as uneconomic.

That is not a trading system. It is the elimination of the three things most people spend years
losing money on, each one refuted by a pre-registered test against a measured cost bar rather
than by an opinion.
