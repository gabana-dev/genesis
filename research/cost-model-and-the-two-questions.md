# The 1.83 bps is not profit, and passive quoting on BTCUSDT is closed

**Date:** 2026-08-18
**Status: CLOSED — a negative result, derived from already-measured quantities.**
**Classification: BUILD + IMPORT. No novelty claimed.** Instrument:
[`../market/costs.py`](../market/costs.py), 9 checks in
[`../tests/test_costs.py`](../tests/test_costs.py).

T1.1 asked whether the 1.83 bps maker advantage survives real costs. It does not survive as
*profit*, because it was never profit. It survives, intact, as something else.

---

## 1. Two questions that had been running together

**EXECUTION.** *Given that Genesis wants to trade, is posting cheaper than crossing?*
Measured per side, against the alternative of crossing.

**MARKET MAKING.** *Ignoring any directional view, does quoting both sides earn money from the
spread?* Measured per round trip, against doing nothing at all.

EXEC-1 answered the first. Its number has since been read as answering the second. It does
not, and the gap between the two answers is three orders of magnitude.

---

## 2. What EXEC-1 actually established

Binance USD-M futures charge **5 bps taker, 2 bps maker**. Posting rather than crossing
therefore saves **3 bps per side** in fees. Adverse selection takes back 1.19 bps at 60 s,
leaving:

> **1.81 bps per side — the amount by which posting beats crossing.**

This is a **cost reduction on a trade you were going to do anyway.** It is real, it reproduces
exactly from the recorded inputs, and it says nothing whatever about whether quoting is a
business.

*(The headline 1.828 bps in EXEC-1's record is the 300 s figure; at 60 s it is 1.813. The
difference is immaterial and both are recorded.)*

---

## 3. What market making actually costs

A round trip buys at the bid and sells at the ask, capturing the full spread and paying the
maker fee **twice**:

```
net  =  spread  −  2 × maker_fee  −  adverse_selection  −  funding  −  inventory_cost
```

The spread is not assumed. MEASURE-1 measured it on the bav-1 recording, 2,042 samples:

| | value |
|---|---|
| measured full spread, median | **0.00154 bps** |
| maker fees, round trip (VIP 0) | 4.00 bps |
| adverse selection at 60 s | 1.19 bps |
| **net per round trip** | **−5.19 bps** |
| **costs as a multiple of the spread captured** | **3,376×** |

**The spread on BTCUSDT is approximately one and a half ticks.** There is nothing in it to
capture. Costs exceed the entire captured spread by a factor of over three thousand.

### 3.1 The fee tier does not rescue it

The obvious hope is volume. The best publicly listed Binance maker fee is **0%** — not
negative; no rebate tier was found. Setting the fee term to zero:

> **net = −1.19 bps per round trip. Adverse selection alone still buries it.**

That closes the escape route explicitly rather than by assumption. **This is not a fee
problem.** Free maker fees do not make quoting BTCUSDT profitable, because the spread is
narrower than the adverse selection.

### 3.2 The break-even form of the answer

For quoting to break even the spread would have to be **5.19 bps**. It is **0.00154 bps**.
It would have to widen by **3,376×**.

---

## 4. What this closes, and what it does not

**CLOSED: passive market making on BTCUSDT for spread capture.** Not marginal, not
"needs better execution", not "needs a bigger VIP tier". Off by three orders of magnitude,
from measured inputs, and robust to the most favourable fee assumption available.

**NOT CLOSED, and now the more interesting half:** the 1.81 bps execution saving is real. Its
use is to make a *directional* strategy cheaper to execute — which is exactly where MEASURE-1
already pointed with P12, *"the reachable region is 1-day-and-longer, as a maker."* That
prediction and this result agree, and neither was derived from the other.

### 4.1 Consequence for COND-1 — its interpretation changes, its value does not

COND-1 conditions **markout**, and markout is the adverse-selection term. Read as *"when is
market making profitable?"* it is now asking about a closed question.

Read as *"when is posting cheapest?"* it is asking a live and useful one, because adverse
selection is the only term left that Genesis can influence. If conditioner A, B, C or D
identifies states where adverse selection is materially lower, that directly widens the
execution saving on every trade a directional strategy makes.

**COND-1 is not amended.** It is frozen, its endpoint is markout in bps, and markout is what it
still measures. Only the sentence describing why the answer matters has changed, and that
sentence was never in the contract.

---

## 5. A correction

Earlier today, in conversation, the maker fee was quoted as **10 bps (Binance spot retail)**
and the 1.83 bps described as *"five times underwater"*. Both wrong:

- EXEC-1 is priced on **USD-M futures**, where the maker fee is **2 bps**, not 10.
- More importantly the comparison itself was malformed. 1.83 bps is a **saving against
  crossing**, not a margin against fees, so setting it beside a fee at all was the same
  category error this document exists to correct.

The corrected finding is **worse** than the incorrect one, and derived properly.

---

## 6. Funding — a term the model did not have

Perpetual funding is exchanged **every 8 hours** between longs and shorts. It is a real cash
flow on held inventory, published in advance, and it was absent from Genesis's cost model
entirely.

Imported from Pindza & Bambe Moutsinga (2026), *J. Finance and Data Science* **12**, 100197,
which reports annualised funding impact exceeding 10% of position value in stressed periods.
The mechanism is a venue fact; the paper is what prompted its inclusion. **No novelty claimed.**

Three properties, each with a check:

- **It is signed.** A positive rate means longs pay shorts, so a *short* inventory under
  positive funding **receives**. Omitting the term is therefore **not conservative** — it
  discards a real credit as readily as a real charge.
- **It is not pro-rated.** Funding is exchanged at the timestamp or not at all. A position
  closed at 7 h 59 m pays nothing. A model that pro-rated it would invent a cost the venue
  never charged.
- **It is material.** 1 bp per interval is ~11% annualised, which dwarfs every other term
  here — and is roughly 7,000× the measured spread.

Funding does not revive market making: §3.1 shows adverse selection alone closes it before
funding is reached. It matters for **inventory carried by a directional strategy**, which is
where it is now available.

### 6.1 What the paper also says, which is worth recording

Pindza & Bambe Moutsinga train PPO and SAC agents on 29,606 **hourly** bars. Their learned
policies come out *"only marginally positive"*; their headline result comes from a hand-built
variant with a volatility filter, fee-aware quoting and momentum inventory targeting. Their own
conclusion: *"profitability depends critically on explicit fee, regime, and inventory filters."*

Two things follow. **Filters before agents** — their own evidence has hand-crafted filters
beating the learned policy. And **hourly bars cannot answer a microstructure question**; their
spread and order-flow variables are proxies, and they say tick-level validation is still
required. Genesis's seven days of millisecond depth and trades is the better instrument for
this specific question, and its statistical discipline — pre-declared families, BH, deflated
Sharpe — is stricter than the paper's single selected variant on one holdout.

---

## 7. What is not claimed

No strategy exists. No order has been placed. This document prices hypothetical round trips
using measured inputs and venue-published fees; it selects nothing and recommends nothing.
Inventory cost is priced as **risk** in the Avellaneda–Stoikov form, and risk aversion is a
required argument rather than a default, because it is a preference and not a measurement.
Realised inventory P&L is a different term and belongs to T3.3.
