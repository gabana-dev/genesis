# Genesis — Business Plan

**Version 1. 2026-08-21.**
Every number in this document is measured or cited. Where something is not measured it says so.
There are no illustrative figures anywhere — a placeholder in a plan becomes a claim in a
product, and that has already happened three times in this project.

---

## 1. What Genesis is

> **Genesis turns raw exchange data into evidence-backed intelligence about liquidity,
> positioning and market fragility — and publishes the research behind every number, including
> the research that failed.**

It is **not** a prediction service. Genesis spent six weeks establishing that it cannot predict
crypto prices, and the arithmetic in §7 explains why almost nobody can at this horizon. Selling
prediction would mean selling something we have specifically disproved for ourselves.

What Genesis sells instead is **measurement nobody else performs, with its limits stated.**

## 2. The one-line positioning

**Everyone else shows you the market. Genesis tells you what it can and cannot see.**

Not one of the eight providers surveyed (§4) publishes a coverage figure on a position map, an
interval on a derived number, or a record of when they were wrong. Two habits, one asset.

## 3. What we sell

Four surfaces, one pipeline. All are generated files, not a query service — a static JSON on a
CDN cannot go down, costs nothing to serve, and needs no ops.

| surface | contents | price | purpose |
|---|---|---|---|
| **`/map`** | live clusters, size, distance, **coverage stated** | **free forever** | distribution — the citation habit |
| **`/intel`** | **defensibility**, fragility state, liquidity condition | **paid** | the product |
| **`/history`** | derived datasets and the archive | **paid** | researchers, backtesters |
| **`/scorecard`** | every published claim and what happened to it | **free always** | the argument, not the product |

**`/map` stays free permanently, not as a trial.** Coinglass's real moat is that every post
quoting a liquidation number says "via Coinglass". That citation habit is worth more than
subscriptions, and charging for what HyperPerps gives away free wins nothing and costs the
channel.

## 4. The market, verified from provider documentation

| provider | sells | price | lacks |
|---|---|---|---|
| **HyperTracker** | per-wallet positions, liquidation price, 16 months history, REST/WS/webhooks, complete coverage | $179–1,999/mo | **`withdrawable`**, margin used, any coverage figure, any track record |
| **Coinglass** | 150+ endpoints, **estimated** heatmaps from OI + assumed leverage | $35–879/mo | exactness on Hyperliquid, defensibility |
| **0xArchive** | trades from 2023, L4 book with wallet identity, liquidation events, projected levels from clearinghouse data, **data-quality API** | free tier → paid | per-wallet endpoint (explicitly "not an account, wallet, or position endpoint"), `withdrawable` |
| **HyperPerps** | exact live clusters, whale/retail split | **free** | cross-margin (declared), history, probabilities |
| **Tardis** | trades, l2Book, fastBook, bbo, funding+OI, from 2024-10 | paid | anything account-level, any completeness statement |
| **QuickNode** | trades, L4 book, TWAP, TP/SL, mempool | usage | account state |
| **Dwellir** | node archives incl. `periodic_abci_states` from Jan 2025 | undisclosed | parsed account state |
| **Hyperdash / ASXN / Nansen / Arkham** | dashboards, wallet labels | mixed | Hyperdash has **no API at all** |

**What they prove:** people pay $35–$1,999/month for crypto market data. The market exists.

**What they leave open:** four things, listed next.

## 5. What we add, and why it is defensible

**1. `withdrawable` → defensibility. Measured, unique.**
No provider exposes the field. And it **cannot be derived**: naive `accountValue − totalMarginUsed`
matches the venue **19% of the time** and **misclassifies one wallet in five** as able to defend
its position (F-0001, n=74). Half of wallets with open positions hold **exactly zero** free
collateral.

*This is the strongest single asset. It is a fact about positions, not a prediction about price,
so nothing in §7 undermines it.*

**2. Depth evaporation. Measured over 1,324 days.**
Near-book depth falls to **0.8462** during the largest moves and **0.6573** in the worst quarter,
against **1.0015** in quiet markets — unchanged to four decimal places across 1,320 distinct days
(F-0002). Withdrawal takes **minutes, not seconds**: barely a flinch at 1 minute, collapsed by 5.

*Every liquidation product implicitly assumes that number is 1.000 everywhere.*

**3. Coverage stated on every figure.**
We see **53.3%** of Hyperliquid BTC open interest, CI [40.9%, 70.8%] (F-0003). We say so on
every number. Only 0xArchive publishes anything comparable, and not for positions.

**4. A published scorecard.**
Every claim, and what happened to it. **A competitor cannot copy this in a fortnight** — they
would have to start publishing falsifiable statements today and be judged for months. They will
not, because their products are never wrong about anything.

**And the differentiator nobody in this market has:** it is legible. Tardis is a docs site,
0xArchive is JSON, HyperTracker is a table, Coinglass is a wall of charts. Making dense things
readable is the founder's demonstrated strength and is worth more here than another endpoint.

## 6. What we do NOT claim

**We do not claim liquidations cause price moves.** CASCADE-1 tested it on Binance: 228 episodes,
K1 met. At 15 minutes forced flow produced **+40.07 bps** with a **60.4% hit rate**, beating a
permutation null — and **lost to a random minute in the same symbol in the same hour (44.52
bps)**. Liquidations happen because the market is already moving.

