# ECON-1 — is the signal worth money, and does it beat simply holding?

**Status: FROZEN 2026-08-19, before any forward observation exists.** No endpoint, benchmark,
control, threshold, prediction or kill condition below may be changed after this point. If a
defect is found it is reported and recorded, not silently repaired.

**Classification: BUILD. No novelty claimed.**

---

## 1. Why this contract exists, stated against my own interest

DIR-1 and DIR-2 declared **directional accuracy** as their endpoint and both returned negative
against a break-even hit rate imported from MEASURE-1.

On 2026-08-19, prompted by an outside reader, I computed a different statistic on DIR-2's
predictions: **the actual return earned**, rather than the fraction of correct calls. The
result was six times larger than the accuracy proxy implied.

**That computation is exploratory and is not evidence.** It was performed after the declared
endpoint failed, on the data that produced the failure, and choosing a better-looking statistic
afterwards is exactly the forking path five frozen contracts exist to prevent. It is recorded
in full in §7 so that nobody, including me, can later present it as a result.

What it did establish is a **methodological defect**, and that is what this contract repairs:

> **MEASURE-1's break-even formula `p* = 0.5 + c/(2φm)` uses the MEDIAN absolute move.
> Expected P&L is driven by the MEAN. On a fat-tailed asset those differ by ~45%, and the
> formula asks a median question of a mean-shaped payoff.**

Every bar in this project inherits that. ECON-1 stops using the proxy and measures the thing
itself.

## 2. The question

> **Does the DIR-2 feature set, traded forward, produce a positive expected net return per
> trade AFTER costs — and does it beat simply holding the asset over the same periods?**

The second half is not decoration. DIR-2's predictions were **70.98% long** across a sample in
which BTC rose roughly sixfold. A long-biased signal in a bull market earns money without
containing any information at all.

**Beating a coin flip is not the bar. Beating buy-and-hold is.**

## 3. Data — forward only

**There is no clean held-out slice, and this contract does not pretend otherwise.** DIR-2's
walk-forward consumed the entire metrics archive, 2020-09 → 2026-08-17. Any in-sample re-read
at a new endpoint is contaminated by §1.

**ECON-1 is therefore a forward test.** It is evaluated only on decision points at or after
**2026-08-20T00:00:00Z**, which did not exist when this contract was frozen.

- **Features and model:** identical to DIR-2 — `taker_z, oi_z, doi_z, toptrader_z, crowd_z`,
  OLS on the forward return, sign of the fit. Frozen; no refitting of the specification.
- **Training:** the trailing 730 days at each decision point, rolling forward, exactly as
  DIR-2. The model may re-estimate its coefficients on new data; it may not change its form.
- **Source:** Binance published USD-M metrics, extended daily.
- **Horizon:** 1 day primary, 3 days secondary and non-substitutable.

**This is slow by construction.** §6 sets the earliest honest read.

## 4. The endpoint, the benchmarks, and the controls

### 4.1 Primary endpoint
**Mean net return per trade, in bps**, after the full cost stack:

```
net = sign(prediction) × forward_return − fees − 2×adverse_selection + spread_capture
```

Costs are taken from [`feemap.py`](feemap.py) at the venue declared at run time, and adverse
selection from the horizon study in `market/evidence/as-horizon.json` **at the matching
horizon**. If that study is unfinished when ECON-1 first reads, the read is **deferred**, not
run with a placeholder.

Reported alongside, and non-substitutable: median net, standard deviation, per-trade Sharpe,
worst trade, and the full decile distribution of net returns.

### 4.2 Three benchmarks, all declared
- **B1 — zero.** Net return per trade > 0.
- **B2 — buy-and-hold.** Mean net return must exceed the mean return of holding the asset over
  the same decision points, **after applying the same cost stack to a single entry and exit**.
- **B3 — sign permutation.** The same predictions with signs randomly permuted, 10,000 draws.
  The observed net must exceed the **95th percentile** of that null. This directly tests
  whether the *timing* carries information, independent of net exposure.

**A result must clear all three.** Clearing B1 alone is what a long-biased signal does in a
rising market.

### 4.3 Controls, reported every time
- **Net exposure** — the fraction of predictions that are long. If it exceeds 0.60 or falls
  below 0.40, the result is reported as **directionally biased** and B2/B3 become the only
  admissible evidence.
