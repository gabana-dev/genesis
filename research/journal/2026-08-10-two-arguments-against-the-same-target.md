# Arguments against the same target

**2026-08-10, extended 2026-08-11. An observation. It decides nothing and selects nothing.**

Recorded because it emerged in discussion rather than from an experiment, and would otherwise
exist nowhere. It is written down so that it can be examined later, not acted on now.

---

## The first two arguments

**One is measured.** The MEASURE-1 power analysis
([`../experiments/0008-measure-1-cost-of-being-right.md`](../experiments/0008-measure-1-cost-of-being-right.md) §8)
established that at daily horizons the variance ratio can only resolve effects outside
[0.851, 1.150], and that reaching 80% power against a true VR of 0.95 would require **68 years**
of BTCUSDT history. The instrument is seven years old. This is a structural limit on method:
directional structure at affordable horizons cannot be settled by this route, ever.

**One is theoretical, and imported.** Hayek, *The Use of Knowledge in Society* (1945): the price
system's function is to compress dispersed, tacit, local knowledge into a single number, without
any participant needing to hold the underlying facts. If that is roughly right, then the
information available to us on public data is by construction *already in the price* — not
because we have researched insufficiently, but because compression is what the mechanism does.

These arguments share no premises. One is a statement about sample size and test power; the
other is a claim about what a price is. They arrive at the same place:

> **Predicting the direction of returns at affordable horizons, from public information, is the
> hardest target available — and Genesis has been implicitly aiming at it.**

## What follows, and what does not

**Does not follow:** that no structure exists. The power result is explicitly *absence of
evidence*, and Hayek's argument is about central tendency, not about the impossibility of local
advantage — he in fact identifies where advantage legitimately lives (particular knowledge of
time and place, not analysis of public facts).

**Does not follow:** any change of direction. No target is selected here. The market direction,
the phase gates and EXEC-1 stand exactly as they are.

**Does follow, as an observation:** the two objections weaken considerably against targets other
than return direction. Volatility is persistent and far more predictable than direction; it also
has vastly more effective observations at every horizon, so the power wall does not bite the same
way. Liquidity and execution quality are measurable directly from recordings Genesis already
owns. Whether any of that is worth pursuing is the researcher's decision and is not taken here.

## A third argument, added 2026-08-11

Same discussion, different premises again. **What a venue publishes freely maps where the
competition is not.**

Binance gives away full order-book depth, the diff stream, and seven years of historical klines,
to anyone, unauthenticated. It does so because a limit order book cannot perform its function in
private -- displayed liquidity is the mechanism -- and because its revenue is fees on volume, so
freely available data is customer acquisition for the product rather than the product. The
contrast with equities exchanges, which sell market data as a major revenue line, is competitive
rather than technical.

What Binance does **not** publish is therefore the informative part:

- **queue position** within a price level
- **trade attribution** -- whether an observed size decrease was a fill or a cancellation
- **low latency**, which is sold or granted by physical proximity

So the shape of the free data marks the contested ground. Anything freely published is by
construction already priced in, which is Hayek's argument arriving from a third direction.

**This one is uncomfortable, and the discomfort is the point.** The scarce resources are closed
to Genesis as well. Queue position and trade attribution are not published to anyone, and the
latency floor is ~291 ms from Nairobi, which is geography and not an engineering problem. Free
data is priced in; scarce data is unavailable. Stated plainly, that makes "no edge found" the
*likely* outcome rather than merely the honest one to prepare for. Recorded now, while it costs
nothing, rather than after a disappointing number.

**What survives is not an information edge.** Two things:

1. **The data is free; using it correctly is not.** MEASURE-1 found three properties of
   Binance's public klines that silently corrupt any analysis built on them -- halt-truncated
   bars, an unreliable `close_time`, and a millisecond-to-microsecond switch that would place
   every 2025+ bar ~50,000 years in the future. All three sit in data that thousands of people
   have downloaded. That is an **operational** advantage, not an informational one: weaker, but
   real, and it is what Genesis has spent its existence building.

2. **Scarce advantages decay with horizon.** A 291 ms disadvantage is fatal at one second and
   irrelevant over three days; queue position decides everything for a market maker and nothing
   for a position held a week. The advantages Genesis cannot obtain stop mattering as the
   horizon lengthens -- the same hours-to-days region the measured constraints already implied,
   reached from a different direction.

The surviving region is narrow and not empty: **long horizons, less-contested targets,
correctness as the advantage.**

**Status of this argument.** It is reasoning about market structure, not a measurement. Three
arguments agreeing is suggestive and is not evidence; two of the three are theoretical. It is
recorded so it can be weighed after EXEC-1, not so it can harden into doctrine before it.

## One idea that came out of the same discussion

Hayek's framing invites the losing question — *can the compression be decompressed?* — to which
his own answer is no. The question it does not invite, and which appears to be open: **a
compression has fidelity, and fidelity varies.**

How much aggregated judgment stands behind *this* price, right now? Depth behind the touch,
resilience after consumption, dispersion across levels, independence of flow. A price backed by
$34M of resilient depth is a different quality of summary than the same number at 04:00 UTC with
half the book withdrawn.

Genesis has already built this instinct — for itself. The completeness rule asks whether Genesis
may claim its book contains every published change. The analogue asks whether a price may claim
to contain every relevant judgment. Same epistemics, one level up, and computable from data
already recorded with no new source, no arrival clock and no licensing.

**Recorded as an idea, not a plan.** It has no contract, no trial declaration, and no place in
the current phase.

## Provenance and prior classification

The discussion also proposed a latent-state estimator over sentiment, news and microstructure.
That is **dynamic-state filtering**, which
[`../prior-art-and-opportunity-map.md`](../prior-art-and-opportunity-map.md) classifies **A —
import if needed, never as research**, and which the prior-art gate therefore denies a
laboratory. Genesis has moreover already run that experiment: RDB-1
([`../experiments/0006-rdb-1-real-data-bridge.md`](../experiments/0006-rdb-1-real-data-bridge.md))
applied exactly that architecture to real sequential data and found the model did not reliably
beat "yesterday at this clock time." Noted so the idea is not rediscovered as novel.

The Hayek reading, the philosophical position that prompted it, and any decision about targets
are the researcher's. This entry contributes form only: it records that two independent
arguments met — three, after 2026-08-11 — and what does and does not follow.

## Status

Nothing changes. EXEC-1 remains frozen with four declared trials outstanding and a recording
running to ~2026-08-17. This is to be re-read when Q3 closes, not before.

The third argument sharpens what 17 August decides. The question is no longer only whether the
maker advantage survives adverse selection. It is: **if Genesis's plausible advantage is
operational rather than informational, is a trading system the right expression of it, or is the
instrument itself the thing worth having?** The kill criteria already anticipate both answers.
