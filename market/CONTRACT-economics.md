# ECON-1 — is the signal worth money, and does it beat simply holding?

**Status: FROZEN 2026-08-19, before any forward observation exists.** No endpoint, benchmark,
control, threshold, prediction or kill condition below may be changed after this point. If a
defect is found it is reported and recorded, not silently repaired.

**Classification: BUILD. No novelty claimed.**

> ## AMENDMENT 1 — 2026-08-19, before any forward observation exists
>
> **What changed:** a fourth benchmark (B4, exposure-matched) and a declared forward
> decomposition (§4.4) were added. Nothing was removed, relaxed, or reworded in a way that
> makes the test easier.
>
> **Why this is legitimate, stated so it can be judged rather than assumed.** ECON-1 evaluates
> only decision points at or after 2026-08-20. **No observation in its evaluation set exists
> yet.** The contract is being amended pre-data, and every change makes the test *stricter*.
>
> **Why it is nonetheless not innocent.** The amendment was prompted by exploratory work on
> DIR-2's in-sample data (§7), so it is not made blind. The mitigating fact is direction:
> adding harder controls after seeing encouraging exploratory numbers biases **against** a
> positive result, which is the safe way to be contaminated. Had the amendment loosened
> anything, it would be void.
>
> **The defect it repairs.** B2 compares against buy-and-hold at 100% exposure. The strategy's
> measured **net exposure is 0.4197** — it is long 71% of the time and short the rest, so it
> carries roughly **2.4× less** directional exposure than the benchmark it was being asked to
> beat. In a rising market that is the wrong comparison in both directions at once: too hard on
> return, too easy on risk. Found by an outside reader.

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

### 4.2 Four benchmarks, all declared
- **B1 — zero.** Net return per trade > 0.
- **B2 — buy-and-hold.** Mean net return must exceed the mean return of holding the asset over
  the same decision points, **after applying the same cost stack to a single entry and exit**.
- **B3 — sign permutation.** The same predictions with signs randomly permuted, 10,000 draws.
  The observed net must exceed the **95th percentile** of that null. Permutation preserves the
  count of longs and shorts exactly, so net exposure is held fixed and only the **timing** is
  destroyed. This is the test of whether *when* the signal fires carries information.
- **B4 — exposure-matched constant position** *(Amendment 1)*. A static position equal to the
  strategy's realised **net exposure** over the same decision points, under the same cost
  stack. The strategy must beat it.

  **This is the primary passive benchmark, not B2.** Measured net exposure in the exploratory
  sample was **0.4197** — long 71% of the time, short the rest. Buy-and-hold carries 2.4× that
  directional exposure, so B2 alone asks whether the strategy beats something taking far more
  risk. B4 asks the question that matters: **does the timing add anything over simply holding
  the same average exposure?**

**A result must clear all four.** Clearing B1 alone is what a long-biased signal does in a
rising market.

### 4.3 Controls, reported every time
- **Net exposure** — the fraction of predictions that are long. If it exceeds 0.60 or falls
  below 0.40, the result is reported as **directionally biased** and B3/B4 become the only
  admissible evidence. *(B2 was named here before Amendment 1; buy-and-hold is not
  exposure-matched and cannot adjudicate a biased result.)*
- **De-drifted return** — `sign(prediction) × (return − sample mean return)`.
- **Day-of-week.** Liu, Bao, Han & Li (2025), *Finance Research Letters* 85(D):108187, find
  bid-ask spread, volume and volatility follow an inverted-U within the week, spread **peaking
  Wednesday** and falling into the weekend. Net return is therefore **reported by day of
  week**, as a declared reporting dimension and **not** as a search dimension. No cell may be
  selected on it.

### 4.4 Declared forward decomposition *(Amendment 1)*

Reported on the forward sample, **declared here so it cannot be run as a retrospective search.**
An outside reader proposed roughly ten slices of the in-sample data — by magnitude quintile,
volatility quintile, confidence, long versus short, and so on. **Run retrospectively on DIR-2's
data that is a ten-fork fishing expedition**, and it is the precise failure §1 exists to
prevent. Declared in advance and reported forward, the same slices are legitimate.

Fixed, and unable to grow: net return **by magnitude quintile of the realised move**, **by
realised-volatility quintile**, and **split long versus short**. Reported for description only.
**No cell may be selected on, and no benchmark may be evaluated within a cell.**

### 4.5 The magnitude hypothesis, declared not concluded *(Amendment 1)*

Exploratory work found the signal is correct more often on **large** moves: mean |move| of
217.2 bps when right against 194.4 when wrong, ratio **1.1170**. A label permutation preserving
the hit count gives a null of mean 1.0007 and p99 1.0755, so **p = 0.0002**.

That is a real asymmetry in the in-sample data, and it suggests the signal may be doing
**conditional magnitude** rather than pure direction — which would matter, because P&L is
magnitude-weighted while accuracy is not.

**It is a hypothesis, not a finding**, for the same reason everything in §7 is: it was computed
after the declared endpoint failed, on the data that produced the failure. It is scored forward
as prediction F6 and nowhere else.

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
- **F6** *(Amendment 1)*. The magnitude asymmetry of §4.5 **persists forward**: mean |move|
  when correct exceeds mean |move| when wrong by more than 5%. I expect this one to hold, and
  it is the only prediction in this contract I expect to hold.
- **F7** *(Amendment 1)*. **B4 is not cleared** — the strategy fails to beat a constant position
  at its own net exposure. If F2 and F7 both hold, the signal's apparent return is exposure
  rather than information, and K3 applies.

## 6. Kill conditions

- **K1.** No read before **270 completed 1-day trades** (approximately 90 days at three
  decisions per day). Earlier looks are not permitted, and no interim result may be quoted.
- **K2.** If B2 fails at the first admissible read, **ECON-1 reports the signal as not worth
  trading** and the directional programme is closed. It does not license new features, another
  venue, or another horizon.
- **K3.** If the directionally-biased flag fires and **either B3 or B4** fails, the result is
  reported as **exposure, not information** — whatever B1 says. *(B4 added by Amendment 1.)*
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
