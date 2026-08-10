# MEASURE-1 — the cost of being right

**Status: FROZEN 2026-08-10.** Amended by the researcher before freezing (five amendments,
§11). No measurement, threshold, definition or prediction below may be changed after this
point. If a defect is found in the contract, it is reported and recorded — not silently
repaired.

**Classification: IMPORT — every method below is established and cited. Nothing is claimed as
novel. What is ours is the specific measurement of *our* costs against *our* horizons from
*our* location.**

Phase 2 of the market direction: **measure the environment, do not trade it.**
No orders, no paper trading, no strategy code, no strategy optimisation, no profitability
analysis. The purpose of this phase is to determine whether a viable directional opportunity
exists at all.

---

## 1. Three questions, kept separate

They are separate because conflating them is how projects convince themselves they have found
something. A positive answer to Q1 is worthless without Q2, and Q1+Q2 together are still
worthless without Q3.

> **Q1 — Is there measurable directional structure?**
> Do returns depart from a random walk at any horizon, in a way that is stable across years?
>
> **Q2 — Does that structure survive realistic trading costs?**
> Given the true round-trip cost, what accuracy would be required for a decision at that
> horizon to break even?
>
> **Q3 — Can Genesis actually capture it through realistic execution?**
> Fills at our latency, at our size, with adverse selection priced in.

**MEASURE-1 answers Q1 and Q2. It does not answer Q3 and cannot.** Q3 requires the
fill/execution simulator, which does not exist and is the largest unbuilt component of the
project. Any result here that is read as an answer to Q3 is being misread. The boundary is
marked at every measurement below.

## 2. The headline statistic — break-even hit rate (Q2)

For a directional decision that risks and captures a comparable magnitude `m`, with round-trip
cost `c` and hit rate `p`:

```
E[profit per trade] = m·(2p − 1) − c
break-even hit rate  p* = 1/2 + c / (2·φ·m)        where φ is the capture fraction (§6)
```

`p*` is the deliverable. One table: horizons down the side, fee tiers across, capture fractions
as a third axis.

**Stated plainly because it will otherwise be over-read:** this assumes symmetric win/loss
magnitude. Real strategies are asymmetric. It is a **first-order screen, not a strategy
model** — reliable about which horizons are hopeless, only approximate about the rest.

## 3. A correction to our own constraint table (amendment 1)

`ai/current_focus.md` records round-trip cost as 0.20% spot / 0.10% futures taker / 0.04%
futures maker. **Those are fees only.** Real round-trip cost has three terms:

```
c = fees + spread crossed + market impact at size
```

The fee-only figure is therefore **optimistic, and must never be used as an execution cost**.
Every conclusion drawn from the constraint table to date is optimistic by an unmeasured margin.
All three terms are measured here, and every reported `c` states which terms it contains.

**The fee tier may matter more than the signal.** Moving from futures taker (0.10% round trip)
to futures maker (0.04%) cuts the fee term by 60% — potentially reducing the required hit rate
by more than any realistic signal improvement could. **This is a hypothesis to test, not a
design decision** (amendment 2), and it is tested by computing the full `p*` table across fee
tiers rather than assuming the maker column wins.

**The counterweight, which must be measured and not assumed:** maker fills are adversely
selected. A resting bid fills when someone is willing to sell into it — disproportionately when
the price is about to fall. This is the maker's curse, and it means the fee discount is partly
repaid in fill quality. **Sizing that repayment is a Q3 question.** MEASURE-1 cannot answer it,
so the maker column of the `p*` table is an **upper bound on maker attractiveness** and is
labelled as such wherever it appears.

## 4. Measurements

Each names its established method, and the question it serves.

| # | Q | Measurement | Method |
|---|---|---|---|
| **A** | Q2 | Median and quartiles of \|return\| at 1m, 5m, 15m, 1h, 4h, 1d, 3d | direct, on log returns |
| **B** | **Q2** | **Break-even hit-rate table** | §2, across fee tiers and capture fractions |
| **C** | Q2 | Observed spread distribution, time-weighted | our own recordings |
| **D** | Q2 | Slippage at size — walk the recorded book for 1k, 10k, 50k, 100k USD | direct book-walk. **Arithmetic on observed depth, not a simulation** |
| **E** | Q2 | Is D consistent with `impact ≈ Y·σ·√(Q/V)`? | Almgren et al. 2005; Tóth et al. 2011 — lets us extrapolate to unrecorded sizes |
| **F** | **Q1** | **Variance ratio at each horizon**, heteroskedasticity-robust statistic | Lo & MacKinlay 1988 — the canonical random-walk test. VR ≈ 1 everywhere means no linear predictability exists to find |
| **G** | Q1 | Realized-volatility signature plot across sampling frequencies | Andersen, Bollerslev, Diebold & Labys 2000 — finds the frequency below which microstructure noise dominates. Below it, nothing measured is real |
| **H** | Q1 | Roll effective spread from serial covariance of price changes | Roll 1984 — cross-checks C, and identifies how much short-horizon negative autocorrelation is bid-ask bounce rather than predictability |
| **I** | Q2 | Amihud illiquidity, \|return\| per unit dollar volume, by hour | Amihud 2002 |
| **J** | Q1 | Volatility and volume by hour-of-day and day-of-week | direct |