- **De-drifted return** — `sign(prediction) × (return − sample mean return)`.
- **Day-of-week.** Liu, Bao, Han & Li (2025), *Finance Research Letters* 85(D):108187, find
  bid-ask spread, volume and volatility follow an inverted-U within the week, spread **peaking
  Wednesday** and falling into the weekend. Net return is therefore **reported by day of
  week**, as a declared reporting dimension and **not** as a search dimension. No cell may be
  selected on it.

## 5. Predictions, recorded before any forward data exists

- **F1.** B1 is cleared: mean net return per trade is positive.
- **F2.** **B2 is NOT cleared** — the strategy fails to beat buy-and-hold. This is my genuine
  expectation, and it is the prediction I most want to be wrong about.
- **F3.** Net exposure stays above 0.60, so the directionally-biased flag fires.
- **F4.** B3 is not cleared: sign-permuted nulls reach the observed net more than 5% of the
  time, because the effect is small relative to per-trade dispersion (measured at 303.7 bps
  in §7).
- **F5.** Day-of-week net return varies more than the pooled effect, mirroring the regime
  dispersion K4 has flagged in every prior experiment.

## 6. Kill conditions

- **K1.** No read before **270 completed 1-day trades** (approximately 90 days at three
  decisions per day). Earlier looks are not permitted, and no interim result may be quoted.
- **K2.** If B2 fails at the first admissible read, **ECON-1 reports the signal as not worth
  trading** and the directional programme is closed. It does not license new features, another
  venue, or another horizon.
- **K3.** If the directionally-biased flag fires and B3 fails, the result is reported as
  **exposure, not information** — whatever B1 says.
- **K4.** If the adverse-selection horizon study returns a value that makes the cost stack
  exceed the measured gross at every venue in the fee map, ECON-1 is **void before it starts**
  and reported as such.
- **K5.** Any change to the feature set, model form, or cost stack voids the run. The whole
  point is that the specification was fixed before the data existed.

## 7. The exploratory numbers, recorded so they cannot be laundered

Computed 2026-08-19 on DIR-2's in-sample walk-forward predictions, **after** the declared
endpoint failed. **Not evidence. Not a result. Recorded only to prevent later re-discovery
being presented as new.**

| | 1 day |
|---|---|
| n | 4,880 |
| accuracy | 0.5242 |
| gross mean | +21.33 bps |
| gross median | +9.04 bps |
| p*-formula implied gross | +3.45 bps |
| \|move\| when right / wrong | 217.2 / 194.4 bps (ratio 1.117) |
| **fraction long** | **0.7098** |
| unconditional 1-day drift | +9.15 bps |
| always-long over same points | +9.15 bps |
| **signal minus always-long** | **+12.18 bps** |
| per-trade SD | 303.7 bps |
| per-trade Sharpe | 0.070 |
| t-stat, ~1,626 effective trades | 2.83 |
| windows positive | 14 of 20, worst −186.3 bps |

**Read honestly:** the signal is 71% long in a sample where the asset rose sixfold, and a large
part of the gross is directional bias meeting drift rather than information. The excess over
always-long is +12.18 bps and is not clearly separable from carrying more exposure. That is why
B2 and B3 exist.

## 8. Known limitations

**Forward tests are slow and this one is slower than it looks.** At a per-trade Sharpe of 0.070
and 303.7 bps of dispersion, 270 trades gives a standard error of roughly 18 bps on a mean of
~21. The first read will be **suggestive at best**. A conclusive read needs closer to a year.
That is the true cost of an effect this thin, and it is stated here rather than discovered in
three months.

**Overlapping positions.** Decisions are 8-hourly and the horizon is 1 day, so consecutive
trades overlap. Intervals use a moving-block bootstrap with block ≥ the horizon, as everywhere
else in this project.

**One asset, one venue, one model form.** No claim beyond BTCUSDT.

**Liquidity commonality.** Liu et al. (2025) find a coin's liquidity co-moves with market-wide
liquidity, most betas near 1. **This is evidence against the assumption that moving to a
different asset would diversify liquidity or cost risk**, and it is recorded here because that
move is the obvious next idea if ECON-1 fails. It should not be made on the assumption that
another coin's costs are independent of this one's.

## 9. Out of scope

No sizing, no leverage, no portfolio construction, no live order, no agent, no change of model
class. ECON-1 asks whether a frozen specification, traded forward, makes money after costs and
beats holding. Nothing else.
