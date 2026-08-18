# Market prior-art audit — first pass

**Date:** 2026-08-18
**Status: FIRST PASS — incomplete. Not a finished audit.**
**Type: 2 (factual), assembled by the assistant. No direction is selected here.**

Closes the material half of **C4**: `canon/architecture.md` designates
[`prior-art-and-opportunity-map.md`](prior-art-and-opportunity-map.md) as *"the authority on
what is worth researching"*, but that map is dated 2026-08-08 and covers cognitive
architecture, axiology and the Research OS. It has nothing on market microstructure or
financial econometrics — the only field worked in since. This begins to fill that gap.

**The gate this serves is ratified, not optional.** DR0003 §6: *"The prior-art gate applies
first and unchanged. Anything classified import (A) gets no laboratory. Import it, validate it,
label it, move on."*

## Method and its limits — read before using any verdict below

Four web searches and two source documents read. That is a **first pass, not an audit.** It is
enough to find the obvious prior art and nowhere near enough to establish that something is
novel.

**Confidence is marked per finding.** Where a paper was read, it is cited and quoted. Where
only search summaries were seen, that is stated.

> **A discipline note that applies to this document specifically.** The assistant produced
> **three false "not found" findings in this repository today** — the Phase-5 constraint (C5),
> `src/` being empty by rule (C2), and the vision statement (C3, withdrawn). Each was an
> incomplete search reported as an absence.
>
> **Therefore: nothing below claims novelty on the basis of not having found prior art.** An
> unfound result is recorded as *unestablished*, never as *novel*. Any A–F verdict of "open"
> would require a real literature review, which this is not.

---

## D1 · Book state → near-future book state

**The candidate:** use the current order book to predict liquidity and adverse-selection
conditions seconds to minutes ahead — not price direction. Recommended by the assistant on
2026-08-18 as the strongest option, and by an outside reader independently.

### What is established

**Forecasting quoted depth from the book is solved and published.** *Forecasting Quoted Depth
With the Limit Order Book* (Frontiers in AI, 2021) predicts quoted depth — combined volume at
best bid and ask — one minute ahead on Tel Aviv Stock Exchange data across 2012–2018, using
deep feed-forward networks over book layers 0–9.

> Best bid-ask layer alone: ~49–52% directional accuracy. **Adding one deeper layer: ~66–67%**,
> statistically significant. *"The additional improvement in prediction decreases with layer
> depth"* — most of the information sits one layer below the surface.

*Confidence: high. Paper read.*

**Adverse selection and limit-order placement is a mature modelled area.** *Limit Order
Strategic Placement with Adverse Selection Risk and the Role of Latency* (arXiv 1610.00261,
2016) connects empirical evidence, stochastic control and latency cost for exactly this
problem, and claims to be first to do so.

*Confidence: high. Abstract read directly.*

Adjacent and active: liquidity-withdrawal forecasting with microstructure feature panels
(2025); Hawkes-process forecasting of order-flow imbalance explicitly framed as *"an estimate
of adverse selection after the fact"*; and frameworks evaluating limit-order tactics on
expected fill price, adverse-selection cost and opportunity cost.

*Confidence: moderate. Search summaries only.*

### The finding that matters most, and it is not the crowding

The 2016 paper's central result is a **structural objection to Genesis pursuing this at all**:

> *"Exploiting liquidity prediction knowledge requires low latency to be economically
> beneficial"* — predictive knowledge *"becomes valueless without sufficient time to cancel and
> reinsert orders"* — establishing *"a rational for market makers to be as fast as possible as
> a protection to adverse selection."*

Genesis has a **measured 291 ms latency floor** from Nairobi, median ~430 ms, recorded as a
hard boundary of the same kind as the 68-year power limit. The literature states that the
economic value of precisely this prediction is eroded by precisely this constraint.

**Verdict: A — import.** The capability is solved. And the one specific advantage that would
make it worth doing — acting on the prediction fast enough to matter — is the one Genesis
structurally cannot have.

### What this does *not* rule out

The literature above operates at second-to-minute horizons where latency dominates.
MEASURE-1 places affordability at **≥4 h**. Whether a *slow* version exists — book state
informing a decision hours out, where 291 ms is irrelevant — was not searched for and is
**unestablished, not open.** It would need its own audit.

---

## D2 · Cross-sectional residual structure

**What is established.** *Statistical Arbitrage in Cryptocurrency Markets* (Fischer & Krauss)
uses machine learning to predict whether a coin outperforms the **cross-sectional median** of a
sample — the same construction, on the same asset class.

Independently, the cost finding echoes MEASURE-1's: of observations showing arbitrage spreads
≥20 bps, *"only 40% of top opportunities generate positive returns after transaction costs and
spread reversals."* Cost binds here too.

**Verdict: A — import.** *Confidence: moderate. Search summaries only; the Fischer & Krauss
paper was not read.*

**Not settled by this pass:** whether *breadth stability tracked per half-year over 5.5 years*
— the specific measurement Genesis already has — is covered. That is a narrower question and
was not searched.

---

## D3 · Volatility predictability

Already settled inside the repository before this audit began. The exploration names
**Corsi (2009) HAR-RV** as *"the standard against which volatility forecasts are judged"*, and
Genesis reproduced it to four decimal places across five years.

**Verdict: A — import.** Reproducing a standard baseline is validation, not a finding.
*Confidence: high, from internal record.*

---

## The recorder — inconclusive, and deliberately left so

Both outside readers independently flagged the recorder as the quietly impressive component:
a gap-honest, integrity-verified logger whose completeness label was *validated* to carry
information (p = 0.0165) rather than assumed to.

One search found that dataset-quality metrics — clock drift, dropped messages, duplicate
payloads, reconnect gaps, stale book state, out-of-order events — are treated as first-class
concerns in current work. It did **not** surface anything doing the specific thing BAV-1 did:
measuring whether a self-reported completeness label *predicts* agreement with an independent
channel.

**Verdict: none. Unestablished.** One search is not evidence of absence, and this document's
own discipline note forbids reading it as such. If the researcher wants this question answered,
it needs a real review — and it is the one area where the answer might not be "import."

---

## What this changes

**All three candidate directions come back A — import.** Under DR0003 §6 that means: no
laboratory. Import, validate, label, move on.

That is not a prohibition on doing them. It is a statement about what they could ever be. Set
against `canon/vision.md`'s two open questions:

> **1. Can Genesis reliably know what is happening?**
> **2. Can that capability produce something practically or financially valuable?**

All three candidates are **Question 2** work, and all three are import. If the goal is economic
value, import is entirely legitimate and the project's whole engineering posture (DR0003) exists
to permit it. If the goal is a contribution, **none of these three is one.**

**The assistant's D1 recommendation is substantially weakened**, and the reason is worth
recording: it was made without checking the literature, on an argument about Genesis's
differentiated asset. The literature says the differentiating factor in that area is latency,
which Genesis has already measured itself out of.

---

## What would make this a real audit

1. Read Fischer & Krauss, and the liquidity-withdrawal and Hawkes papers, rather than summaries.
2. Search the **slow** version of D1 explicitly — book state informing decisions at ≥4 h.
3. Search the breadth-stability question at half-year resolution.
4. A proper review of the completeness-validation question, which is the only one that might
   not return "import".
5. Give the results to someone statistically literate who is not the researcher or an assistant
   — the "no second pair of eyes" gap an outside reader named.

Until then this is a first pass, and the verdicts above are provisional in exactly the way the
confidence markings say.
