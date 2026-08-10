# MEASURE-1 — the cost of being right

**Status: DRAFT — not frozen, not authorized, no code written.**
**Classification: IMPORT — every method below is established and cited. Nothing is claimed as
novel. What is ours is the specific measurement of *our* costs against *our* horizons from
*our* location.**

Phase 2 of the market direction: **measure the environment, do not trade it.**
No orders, no paper trading, no strategy, no profitability analysis.

---

## 1. The question

> At what horizon does a correct prediction pay for itself?

Every strategy Genesis could ever run must clear the same bar: the move it predicts has to be
larger than the cost of acting on it. That bar is arithmetic and it can be measured **before**
any signal exists. If the answer is "no horizon," the market direction closes here, cheaply,
having spent days rather than months.

This is deliberately the first Phase 2 measurement because it is the one that can **close the
design space**. Latency already closed everything below a minute. This asks whether cost
closes everything below a day.

## 2. The headline statistic — break-even hit rate

For a directional decision that risks and captures a comparable magnitude `m`, with round-trip
cost `c` and hit rate `p`:

```
E[profit per trade] = m·(2p − 1) − c
break-even hit rate  p* = 1/2 + c / (2m)
```

`p*` is the deliverable. One table, horizons down the side, fee tiers across, and it tells us
what accuracy the project would need in order to be worth continuing.

**Stated plainly because it will otherwise be over-read:** this assumes symmetric win/loss
magnitude and full capture of the move. Real strategies are asymmetric and capture a fraction.
It is a **first-order screen, not a strategy model** — it is right about which horizons are
hopeless and only approximate about the rest. A capture-fraction sensitivity (100%, 50%, 25%)
is reported alongside, because a strategy capturing half the move faces the `p*` of a horizon
with half the magnitude.

## 3. A correction to our own constraint table, before we start

`ai/current_focus.md` records round-trip cost as 0.20% spot / 0.10% futures taker / 0.04%
futures maker. **Those are fees only.** Real round-trip cost is:

```
c = fees + spread crossed + market impact at size
```

The constraint table therefore *understates* cost, and every conclusion drawn from it so far is
optimistic by an unmeasured margin. Measuring the other two terms is part of this contract.

**The fee tier is a strategic decision, not an accounting detail.** Moving from futures taker
(0.10% round trip) to futures maker (0.04% round trip) cuts `c` by 60% — which reduces the
required hit rate by more than any realistic signal improvement plausibly could. If that holds
under measurement, *how we execute matters more than what we predict*, and the project's effort
should be allocated accordingly.

**The counterweight, which must be measured and not assumed:** maker fills are adversely
selected. A resting bid fills when someone is willing to sell into it — disproportionately when
the price is about to fall. This is the maker's curse, and it means the fee discount is partly
paid back in fill quality. **The size of that payback is exactly what the fill/execution
simulator exists to determine**, and it is the largest unbuilt component of the project. This
contract measures what can be measured without it, and marks the boundary explicitly.

## 4. Measurements

Each names its established method. None is a Genesis invention.

| # | Measurement | Method | Why |
|---|---|---|---|
| **A** | Median and quartiles of \|return\| at 1m, 5m, 15m, 1h, 4h, 1d, 3d | direct, on log returns | the `m` in `p*` |
| **B** | Break-even hit-rate table | §2, with capture sensitivity | the deliverable |
| **C** | Observed spread distribution | time-weighted best bid/ask from our own recordings | the second cost term |
| **D** | Slippage at size — walk the recorded book for 1k, 10k, 50k, 100k USD | direct book-walk on recorded depth | the third cost term. **Arithmetic on observed depth, not a simulation.** |
| **E** | Square-root impact check: is measured D consistent with `impact ≈ Y·σ·√(Q/V)`? | Almgren et al. 2005; Tóth et al. 2011 | lets us extrapolate to sizes we never recorded |
| **F** | Variance ratio at each horizon, with the heteroskedasticity-robust statistic | Lo & MacKinlay 1988 | the canonical test for whether returns are a random walk at horizon *h*. VR ≈ 1 everywhere means no linear predictability exists to find |
| **G** | Realized-volatility signature plot across sampling frequencies | Andersen, Bollerslev, Diebold & Labys 2000 | finds the frequency below which microstructure noise dominates the signal. Below it, *nothing measured is real* |
| **H** | Roll effective spread from serial covariance of price changes | Roll 1984 | cross-checks C, and identifies how much short-horizon negative autocorrelation is bid-ask bounce rather than predictability |
| **I** | Amihud illiquidity, \|return\| per unit dollar volume, by hour | Amihud 2002 | when the market is cheap to move through, and when it is not |
| **J** | Volatility and volume by hour-of-day and day-of-week | direct | crypto trades 24/7 but is not uniform; sessions matter |

