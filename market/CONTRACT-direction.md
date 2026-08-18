# DIR-1 — can anything predict direction at a reachable horizon?

**Status: FROZEN 2026-08-18, before any predictive figure has been computed.** No feature,
horizon, model class, threshold, prediction or kill condition below may be changed after this
point. If a defect is found it is reported and recorded, not silently repaired.

**Classification: IMPORT + BUILD. No novelty claimed.** Every feature below has decades of
prior art. What is being tested is not whether these features are known, but whether any of
them clears **Genesis's own measured cost bar** on **Genesis's own out-of-sample protocol**.

---

## 1. The bar, which was measured before this contract and is not negotiable

MEASURE-1's break-even table, futures maker, capture φ = 0.5:

| horizon | median absolute move | break-even hit rate |
|---|---|---|
| 1 min – 5 min | 0.032% – 0.073% | **unreachable at any accuracy** |
| 15 min | 0.125% | 82.0% |
| 1 hour | 0.237% | 66.9% |
| 4 hours | 0.462% | 58.7% |
| **1 day** | **1.425%** | **52.8%** |
| **3 days** | **2.643%** | **51.5%** |

> **DIR-1 asks one question: does any declared feature predict the SIGN of the 1-day or 3-day
> return with out-of-sample accuracy exceeding 52.8% / 51.5% respectively?**

At φ = 0.25 — a more pessimistic capture assumption — the bars are **55.6%** and **53.0%**.
Both φ values are reported for every cell. **φ = 0.5 is the primary** because it is what the
MEASURE-1 table headlines; φ = 0.25 is reported so the result cannot be read as more robust
than it is.

**What this is not.** No strategy, no sizing, no P&L, no Sharpe, no live order. A feature that
clears the bar has earned a second experiment, not a position.

## 2. Why this experiment and why now

Two of Genesis's three candidate directions are closed, both with evidence:

- **Market making: closed.** Spread 0.00154 bps against 5.19 bps of cost; a 0% maker fee does
  not rescue it ([`../research/cost-model-and-the-two-questions.md`](../research/cost-model-and-the-two-questions.md)).
- **Carry: positive but not worth doing.** +19.88 bps per 14-day round trip, ≈2.6–4.3%
  annualised on deployed capital, against a 4–5% risk-free rate
  ([`../research/carry-1-result.md`](../research/carry-1-result.md)).

Direction at 1-day-plus is what remains, and MEASURE-1's P12 pointed there independently
before either closure.

## 3. The model class is declared, and it is linear

**Ordinary least squares and logistic regression only. No gradient boosting, no random
forests, no neural networks, no ensembles.**

This is not conservatism, it is an imported finding. Pindza (2026), *Frontiers in Blockchain*,
on 3.4 million minute-level crypto observations under purged walk-forward validation:

> **LightGBM: −10.94% out-of-sample R². Linear OLS: +1.23%.**

A negative out-of-sample R² means the model is worse than predicting the mean. With 3.4 million
observations and explicit leakage controls. At this signal-to-noise ratio, flexible models are
a documented way to lose, and Genesis will not spend its first directional experiment
rediscovering that.

**A non-linear model requires a separate declaration, and may only be declared after a linear
model has cleared the bar.**

---

## 4. Data

**Primary: `~/genesis-evidence/market-data/`** — 3,983,271 one-minute BTCUSDT bars, 91 monthly
files, 2019-01 → 2026-07. Columns: open time, OHLC, base volume, close time, quote volume,
trade count.

**Secondary: the CARRY-1 archive** — 7,604 funding settlements and 8-hourly spot and perp
closes, 2019-09 → 2026-08, SHA-256 of the funding payload `eb63d8425e36c4e4…`.

**Not q5.** q5 is frozen to COND-1 and, at seven days, contains about seven daily observations.
It cannot support a daily-horizon experiment and is not used.

### 4.1 What is deliberately absent, and why

**VPIN is not a feature in DIR-1**, despite being the most promising candidate from the
prior-art survey (Kitvanitphasu et al. 2026, RIBAF 81:103163, where it predicts price jumps).

VPIN requires the buy/sell split of volume. **The archived minute bars do not carry taker-buy
volume** — they have total volume and a trade count, and nothing that separates aggressor
side. q5 does carry aggressor side, but only for seven days.

Computing VPIN over this history requires downloading Binance's historical aggTrade dumps, at a
scale not available tonight. **It is recorded here as the leading feature for the next
declaration, not smuggled into this one as a proxy.** A "VPIN-like" feature built from trade
counts would be a different quantity wearing VPIN's name.

---

## 5. The features, fixed in advance

All are computed **only from information available at the decision timestamp.** Each is
standardised on a trailing window that also ends at the decision timestamp.

| | Feature | Rationale | Source |
|---|---|---|---|
| **F1** | **Funding rate**, level and trailing z-score | Positioning and crowding. Persistently high funding means crowded longs. This is the one feature that is not derivable from price. | CARRY-1 archive |
| **F2** | **Basis**, `(perp − spot)/spot`, level and z-score | Leveraged demand relative to spot | CARRY-1 archive |
| **F3** | **Realised volatility**, HAR-RV form (1d, 5d, 22d components) | Corsi (2009). The volatility holon already implements this. | minute bars |
| **F4** | **Momentum**, trailing returns at 1d, 7d, 30d | The most documented and most crowded effect here | minute bars |
| **F5** | **Mean trade size**, `volume / trade_count`, z-scored | Composition proxy — the closest observable to "is this retail or institutional flow" that the archive supports. **It is not VPIN and is not order-flow imbalance**, and no result may describe it as either. | minute bars |
| **F6** | **All five combined**, one linear model | Whether the features add to each other | all |

