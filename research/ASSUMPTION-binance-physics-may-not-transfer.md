# ASSUMPTION: that Binance's order-book physics transfers to Hyperliquid

**Date:** 2026-08-20
**Status: UNTESTED, load-bearing.** Written down before it is forgotten, because it is the kind
of premise that gets asserted once and then inherited by every document after it — which is
exactly how "21 days" survived a full day of reasoning.

---

## 1. The assumption

The cascade forecast is built from two sources that are **not the same market**:

| | question | source | depth |
|---|---|---|---|
| **the physics** | how far does forced flow push price, and does the book hold? | **Binance USD-M** `bookDepth`, free | 3 years |
| **the current state** | who is positioned where, and can they defend? | **Hyperliquid** `clearinghouseState`, live | since 2026-08-19 |

**Calibrating on Binance and applying to Hyperliquid assumes the two behave alike under stress.**
That has not been tested. It is plausible, and plausible is precisely the category of premise
this project has been burned by.

## 2. Why it might not hold

**Different liquidation mechanics.** Hyperliquid has **HLP**, a vault that backstops liquidations
and takes the other side. Binance has an insurance fund and auto-deleveraging. A venue with a
committed backstop may absorb forced flow that Binance would let run — which would make a
Binance-calibrated model **over-predict** cascade depth on Hyperliquid.

**Different participants.** Binance USD-M is dominated by large professional market makers.
Hyperliquid's maker population is smaller and differently incentivised. Depth withdrawal under
stress is a behavioural property of the makers, not a law of nature.

**Different size.** Binance BTCUSDT open interest is far larger than Hyperliquid's. Absolute
depth does not transfer; only the *shape* — depth as a fraction of its own normal — plausibly
does, which is why the measurement is normalised. **That normalisation is what makes transfer
conceivable at all, and it is not proof that it works.**

**Different microstructure.** Hyperliquid is an on-chain CLOB with block-paced matching.
Binance is a conventional matching engine. Quote-cancellation dynamics under stress may differ
simply because cancelling is not equally cheap or fast.

## 3. Why it might hold

The measured quantity is deliberately **relative**: depth after a move divided by depth before,
normalised by hour-of-day. That strips out size, currency, tick regime and the diurnal cycle,
leaving a behavioural ratio.

If market makers everywhere widen and thin when volatility spikes — which is what makers do,
for the same inventory-risk reason — the ratio may be roughly venue-invariant even where the
levels are not.

**This is an argument, not evidence.**

## 4. How to test it, and it is cheap

Hyperliquid publishes its order book free over WebSocket (`l2Book`), and Genesis already has a
Hyperliquid dialect and a running recorder.

**Record Hyperliquid book depth alongside `hl1`, compute the same normalised
depth-after/depth-before ratio, and compare the curve against the Binance one.**

- If the two curves have the same shape, transfer is supported and the three-year Binance
  calibration is usable
- If Hyperliquid's book holds up better — plausible, given HLP — then Binance-calibrated cascade
  depths are **too pessimistic** and must be scaled
- If it holds up worse, they are too optimistic, which is the dangerous direction for anyone
  acting on the forecast

**Cost: one more subscription on a recorder that is already running, and disk.** No new
dependency, nothing bought.

## 5. What must not happen in the meantime

**No forecast may be published as a Hyperliquid number while calibrated only on Binance**, unless
the document says so plainly on the figure itself. The honest form is:

> *"cascade depth modelled from Binance liquidity behaviour; not yet validated on Hyperliquid"*

That is the same discipline as restating coverage on every LIQ-2 figure, applied to a different
borrowing.

## 6. Why this document exists

Three claims were closed wrongly in the last two days, each because a premise was asserted and
never measured — the 21-day recording, Coinglass being free, and the exhausted universe. Each
was inherited by the next document and looked better established with every restatement.

**This one is written down while it is still visibly an assumption**, before it becomes a
sentence in a product page that nobody remembers deciding.