**Scope, stated honestly:** that result is Binance. The contract's §9 says it establishes nothing
about Hyperliquid, whose HLP backstop and far smaller book differ in ways that could cut either
way. That test is a background track, not a blocker.

**We do not claim evaporation predicts anything.** It is a conditional description: given a move
of this size, the book was this much thinner. Whether it forecasts what comes next is an open
question and is the next experiment, not a feature.

## 7. Why we do not sell prediction

Detecting a 52% directional edge needs **4,900 independent observations — 13.4 years** on one
instrument at a daily horizon. 51% needs **53.7 years** (F-0005).

Genesis established this by discovering that its **own** tests were underpowered by one to two
orders of magnitude: GEN-1 could resolve nothing below 54.67% and measured 52.10%.

**Almost every product selling crypto prediction is selling a number it does not have the
observations to support.** Saying so is both honest and marketable.

## 8. Assets in hand

| dataset | size | why it matters |
|---|---|---|
| Binance spot+perp+liquidations, **one clock** | 14 GB | interleaving cannot be reconstructed from separate feeds |
| Binance `bookDepth`, 3 years | 592 MB | 3.7M snapshots, 0 missing days — the evaporation calibration |
| Hyperliquid wallet-attributed fills | 2.1 GB | 4.2M fills, 911 wallets, 22 days |
| Hyperliquid trades, buyer **and** seller wallets | 357 MB | 32,000+ wallets discovered |
| Hyperliquid book at ±2.7% | growing | settles the Binance-transfer assumption |
| Positions + liquidation price + **`withdrawable`** | growing | the unique field |
| Binance metrics, 6 years, 6 assets | 170 MB | OI, top-trader ratios, taker volume |

**Input cost: zero.** Every source is free and public. The cost is compute, storage and uptime.

## 9. Revenue model

Priced in **USDC**. Crypto-native buyers pay in stablecoins, which removes the payment-rails
problem entirely — the single largest operational constraint on a Nairobi-based solo founder
selling to a Western market.

| tier | price | for |
|---|---|---|
| Free | $0 | map, coverage, research, scorecard |
| Pro | $29–49/mo | alerts, defensibility detail, multiple assets, history |
| API | $99–299/mo | structured intelligence for applications and agents |
| Data | negotiated | derived datasets, custom research |

**Prices are proposals, not measurements.** They bracket the observed market ($35 Coinglass
hobbyist to $1,999 HyperTracker top tier) and must be tested against actual buyers.

## 10. Distribution — the real constraint

**This is where the founder's three previous products failed. They work and go unseen.**

Nothing in §5 solves it, so it is addressed directly:

**Research as the front door.** Genesis has produced findings that contradict things the market
believes. Each is an article, a chart, a machine-readable finding, and a citation:

1. *Crypto order books lose 15% of their depth during large moves* — F-0002
2. *The liquidity doesn't disappear immediately. It takes minutes.* — F-0002
3. *Liquidation maps show where forced selling is. We tested whether they predict anything.* — F-0010
4. *Half of leveraged traders have no collateral left to defend with* — F-0001
5. *Your backtest needs 13 years to prove what it claims* — F-0005
6. *25 crypto assets are worth 2.65 independent bets* — breadth measurement
7. *We measured the spread at 0.00154 bps and the cost at 5.19* — EXEC-1
8. *The 21-day recording that was four hours: how a premise survived a full day* — methodology

**This content already exists as evidence.** It needs writing, not researching — and negative
results are more credible than another "we found an edge" post, which is the entire point.

**Machine-readable second.** Every finding ships as structured JSON with method, sample, interval
and provenance. When an agent is asked what happens to crypto liquidity during selloffs, Genesis
should be a retrievable source with a citation, not a chart it cannot read.

## 11. Build order

**v1 — assembly, not research. Everything it needs exists.**
`/map` with coverage stated · defensibility from `withdrawable` · `/scorecard` published empty ·
one page. Static JSON, generated on a schedule, free hosting.

**v2 — the research front door.** Publish findings 1–4 above with their datasets.

**v3 — `/intel` and `/history`.** Paid tiers, once free users exist to convert.

**v4 — the fragility question.** Does depth evaporation predict anything after controlling for
volatility? A contract with a power section, as required since 2026-08-20.

## 12. What would kill this

| | |
|---|---|
| **Nobody finds it** | the documented failure mode of every previous product — §10 is the only defence and it is unproven |
| Hyperliquid ships account-state history | possible; would compress `/history` but not defensibility |
| HyperTracker adds `withdrawable` | one field, one day of their engineering. **The lead is their inattention, not a moat** |
| Nobody pays for honesty | plausible. Traders may want a red chart, not an interval |

**Odds, honestly: 10–15% that this becomes meaningful revenue.** Most of the loss sits in
distribution, not in the measurement.

## 13. Why it is worth building anyway

The measurement work is done and paid for. The findings are real and publishable whether or not
anyone subscribes. The build is assembly of components that already pass 31 test suites.

And the failure mode is benign: if nobody buys, Genesis remains a public body of original crypto
market research with a track record of saying when it was wrong — which is a credential, a
portfolio, and a distribution asset in its own right.

**What we are not doing is starting a sixth research branch to avoid shipping.**
