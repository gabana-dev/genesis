# Prior art, 2026-08-18: four papers, one of which closes an argument for us

**Classification: IMPORT.** Read against Genesis's open questions. Nothing here is novel to
Genesis and nothing here is adopted into a frozen contract.

---

## 1. Pindza (2026), *Microstructure alpha: hierarchical learning and cross-asset transfer in cryptocurrency markets*, Frontiers in Blockchain

**This paper reaches tonight's conclusion independently, and it is the most important of the
four.**

3.4 million minute-level observations, six cryptocurrencies, Binance spot and perpetual,
August 2025 – February 2026. Purged walk-forward cross-validation with explicit leakage
controls. Its own words:

> *"microstructure signals carry genuine but weak information content that is useful for
> understanding market quality but not exploitable at standard retail fee levels."*

It uses **exactly the fee schedule Genesis used** — Binance VIP 0, 10 bps per side on spot
(20 bps round trip), 2–5 bps on perpetuals.

**What this does for Genesis.** The cost model's conclusion —
[`cost-model-and-the-two-questions.md`](cost-model-and-the-two-questions.md) — was derived from
a seven-day order-book recording and a measured spread. This paper reaches the same place from
3.4 million minute bars, six assets, and a different method entirely. **The negative result is
not idiosyncratic to Genesis's data, its instrument, or its week.** That is worth more than any
of the positive claims in the other three papers.

Three further findings, each directly usable:

**LightGBM produced −10.94% out-of-sample R² under purged validation, while linear OLS produced
+1.23%.** A catastrophic negative R² means the model is worse than predicting the mean. With
3.4 million observations and proper leakage controls. **This is a hard design constraint on any
directional experiment Genesis runs: start linear.** Gradient boosting on microstructure
features at this signal-to-noise ratio is a documented way to lose.

**No cross-asset transfer.** Models trained on one crypto fail on others. Genesis measured the
same thing from a different direction — the cross-section holon reported effective breadth
1.03 across 25 instruments and the integrator refused to combine. Two independent routes to
*"these are not independent opinions."*

**Strong within-asset transfer between spot and futures.** This one cuts against us, and is
recorded because it does. If spot and perp carry substantially the same information for the
same asset, then COND-1's conditioner A — basis — may be measuring less than hoped. **COND-1 is
frozen and is not amended.** This is a caution for interpreting its result, not a change to it.

## 2. Le (2026), *Funding-Aware Optimal Market Making for Perpetual DEXs*, arXiv:2605.06405

Formulates market making with funding as a stochastic state variable, solving a reduced
inventory-funding HJB. Its central idea — that **inventory carries dual exposure, mark-to-market
risk *and* a state-dependent funding cash flow** — is precisely what CARRY-1 measured
empirically, and the theoretical and empirical routes agree.

**But its backtest assumes away everything that decided tonight's questions.** By its own
statement: *"no modeling of queue position, latency, maker priority, or adverse selection"* and
*"no explicit transaction fees beyond spread capture."*

Genesis has now measured all five. Fees alone closed market making by a factor of 3,376, and
adverse selection closed it again at a 0% maker fee. **A market-making result computed without
fees is not a result about trading.** Results are also reported in unnamed "units" over a
five-week holdout on Hyperliquid, a different venue with a different fee structure.

**Import:** the inventory-funding coupling as a formalism, if a quoting policy ever exists.
**Reject:** the backtest, as evidence about anything Genesis could do.

## 3. Kitvanitphasu, Kyaw, Likitapiwat & Treepongkaruna (2026), *Bitcoin wild moves: evidence from order flow toxicity and price jumps*, Research in International Business and Finance 81, 103163

VPIN — volume-synchronised probability of informed trading — **significantly predicts future
price jumps**, with positive serial correlation in both VPIN and jump size. Price jumps only
occasionally feed back into VPIN, so the direction is mostly one way. Robust across jump tests
including Jiang–Oomen, which is designed to survive microstructure noise.

Also documents **time-zone and day-of-the-week effects in VPIN**.

**This is the best candidate for the declaration after COND-1.** It is a published, replicable,
directionally-relevant signal, and Genesis has the data to compute VPIN — q5 carries perp trades
with venue-supplied aggressor side, which is what VPIN needs.

Two things to be honest about:

- **It cannot enter COND-1.** COND-1 is frozen at 29 cells. VPIN would be a fifth conditioner.
- **A jump is not a direction.** VPIN predicting *that* a jump occurs is not the same as
  predicting *which way*, and a strategy needs the second. Whether the sign is predictable is
  not established by this paper and must not be assumed from it.

The day-of-week finding also settles an earlier open item: the "weekend liquidity asymmetry"
idea was parked pending months of data. It is documented in the literature. **Import it rather
than spend a quarter rediscovering it.**

## 4. DolphinDB, *Market making strategies* (tutorial)

An Avellaneda–Stoikov implementation reference: γ = 0.1, k = 1.5, 0.01 BTC orders, 1000 ms
cadence, 5 BTC position limit, **minimum spread 0.01% of mid**.

Engineering reference only — no evidence, no claim. But one number in it is worth recording.

**Its minimum spread floor is 1 bp of mid. Genesis measured the BTCUSDT spread at 0.00154 bps.**
The tutorial's floor is roughly **650× the actual market spread.** A quoting engine run at that
default on BTCUSDT would sit permanently far behind the touch and never fill.

That is the same finding as tonight's cost model, arriving from the direction of a textbook
default: **the standard market-making parameterisation implicitly assumes a market with a far
wider spread than BTCUSDT has.** The model is not wrong; the instrument is.

---

## What changes, and what does not

**Changes:** the next directional experiment starts linear, not with gradient boosting, and
says so in its contract. VPIN is the leading candidate for the declaration after COND-1.
Weekend and time-zone effects are imported, not rediscovered.

**Does not change:** COND-1 stays frozen at 29 cells. CARRY-1's result stands. The cost model's
closure of market making stands, and is now corroborated by an independent published study
using the same fee schedule.

**The standing risk:** four papers in one evening is a lot of reading and no building. Papers
are cheap to consume and feel like progress. The only one that changed what Genesis will
actually do is the first, and what it changed is one line in a contract that has not been
written yet.
