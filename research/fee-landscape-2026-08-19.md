# The fee landscape: the bar is a property of the account, not of the market

**Date:** 2026-08-19
**Instrument:** [`../market/feemap.py`](../market/feemap.py) ·
[`../market/evidence/feemap.json`](../market/evidence/feemap.json)
**Classification: measurement of published schedules. Not a result, not a recommendation.**

Every Genesis result so far was judged against one cost assumption — Binance USD-M VIP 0,
2 bps maker, **4 bps round trip** — which produced the **52.81%** bar that DIR-1 and DIR-2 were
measured against. DIR-2 missed it by 0.4 points.

That bar is not a property of Bitcoin. It is a property of the account.

---

## 1. The map

Break-even hit rate at a 1-day horizon, φ = 0.5, against Genesis's measured **0.5242**:

| venue | tier | maker/side | round trip | bar | point est. clears | requirement |
|---|---|---|---|---|---|---|
| Binance USD-M | VIP 0 | 2.00 bps | 4.00 bps | **0.5281** | **no** | none |
| Binance USD-M | VIP 0 + BNB | 1.80 | 3.60 | 0.5253 | no | pay fees in BNB |
| **Hyperliquid perp** | **Tier 0 base** | **1.50** | **3.00** | **0.5211** | **yes** | **none** |
| Hyperliquid perp | Tier 0 Wood | 1.43 | 2.86 | 0.5201 | yes | stake 10 HYPE (~$590) |
| Hyperliquid perp | Tier 0 Bronze | 1.35 | 2.70 | 0.5189 | yes | stake 100 HYPE (~$5.9k) |
| Hyperliquid perp | Tier 0 Silver | 1.28 | 2.56 | 0.5180 | yes | stake 1,000 HYPE (~$59k) |
| Hyperliquid perp | Tier 3 | 0.40 | 0.80 | 0.5056 | yes | $100M 14d volume |
| Binance USD-M | VIP 9 | 0.00 | 0.00 | 0.5000 | yes | institutional volume |

**Hyperliquid's base tier — no staking, no volume, no requirement whatsoever — is 25% cheaper
than Binance's base tier**, and its bar sits below what Genesis measured.

Source: `hyperliquid.gitbook.io/hyperliquid-docs/trading/fees`, read 2026-08-19, page updated
7 hours before reading. HYPE at $58.69 (`api.hyperliquid.xyz`, same day).

## 2. The honest reading, which is weaker than the table looks

**The point estimate clears. The confidence interval does not.**

DIR-2's G5 measured 0.5242 with a 95% interval of **[0.5063, 0.5404]**. The lower bound is
0.5063, which is below **every** bar in the table except the two zero-fee tiers. So:

> On present evidence, a venue change moves the bar below the measured accuracy — **and leaves
> it inside the confidence interval.** That is a reason to run an experiment, not a reason to
> believe a result.

**Three further reasons this is not a finding:**

1. **The signal was measured on Binance.** The 0.5242 came from Binance positioning metrics
   predicting Binance prices. Hyperliquid is a different venue with different participants and
   its own published metrics. Whether the signal exists there is unknown and unaddressed.
2. **The cost model counted fees only.** That was defensible on Binance, where the measured
   spread is 0.00154 bps — negligible beside 4 bps of fees. **Hyperliquid's book is thinner and
   its spread has never been measured by Genesis.** If the spread there is 2 bps, the venue
   advantage disappears entirely.
3. **Changing the venue after seeing the score is the move the contracts forbid.** DIR-2 is
   frozen and its verdict stands: negative at Binance VIP 0. Re-reading it against a cheaper
   fee schedule would be exactly the retrospective threshold change that K-conditions exist to
   prevent.

**The correct response is a new declaration, tested on Hyperliquid's own data — not a re-reading
of DIR-2.**

## 3. The structural insight, which is the durable part

**Binance discounts volume. Hyperliquid discounts capital.**

Binance's cheaper tiers require 30-day trading volume that a small account cannot generate —
the discount is reachable only by already being large. It is a ladder whose bottom rung is
above the ceiling.

Hyperliquid's tier-0 discounts are bought by **staking**, which is a capital decision rather
than an activity requirement. And its base rate — requiring nothing at all — already beats
Binance's base rate by a quarter.

For an account of Genesis's size that is a categorically different accessibility model, and it
is the first cost lever in this project that does not require already being someone else.

Note the honest limit: the staking tiers are not cheap. Silver is ~$59,000 of HYPE, held at
price risk, to save 0.44 bps per round trip. **The staking ladder is not the opportunity. The
base rate is.**

## 4. What could not be verified, and is therefore not in the table