**G and H exist to protect us from ourselves.** We *will* find negative autocorrelation at 1m.
It will be bid-ask bounce. Pre-registering that expectation is what stops it being reported as
a discovery — the exact failure this project has already made six times in a different costume.

## 5. Pre-registered expectations

Written before any computation, so the result cannot be quietly reinterpreted.

| Claim | Prediction |
|---|---|
| Median \|1d return\| | 1.2%–2.0% |
| Median \|1h return\| | 0.25%–0.45% |
| Median \|1m return\| | 0.03%–0.08% |
| `p*` at 1h, spot taker | **> 70% — hopeless** |
| `p*` at 1h, futures maker | 58%–65% — hard, not absurd |
| `p*` at 1d, futures maker | **52%–55% — the only genuinely reachable region** |
| Variance ratio | ≈ 1 at every horizon ≥ 1h; no linear predictability |
| Short-horizon autocorrelation | negative at 1m, and **explained by Roll spread, not signal** |
| Signature plot | noise dominates below ~1–5 minutes |
| BTCUSDT spread | ~1 tick, ~0.001% — negligible beside fees |
| Slippage at 10k USD | < 0.01% — BTCUSDT is deep enough that our size is invisible |

**The prediction that matters: cost, not depth, is our binding constraint.** We are small
enough that the market does not notice us, and that means fees and horizon decide everything.
If this is right, the project's target is **1-day-and-longer horizons, executed as a maker**,
and every shorter idea is closed on arithmetic — the same way latency closed sub-minute.

## 6. Data

| | |
|---|---|
| Returns (A, B, F, G, I, J) | Binance public klines, BTCUSDT, 2019-01-01 → present, 1m native, aggregated upward. Public REST, no credentials, read-only. |
| Spread and depth (C, D, E, H) | **our own BAV-1 recordings** — 3 hours, hash-chain verified, `~/genesis-evidence/bav-1/` |
| Fees | Binance published schedule, recorded with retrieval date |

**The depth data is three hours of one symbol.** Everything derived from it (C, D, E, H) is
correspondingly weak and must be reported as indicative, not established. Extending it is a
recording job the instrument can already do — and is the natural follow-on if C/D/E turn out
to matter.

Aggregation from 1m klines is treated as a data fact to verify, not assume: kline timestamps
are interval-**opening** on Binance. Treating them as closing would leak a minute of future
into every return, which is the same class of error caught in RDB-1 §2.

## 7. Analysis discipline

- Every point estimate carries an interval. Returns are serially dependent and heteroskedastic,
  so intervals come from a **moving-block bootstrap**, not an IID one.
- Results are reported **by year as well as pooled**. A statistic pooled over 2019–2026 hides
  that the market changed; if the answer is unstable across years it is not an answer.
- The full period is used. **No holdout is defined here** — this contract fits nothing and
  predicts nothing, so there is nothing to overfit. A holdout becomes mandatory the moment a
  hypothesis search begins, which is Phase 5.
- Raw outputs are reported **before** interpretation, in the order above.

## 8. What this cannot establish

- **Nothing about whether an edge exists.** A reachable `p*` is a necessary condition, never a
  sufficient one. "The bar is 53%" does not imply anyone can clear it.
- **Nothing about fills.** Every slippage figure assumes the recorded book is available to us
  at the recorded moment — it is not, by ~291 ms. Closing that gap needs the fill simulator.
- **Nothing about adverse selection**, the single largest unmeasured term. See §3.
- **One symbol, one venue.** BTCUSDT is the deepest crypto market in existence. Every liquidity
  conclusion is a best case and will not transfer to a thinner instrument.
- **The past.** Volatility regimes change; a horizon affordable in 2021 may not be in 2027.

## 9. Kill condition, stated in advance

> If no horizon at any available fee tier yields `p* ≤ 60%` under the 50% capture assumption,
> the directional-prediction line closes, and the market direction is reconsidered rather than
> pursued with a smaller signal.

Recorded here so that abandoning it is a planned outcome. Per the standing kill criteria, the
observation infrastructure remains valuable even if this closes — that is not consolation, it
is the most probable honest outcome and was named as such before we started.