**G and H exist to protect us from ourselves (amendment 3).** We *will* find negative
autocorrelation at 1 minute. It will be bid-ask bounce. **A result matching this prediction is
a confirmation of established microstructure, not a discovery, and must not be reported as
one.** Should H fail to account for the observed short-horizon autocorrelation, that residual
is interesting — and is still not a discovery until it survives Q2 and Q3.

## 5. Pre-registered predictions — falsifiable, not assumed (amendment 2)

Written before any computation. **Each is a hypothesis this measurement is capable of refuting.
None is an architectural assumption, and none may be built upon until measured.** Each carries
its falsification criterion.

| # | Prediction | Falsified if |
|---|---|---|
| P1 | Median \|1d return\| in 1.2%–2.0% | outside the band |
| P2 | Median \|1h return\| in 0.25%–0.45% | outside the band |
| P3 | Median \|1m return\| in 0.03%–0.08% | outside the band |
| P4 | `p*` at 1h, spot taker, φ=1 exceeds 70% | ≤ 70% |
| P5 | `p*` at 1d, futures maker, φ=0.5 lies in 52%–58% | outside the band |
| P6 | VR ≈ 1 at every horizon ≥ 1h — no linear predictability | any horizon's VR interval excludes 1 in a direction stable across years |
| P7 | 1m autocorrelation is negative and **fully accounted for by Roll spread** | a residual remains after the Roll correction |
| P8 | Signature plot: noise dominates below ~1–5 minutes | the plot is flat to a finer scale |
| P9 | BTCUSDT spread ≈ 1 tick, ~0.001% — negligible beside fees | spread is a material fraction of `c` |
| P10 | Slippage at 10k USD < 0.01% — our size is invisible | ≥ 0.01% |

**P11 — the central hypothesis: cost, not depth, is our binding constraint.**
We are small enough that the market does not notice us, so fees and horizon decide everything.
**Falsified if** slippage at deployable size is comparable to or larger than the fee term
(P10 fails), in which case depth binds and the analysis must be redone around size.

**P12 — the directional hypothesis: the reachable region is 1-day-and-longer, as a maker.**
**Falsified if** a shorter horizon clears the §6 threshold, or if no horizon does, or if the
taker column clears it where the maker column does not.

**P11 and P12 are predictions to be tested, not the project's target.** No horizon and no
execution style is selected by this contract. Selection happens after measurement, in a
separate decision, and requires the measurement to have supported it.

## 6. The kill condition — definitions and rationale (amendment 4)

> **If no horizon at any available fee tier yields `p* ≤ 60%` at capture fraction φ = 0.5, the
> directional-prediction line closes and the market direction is reconsidered rather than
> pursued with a smaller signal.**

Both numbers are defined and justified here rather than assumed.

### What φ = 0.5 means

**φ is the fraction of the horizon's move that a decision actually converts into P&L.**
Formally, `realised P&L per trade ÷ m`, where `m` is the median absolute return over the
holding horizon.

- **φ = 1 is the definitional ceiling** for a rule that enters on a signal and exits exactly at
  horizon `h`: it captures the h-period return by construction.
- **φ < 1** covers everything that erodes that: exiting before the horizon, stop-losses
  triggering on adverse excursion, entry delay (≈291 ms — negligible at daily horizons, not at
  minute ones), and partial fills.
- **φ = 0.5 means half the move is converted.**

Why 0.5 for the kill evaluation: it is the conservative midpoint of the reported
{1.0, 0.5, 0.25} grid. Evaluating the kill condition at φ = 1 would be self-flattering —
it assumes perfect execution, which is exactly the Q3 assumption this contract refuses to
make. Evaluating at 0.25 would be defeatist about execution we have not yet attempted.

**One asymmetry recorded honestly:** stops reduce φ but also truncate the loss side, which
partly violates the symmetric-magnitude assumption in our favour. So φ = 0.5 is conservative in
a way that is not perfectly clean. It is a screening bar, not an accounting identity.

**φ is measurable, and this contract does not fix it permanently.** It becomes an *output* at
Phase 3/4, when a real decision meets a real cost. Until then it is a stated assumption, used
only for screening.