Recorded because an absence in a fee map reads as "we checked and there was nothing":

- **Binance's intermediate VIP tiers (1–8).** The published table returned "No records found"
  without a login. Only VIP 0 (verified) and VIP 9 (secondary sources) are listed.
- **Bybit and OKX.** Both fee pages are JavaScript-rendered and returned no table content.
  Secondary sources report Bybit base at 2.0 bps maker / 5.5 bps taker on perps, and OKX maker
  turning negative at institutional tiers. **Neither is verified and neither is in the table.**
- **Bitget's reported −0.005% maker rebate promotion** on ~130 perpetual contracts. Secondary
  source only, explicitly described as promotional and temporary. A cost structure that can be
  withdrawn is not a foundation.
- **Hyperliquid's own maker rebates** (−0.001% to −0.003%) require 0.5–3.0% of exchange-wide
  14-day maker volume. That is professional market-maker territory and is not reachable.

## 5. What this actually changes

**Nothing about DIR-2's verdict.** It was negative at the cost it declared, and it stays
negative.

**Everything about what to test next.** The cheapest reachable round trip drops from 4.00 bps
to 3.00 bps with no requirement at all, and the 1-day bar drops from 0.5281 to 0.5211 — a
**0.7 point** reduction, against a signal that missed by 0.4.

The next experiment is not a better model. It is the same measurement, on a venue where the
toll is lower, with the spread measured rather than assumed.

### The concrete next step

**Point the recorder at Hyperliquid and measure its spread and book depth**, exactly as EXEC-1
and MEASURE-1 did for Binance. Everything needed already exists — the recorder, the dialect
abstraction, the completeness machinery, the fill simulator. Hyperliquid publishes a public
websocket API and requires no account to read it.

Until that measurement exists, the third row of the table above is a fee schedule, not a cost.
**Genesis has spent four experiments learning the difference.**

---

## 6. Addendum, same day: Hyperliquid's spread measured

§2 named the unmeasured spread as the thing that could destroy the venue advantage. Measured
directly, 150-second probe on the public websocket (`wss://api.hyperliquid.xyz/ws`, `l2Book`
and `trades` on BTC, no account):

| | Hyperliquid BTC | Binance BTCUSDT |
|---|---|---|
| median spread | **0.1554 bps** | 0.00154 bps |
| depth within 5 bps of mid | **$5.1M bid / $12.9M ask** | — |
| trades observed | 302 in 150 s | — |
| book updates observed | **29 in 150 s** | ~224 in 60 s |

**Hyperliquid's spread is 100× Binance's — and that is good news, not bad.**

A *passive* round trip **captures** the spread rather than paying it: buy at the bid, below mid;
sell at the ask, above mid. The wider book therefore reduces the effective cost:

| | fees | spread capture | effective | 1-day bar | clears 0.5242? |
|---|---|---|---|---|---|
| Binance VIP 0 | 4.00 bps | 0.0015 | 3.998 | 0.5281 | no |
| **Hyperliquid T0 base** | 3.00 | **0.1554** | **2.845** | **0.5200** | **yes** |
| Hyperliquid T0 Bronze | 2.70 | 0.1554 | 2.545 | 0.5179 | yes |

The concern in §2 is resolved in the favourable direction. **The venue advantage survives
measurement**, and is slightly larger than the fee schedules alone suggested.

### 6.1 What the probe also found, which is a real limitation

**The book updated 29 times in 150 seconds** — roughly 0.2/s, against Binance's ~3.7/s. Trades
arrived normally at 2/s, so this is not a dead feed. Hyperliquid's `l2Book` appears to publish
throttled snapshots rather than continuous diffs.

**That matters more than the spread.** Genesis's entire microstructure toolkit — queue position,
fill bracketing, cancellation-versus-fill separation, adverse-selection markouts — assumes a
continuously updating book. At 0.2 updates/second, EXEC-1's methods do not transfer, and
anything resembling COND-1 is not computable there.

Recorded as a **150-second probe, not a measurement.** It establishes an order of magnitude and
nothing more. Whether the update rate is a subscription artefact, a rate limit, or the venue's
actual behaviour is not established.

### 6.2 The unmeasured term is now adverse selection, not spread

EXEC-1 measured 1.19 bps of adverse selection at 60 s on Binance — the cost of being picked
off, which consumed 40% of the maker advantage there. **It has not been measured on
Hyperliquid**, and with a book that publishes 0.2 times a second it is not obvious it can be,
by the methods Genesis currently owns.

The bar figures above, on both venues, count fees and spread only. They are optimistic by
whatever adverse selection turns out to be. That was true of every bar in this project and is
restated here because the venue comparison does not change it.
