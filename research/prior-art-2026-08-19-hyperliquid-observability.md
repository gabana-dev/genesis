# Hyperliquid is not "cheap but blind" — it is blind in one dimension and transparent in a way Binance can never be

**Date:** 2026-08-19
**Classification: IMPORT. Nothing adopted into a frozen contract.**

Three papers found by targeted search. Together they invert a conclusion I reached yesterday.

---

## 1. Bysik & Ślepaczuk (2026), arXiv:2606.00060 — independent confirmation of Genesis's central finding

*Machine Learning-Based Bitcoin Trading Under Transaction Costs: Evidence From Walk-Forward
Forecasting.* Hourly BTC, 2018–2025, ~70,000 observations, **10 bps all-in cost** (fees, spread
crossing, slippage).

| naive sign-based XGBoost | annualised | Sharpe |
|---|---|---|
| **without costs** | **+73.50%** | 1.27 |
| **with 10 bps costs** | **−64.00%** | −1.25 |

**A 137-point swing from a 10 bps cost.** Their conclusion: *"the main obstacle in hourly
cryptocurrency trading is not only weak predictability, but also the way forecasts are converted
into trades."*

That is Genesis's central finding, reached independently on different data with a different
method. **Costs, not prediction, are the binding constraint.** It is now the third source
saying so, after Pindza (2026) and Genesis's own cost model.

**Their positive result deserves the scepticism the negative one does not.** Cost-aware
filtering restores +65.4% at Sharpe 1.09 — by cutting trades from **10,619 to 251**. That is
2.4% coverage and about 36 trades a year over seven years. It is the same selective-trading
claim as the Kuznetsov papers, and it must meet the six requirements in
[`prior-art-confidence-thresholds.md`](prior-art-confidence-thresholds.md) §3 before it means
anything. XGBoost is also the model class Pindza measured at **−10.94% out-of-sample R²**.

**What is worth taking:** their filter is a **forecast-magnitude threshold** — suppress weak
signals. That is the same mechanism as Genesis's F6 finding, arrived at independently: the
signal is right more often on large moves (ratio 1.1170, p = 0.0002). Two routes to the same
place is worth noting, and F6 is already declared forward in ECON-1.

## 2. Barone & Lillo (2026), arXiv:2606.15715 — Hyperliquid publishes announced flow

*Trading in the Sunshine or in the Shade: Market Impact and Adverse Selection on Hyperliquid.*
**4.3 million hidden metaorders against 465,000 visible TWAP executions.** Fabrizio Lillo is a
serious microstructure researcher; this is not a parameter sweep.

Findings:

- **Visible TWAPs face lower execution costs and leave smaller permanent impact** than
  comparable hidden metaorders.
- **Hidden metaorders running alongside already-visible same-direction TWAP flow incur higher
  permanent costs** — adverse selection shifts onto the non-announcers.
- While a visible TWAP is active, **displayed depth rises and the book tilts toward the
  absorbing side**, more so for larger announced orders.

**The fact that matters most is structural, not statistical: Hyperliquid has publicly visible
TWAP orders.** Institutional execution schedules are *announced*, not inferred.

Genesis spent effort on inferring execution footprints — the FFT idea, taker-order
reconstruction, iceberg detection. On this venue a large class of that flow does not need
inferring. It is published.

And the second finding is a directly usable **cost-conditioning variable**: trading in the same
direction as an active visible TWAP is measurably more expensive. That is a state Genesis could
observe and avoid.

## 3. Zhai (2026), arXiv:2608.04373 — trader informativeness is persistent and public

*Public Trader Identity: Adverse Selection and Return Predictability.*

Scores wallets by **notional-weighted 10-second markout** of their aggressive orders over a
frozen window, requiring ≥100 qualifying orders.

- **Rank correlation 0.52 across adjacent ten-day windows.** Informativeness is a persistent
  *wallet attribute*, not a transient state.
- Top-decile wallets: **+2.20 bps** markout. Bottom decile: **−1.13 bps**.
- Adding toxic-wallet features raises one-second R² by **13.2% (t = 9.2)**, 10.88% → 12.31%.
- A matched-wallet placebo confirms the effect is **toxicity, not size or activity** — the toxic
  cohort's increment was 1.6× the largest matched draw.

**This is only possible where orders carry identity.** On an on-chain order book every order is
attributable to a wallet, and history is public. **On Binance it is impossible** — the trade
stream carries no account information, which is exactly why DIR-1's fee-tier conditioner had to
be discarded as unobservable.

---

## 4. The inversion

Yesterday I wrote that Hyperliquid was **cheap but experimentally blind**, because its `l2Book`
published ~0.2 updates/second against Binance's ~3.7, and concluded that EXEC-1's methods would
not transfer.

That is true, and it is only half the picture. **Hyperliquid is blind in one dimension and
radically more transparent in another.**

| | Binance | Hyperliquid |
|---|---|---|
| book update rate | ~3.7/s | **~0.2/s** (probe, unconfirmed) |
| round-trip cost | 4.00 bps | **3.00 bps** |
| spread captured passively | 0.0015 bps | **0.1554 bps** |
| **order-level identity** | **none** | **every order, on-chain** |
| **announced institutional flow** | none | **visible TWAPs** |

Binance is better for **book microstructure**. Hyperliquid is better for **participant
attribution** — and participant attribution is precisely what T2.1 (forced versus informed flow)
has been blocked on.

**The venue trade-off is not cost against observability. It is one kind of observability against
another**, and Genesis chose the axis before knowing the other existed.

## 5. What this changes, and what it does not

**Does not change:** ECON-1 is frozen, forward-running, and priced at Hyperliquid tier 0. None
of this enters it. COND-1 is frozen against q5 and is a Binance experiment. Both stand.

**Does change the map:**

- **T2.1 (flow attribution) has a better home than Binance.** The plan was to infer forced flow
  from trade-stream signatures and validate against the sampled `forceOrder` feed. On
  Hyperliquid, wallet identity is public and Zhai's method is replicable — informativeness
  measured directly rather than inferred, with a published persistence figure to check against.
- **Task #22 (re-probe the book) drops in priority further.** It settles whether EXEC-1-style
  microstructure transfers. But the reason to be on Hyperliquid may not be microstructure at
  all.
- **A new question, unasked until now:** does Zhai's wallet-toxicity ranking replicate on
  Hyperliquid, and does it survive at horizons Genesis can reach? Zhai measures **one-second**
  R². Genesis's floor is 291 ms and its reachable region is one day. A signal with a
  one-second half-life is not available to us, and that must be established before anything is
  built on it.

**The honest caution.** Every number above is from a paper Genesis has not replicated. The
pattern of this project has been that imported numbers do not survive contact with our own
measurement — the 60-second adverse-selection figure did not extrapolate, the accuracy bar was
the wrong statistic, and the fill simulator could not see size. **These are leads, not facts.**