### Why `p* ≤ 60%`

The threshold is **not a preference for 60% accuracy.** It is an argument about what is
credibly achievable, and it runs in the negative direction:

Sustained directional hit rates above roughly 55–60% at horizons of hours to days are not
characteristic of systematic strategies at this horizon, including well-resourced ones. Most
documented profitable directional systems at daily horizons win **less** than half their
trades and profit through asymmetric payoff, not accuracy. A horizon demanding better than 60%
symmetric accuracy is therefore demanding something rarely achieved by participants with more
data, more capital and lower fees than we have. **Requiring it means the horizon is closed to
us**, and the honest response is to stop rather than to search harder.

**60% is deliberately generous.** It sits at the upper edge of that band rather than the
middle, so the condition errs toward keeping the project open. That asymmetry is intentional:
it means a *failure* is strong evidence, while a pass is weak evidence and licenses nothing
beyond continuing to Q3.

**It is still a judgment call**, and it is recorded as one. It rests on general knowledge of
systematic-strategy performance, not on a measurement Genesis owns. It is frozen so that it
cannot be relaxed after seeing an inconvenient table — which is its only real function.

## 7. Data

| | |
|---|---|
| Returns (A, B, F, G, I, J) | Binance public klines, BTCUSDT, 2019-01-01 → present, 1m native, aggregated upward. Public REST, no credentials, read-only. |
| Spread and depth (C, D, E, H) | **our own BAV-1 recordings** — 3 hours, hash-chain verified, `~/genesis-evidence/bav-1/` |
| Fees | Binance published schedule, recorded with retrieval date |

**The depth data is three hours of one symbol.** Everything derived from it (C, D, E, H) is
indicative, not established, and is labelled so in every result. Extending it is a recording
job the instrument can already do, and is the natural follow-on if C/D/E turn out to bind.

Kline timestamps are interval-**opening** on Binance. This is treated as a data fact to verify
against the raw files, not to assume: treating them as closing would leak a full interval of
future into every return — the same class of error caught in RDB-1 §2.

## 8. Analysis discipline

- Every point estimate carries an interval, from a **moving-block bootstrap**. Returns are
  serially dependent and heteroskedastic; an IID bootstrap would understate every interval.
- Results are reported **by year as well as pooled**. A statistic pooled over 2019–2026 hides
  that the market changed. If an answer is unstable across years, it is not an answer.
- The full period is used. **No holdout is defined here** — this contract fits nothing and
  predicts nothing, so there is nothing to overfit. A holdout becomes mandatory the moment a
  hypothesis search begins, at Phase 5.
- **Raw outputs are reported before interpretation**, in the order A→J, with Q1 results stated
  before Q2 results. Interpretation is a separate document.

## 9. What this cannot establish

- **Nothing about whether an edge exists.** A reachable `p*` is a necessary condition, never a
  sufficient one. "The bar is 53%" does not imply anyone can clear it.
- **Nothing about Q3.** Every slippage figure assumes the recorded book is available to us at
  the recorded moment. It is not, by ~291 ms.
- **Nothing about adverse selection**, the largest unmeasured term. See §3.
- **One symbol, one venue.** BTCUSDT is the deepest crypto market in existence. Every liquidity
  conclusion is a best case and will not transfer to a thinner instrument.
- **The past.** Volatility regimes change; a horizon affordable in 2021 may not be in 2027.
  This is why §8 requires per-year reporting.

## 10. Out of scope, explicitly

No strategy code. No parameter search. No optimisation. No backtest. No paper trading. No
signal construction of any kind. A measurement that would require choosing a strategy parameter
is out of scope and is reported as such rather than resolved by picking one.

## 11. Amendments made before freezing

Made by the researcher on 2026-08-10, on the draft of the same date:

1. **Fee / spread / impact kept explicit**; fee-only costs treated as optimistic, never as
   execution cost. → §3.
2. **"Cost not depth binds" and "1-day-plus maker" demoted** from architectural assumptions to
   falsifiable pre-registered predictions with stated falsification criteria. → §5, P11/P12.
3. **Variance-ratio and Roll retained**, with the pre-registered bid-ask-bounce expectation and
   an explicit prohibition on reinterpreting a matching result as a discovery. → §4.
4. **φ = 0.5 and `p* ≤ 60%` defined and justified** in the contract rather than assumed. → §6.
5. **Phase 2 restructured around three separated questions**, with Q3 marked out of scope. → §1.

The draft's §5 previously read *"the project's target is 1-day-plus horizons executed as a
maker."* That stated a conclusion the measurement had not produced. It is now P12, a
prediction. The correction is recorded rather than quietly applied.
