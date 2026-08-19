# The cost problem is a fee problem, and netting is an 8.9× lever we are not pulling

**Date:** 2026-08-19
**Classification: measurement + analysis. Nothing adopted into a frozen contract.**

---

## 1. Where the cost actually is

Hyperliquid tier 0, one-day hold, per round trip:

| term | bps | share |
|---|---|---|
| **fees** (2 × 1.50 maker) | **+3.0000** | **96.6%** |
| adverse selection (2 × 0.1301) | +0.2602 | 8.4% |
| spread captured | −0.1554 | −5.0% |
| **total** | **3.1048** | |

**Fees are 96.6% of the cost.** Everything Genesis has spent effort on — spread, adverse
selection, queue position, markout — sums to a net **+0.105 bps**, or 3.4% of the total.

## 2. What the running experiments are actually doing about it

**COND-1 optimises 8.4% of the problem, and was designed when we believed it was the whole
problem.**

Its endpoint is markout at 60 seconds — the adverse-selection term. That was the right target
when adverse selection was believed to be 1.19 bps and dominant. The horizon study
([`adverse-selection-horizon.md`](adverse-selection-horizon.md)) measured it at **0.1301 bps at
one day**. Halving it would save 0.13 bps against a 3.105 bps stack.

COND-1 remains worth running — it is frozen, it is nearly free, and markout matters for any
shorter-horizon work. **But it is not addressing the cost problem, and it should not be
described as if it were.**

**ECON-1 measures the cost problem; it does not attack it.** It prices the signal against a
fixed cost stack and asks whether the signal clears it. That is its job. It reduces nothing.

## 3. The lever nobody has pulled: netting

ECON-1 charges a **full round trip at every decision point** — every 8 hours. But consecutive
predictions mostly agree:

| horizon | side flips between consecutive decisions |
|---|---|
| 1 day | **11.2%** |
| 3 days | **8.8%** |

**Eighty-nine percent of the time, the strategy closes a position and immediately reopens the
same one.** Netting consecutive same-side signals means holding instead:

| | cost per decision | net (exploratory gross) |
|---|---|---|
| trade every decision, 1d | 3.105 bps | +18.22 bps |
| **net consecutive, 1d** | **0.348 bps** | **+20.98 bps** |
| trade every decision, 3d | 3.105 bps | +22.12 bps |
| **net consecutive, 3d** | **0.274 bps** | **+24.95 bps** |

**An 8.9× reduction in the dominant cost term, for free.** No new signal, no new venue, no
capital, no change to a single prediction. Pure implementation.

## 4. Why ECON-1 is not being amended to do this

Amendment 1 stated: *"Had the amendment loosened anything, it would be void."* Netting lowers
the cost stack and therefore makes the test easier. **It may not be added.**

ECON-1 therefore measures the **worst-case implementation** — one that pays the fee eight times
more often than an obvious implementation would. That is conservative rather than wrong, and it
cuts both ways:

- If ECON-1 **passes**, the real implementation is strictly better than the measured one.
- If ECON-1 **fails**, netting alone might have saved it, and we will not know from ECON-1.

The second is a real risk of a false negative, and it is recorded here so that a negative ECON-1
result is not read as closing more than it closed.

**The netted variant is a separate declaration**, and it should be written now, before ECON-1
reads, so it cannot be shaped by ECON-1's outcome.

## 5. The other half of the bar, which has been ignored

The break-even is `p* = 0.5 + c / (2φm)`. **Two terms, and all of Genesis's effort has gone into
c.**

`m` is the median absolute move over the holding period. It is not fixed:

| horizon | median \|move\| | bar at 3.105 bps |
|---|---|---|
| 1 day | 142.5 bps | 0.5218 |
| 3 days | 264.3 bps | 0.5117 |

**The cost is fixed per trade; the prize scales with the move.** That reframes the cost problem
as a *when to trade* problem — and it connects to two things already in hand:

- **F6, already declared.** The signal is right more often on large moves (ratio 1.1170,
  p = 0.0002). It is already selecting for high `m` on its own.
- **The volatility holon, built and abandoned.** T3.2 was framed as "is the volatility holon
  tradeable?" — meaning options. **That is the wrong use.** A volatility forecast predicts `m`,
  and `m` sets the bar. **Its natural job is to say when the bar is low enough to bother
  trading.** It is a cost-management instrument, not an alpha source, and Genesis built it and
  then never connected it to the thing it is actually for.

## 6. What does not work, recorded so it is not re-attempted

**Leverage does not help.** Fees scale with notional exactly as the edge does. The ratio is
invariant.

**Volume-based fee tiers are unreachable.** Binance's cheaper tiers and Hyperliquid's maker
rebates both require volume a small account cannot generate. The ladder's bottom rung is above
the ceiling.

**Staking tiers are capital, not edge.** Hyperliquid Bronze is ~$5,900 of HYPE at price risk to
save 0.30 bps per round trip. Against a netted cost of 0.348 bps, buying tiers is now close to
pointless — **netting makes the fee tier almost irrelevant**, which is the clearest sign of
which lever matters.
