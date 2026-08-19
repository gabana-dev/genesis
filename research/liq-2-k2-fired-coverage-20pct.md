# LIQ-2: K2 fired at 20.24% coverage — and the wallet source is exhausted, not merely thin

**Date:** 2026-08-19
**Contract:** [`../market/CONTRACT-liquidation-map-2.md`](../market/CONTRACT-liquidation-map-2.md),
`sha256 3ec70684b2aec79882191cb8393a22239a7c5c86821930c9cf60f6441639a800`, frozen with
Amendment 1 before this scan ran.
**Status:** **K2 FIRED.** The map is reported unevaluable and the secondary test is not computed.

---

## 1. The scan

First deep scan, 2026-08-19 12:45–15:05Z, over the frozen 5,395-wallet universe.

| | LIQ-1 | LIQ-2 | K2 floor |
|---|---|---|---|
| wallets scanned | 200 | **5,395** | — |
| holding a BTC position | 127 | **2,342** | — |
| **coverage of exchange OI** | **5.8%** | **20.24%** | **25%** |

**M1 predicted coverage above 25%. It failed.** The new selection rule was a large improvement —
3.5× the coverage — and it was not enough. Per K2 the map is unevaluable, the secondary is not
computed, and no directional claim may be made from it.

## 2. Why this is a stop rather than a wider net

The obvious response is "scan more wallets". The data says that is pointless:

| top N wallets by notional | share of scan-set notional |
|---|---|
| 50 | **86.17%** |
| 300 | **97.83%** |
| 1,000 | 99.83% |

**Wallets ranked 1,000–5,395 contribute 0.17% between them.** The universe is not thin at the
tail, it is empty. Extending the recording to gather more wallets of the same kind would move
coverage by a fraction of a percent.

So the missing ~80% of open interest is **not** held by wallets we ranked too low. It is held by
wallets that **never traded during the 21-day recording at all** — and no amount of scanning a
trade-derived universe will ever see them.

**The instrument is exhausted, and that is a more useful finding than a marginal pass would have
been.** A coverage figure of 26% would have licensed a directional test on a map still missing
three quarters of the exchange.

### One caveat that can only make this worse

The denominator uses `openInterest × markPx` from `metaAndAssetCtxs`. If that field follows the
usual convention and counts **one side** rather than both, then total position notional across
all wallets is roughly twice it, and true coverage is nearer **10%**. This is unresolved and is
recorded here rather than settled, because settling it now — after a kill condition has fired —
could only serve to re-open a closed question. **It cannot rescue the result in any case.**

## 3. The genuinely surprising finding: nobody can move the goalposts

Amendment 1 and §2.1 of the contract were built around the caveat that traders top up margin and
push their liquidation price away. `withdrawable` was collected specifically to weight for it.

Across all 2,342 positions:

| | |
|---|---|
| exactly zero free collateral | **1,133 (48.4%)** |
| median `withdrawable`, all positions | **$0.00** |
| median `withdrawable`, non-zero only | **$14.81** |
| mean | $20,630 (one wallet holds $5.69M) |

**Half of all wallets with an open BTC position have literally no free collateral, and the median
of the rest is under fifteen dollars.** They are fully deployed.

Consequently the credibility weighting is **inert**: forced buy within 5% was $46,639,346 raw
against $46,636,874 weighted — a difference of **0.005%**. **M4, which predicted the weighted map
would be more than 40% smaller, fails as completely as a prediction can.**

**The implication runs the other way from the caveat.** These traders cannot move their
liquidation price from inside the account — there is nothing to move it with. They would have to
deposit new money from outside, under stress, on a deadline. The goalpost problem that motivated
half of this contract's design **appears to be much smaller than assumed**, and that conclusion
survives K2 because it is a property of the wallets scanned, not of the wallets missed.

## 4. Predictions scored

| | prediction | outcome |
|---|---|---|
| **M1** | coverage above 25% | **FAILED — 20.24%** |
| **M4** | weighted map >40% smaller than raw | **FAILED — 0.005% smaller** |
| M2 | map is sell-heavy most of the time | not scored — K2 |
| M3 | largest bucket holds >25% of its side | not scored — K2 |
| M5 | secondary is not significant | not computed — K2 |
| M6 | >20% of liquidation prices move hourly | not scored — K2 |

Two predictions failed. Neither failed in the direction of a false positive.

## 5. Collection continues; reading does not

The hourly fast scan stays running. `clearinghouseState` has no history, so an hour not collected
is an hour permanently lost, and the marginal cost is disk.

**This is not a wait for coverage to improve.** It cannot improve — §2 shows the tail is empty.
The data is retained because it is unrecoverable, not because the contract is still live. **No
LIQ-2 figure may be read as a result.**

## 6. The line this project should not cross

LIQ-1 closed at 5.8%. LIQ-2 has now fired K2 at 20.24%. **A third contract that simply casts a
wider net would be us moving our own goalposts**, which is the exact failure every contract in
this repository is built to prevent.

There is a principled distinction, and it is narrow:

- **LIQ-1 closed on a DESIGN error**, identified before any analysis: activity-ranking is
  anti-correlated with forced flow. Fixing a broken instrument before reading it is legitimate.
- **LIQ-2 ran correctly and its kill condition fired on a MEASURED result.** A kill condition that
  fires means stop. It does not mean retry with a larger sample.

A LIQ-3 is therefore only defensible if it uses a **fundamentally different source of wallet
addresses** — not more wallets of the same kind, which §2 proves is worthless. Absent that, the
forced-flow line is closed, and it closes having established two real things: exact per-wallet
liquidation prices are readable at roughly a fifth of the exchange, and the traders behind them
are far more trapped than assumed.