**Family DIR-1 = 6 feature sets × 2 horizons = 12 declared trials.** Fixed by this table,
unable to grow.

**Correction:** Benjamini–Hochberg at q = 0.05 across all 12, with Bonferroni α = 0.05/12 =
0.004167 reported alongside. In addition, because the headline will be *"the best cell"*, the
**expected best-of-12 accuracy under zero skill** is computed and reported beside the observed
best (`ledger.expected_max_sharpe` and the deflated form). A best cell that does not exceed its
own zero-skill expectation is reported as **noise**, whatever its p-value.

---

## 6. Protocol

### 6.1 Out-of-sample is by time, always
**Purged walk-forward with an embargo.** Train on a trailing window, predict forward, roll.
The embargo is **one full horizon** — 1 day or 3 days — removed between train and test, so a
label overlapping the training window cannot leak into the test.

**No random splits, no k-fold, no shuffling.** Time-series data shuffled is a leakage machine,
and the leakage inflates accuracy in exactly the range this experiment is trying to resolve.

### 6.2 Windows
Train 730 days, test 90 days, roll by 90 days. First test window begins 2021-09, giving
approximately **20 non-overlapping test windows** across 2021–2026 and covering a bull market,
a bear market and two chop regimes.

### 6.3 The reported statistic
**Directional accuracy on pooled out-of-sample predictions**, with a moving-block bootstrap
95% interval (block = one horizon). Per-window accuracy is reported as a series so that a
result driven by one regime is visible rather than averaged away.

### 6.4 Costs are not re-derived
The bar comes from MEASURE-1 and is fixed. DIR-1 does not recompute costs, does not choose φ
after seeing accuracy, and does not adjust the horizon set.

---

## 7. Predictions, recorded before the data

- **D1.** No single feature clears 52.8% out-of-sample at 1 day.
- **D2.** F4 (momentum) is the weakest performer at 1 day, at or below 50%. It is the most
  crowded effect in the most liquid crypto asset.
- **D3.** F1 (funding) is the **best single feature** at both horizons, because it is the only
  one carrying positioning rather than price.
- **D4.** F6 (combined) beats every single feature in-sample and **fails to beat F1
  out-of-sample.** Five correlated features on a weak signal is where overfitting lives.
- **D5.** Per-window accuracy has a standard deviation across the ~20 windows **exceeding** the
  distance between the pooled result and 50%. Stated plainly: **the regime-to-regime variation
  is larger than the effect.**
- **D6.** The 3-day horizon clears its lower bar (51.5%) in at least one cell where the 1-day
  horizon does not clear 52.8%.

**My honest expectation is that D1 holds and DIR-1 returns negative.** It is written down so
that a negative result is a scored prediction rather than a disappointment.

## 8. Kill conditions, declared before the data

- **K1.** Any test window with fewer than 30 predictions is excluded and the exclusion recorded.
- **K2.** If **no** cell exceeds its bar out-of-sample, **DIR-1 reports directional prediction
  at reachable horizons as CLOSED for this feature set.** That is a result. It does not license
  adding features, changing horizons, trying another model class, or moving to another symbol.
  Each requires a new declaration.
- **K3.** If a cell clears its bar but its observed accuracy does not exceed the **expected
  best-of-12 under zero skill**, it is reported as **noise** and not as a finding.
- **K4.** If D5 holds — regime variation exceeds the effect — then **no cell may be reported as
  tradeable**, whatever its pooled accuracy. A pooled edge smaller than its own regime
  dispersion is a statement about the sample, not about the market.
- **K5.** If any feature is found to use information unavailable at the decision timestamp, the
  entire run is **void** and re-declared. Leakage is not repaired in place.

## 9. Known limitations, stated before results

**One symbol.** BTCUSDT. Pindza (2026) found **no cross-asset transfer** in crypto
microstructure models, so nothing here may be extrapolated to another asset — and Genesis's own
cross-section holon measured effective breadth 1.03 across 25 instruments, which is the same
finding by another route.

**Funding and basis are 8-hourly**; minute-derived features are aligned to those boundaries, so
the effective decision frequency is 8-hourly regardless of horizon.

**Survivorship and regime.** 2019–2026 on BTC contains two full cycles and one exchange
landscape. It is not a general claim about crypto.

**The bar assumes passive execution.** The 52.8% figure uses futures maker fees, so it assumes
Genesis captures the 1.81 bps execution saving EXEC-1 measured. If fills are aggressive the bar
rises to the taker column and no result here survives it.

## 10. Out of scope

No sizing, no leverage, no portfolio construction, no live order, no agent, no non-linear
model. DIR-1 answers whether a linear function of five observable quantities beats a measured
threshold out of sample. Everything downstream of that answer requires machinery that does not
yet exist and a contract that has not been written.
