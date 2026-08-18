# Market prior-art audit

**Date:** 2026-08-18
**Status: THIRD PASS — all five candidate areas covered. Still not a finished audit.**
**Updated 2026-08-18** with the slow-D1 search, the completeness review, and the external-information branch.
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

Twelve web searches and three source documents read. That is a **survey, not an audit.** It is
enough to find the obvious prior art and nowhere near enough to establish that something is
novel.

**Confidence is marked per finding.** Where a paper was read, it is cited and quoted. Where
only search summaries were seen, that is stated.

> **A discipline note that applies to this document specifically.** The assistant produced
> **five false "not found" claims in a single day** — the Phase-5 constraint (C5), `src/` being
> empty by rule (C2), the vision statement (C3, withdrawn), the recommendation of D1 without a
> literature check, and the description of the external-information branch as untouched ground.
> Each was an unchecked absence, asserted.
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

### The slow version — searched 2026-08-18, and it closes too

The literature above operates where latency dominates. MEASURE-1 places affordability at
**≥4 h**, so the surviving question was whether a *slow* version exists: book state informing a
decision hours out, where 291 ms is irrelevant.

**Two findings, and they point the same way.**

**One — microstructure signal does not survive to that horizon.** The alpha in microstructure
signals *"decays extremely rapidly, often within microseconds"*. And specifically on this asset:
Bitcoin volatility forecasting work found short-term book features sufficient, with **40 and 50
minutes of order-book features producing no improvement**. The information is gone long before
four hours.

**Two — and where liquidity *is* predictable at daily scale, it is a mature field using the
estimator Genesis already built.** Realized-illiquidity forecasting is established: the slow
decay of the realized Amihud autocorrelation is modelled with **HAR** — the same heterogeneous
autoregressive specification Genesis implemented for volatility — alongside Engle's
Multiplicative Error Model and VAR analyses, with production infrastructure at NYU Stern's
V-Lab.

So the slow version is not an unexplored gap between two literatures. It is **occupied, by a
mature field, using machinery already in this repository.**

**Verdict: A — import**, at both speeds. *Confidence: moderate-high. Search summaries; the
Realized Illiquidity paper was not read in full.*

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

## External information — news, sentiment, on-chain, macro

**Audited 2026-08-18, after the assistant twice described this branch as "the only genuinely
untouched ground" and "the branch where a null would mean something new." Both statements were
made without checking. Both were wrong.**

### News and sentiment → returns

Heavily worked, across venues and methods. Sentiment from Twitter predicts crypto spot returns;
predictability is attributed *"mostly to social media sentiment rather than macroeconomic
news"*; work exists on BTC and ETH futures specifically, on sentiment and the crypto risk
premium via technical indicators, and on social-media sentiment through COVID.

**Verdict: A — import.** *Confidence: moderate. Search summaries; no paper read in full.*

**One acknowledged gap, and it is the same gap as the left branch.** The literature notes that
*"the cryptocurrency literature on technical analysis has largely ignored drivers of technical
analysis return adjusted by transaction costs"*, and that sentiment strategies producing excess
returns *"did not take into consideration operational issues such as transaction costs"*.

### On-chain

The most worked region of the four, and the only one that is **operationally** crowded rather
than merely academically crowded: exchange in/outflows, active addresses, whale transfers, with
published work forecasting volatility spikes from whale transactions and using on-chain data to
predict Bitcoin cycles.

And the fact that matters most: **over 85% of crypto hedge funds already incorporate blockchain
analytics into their investment process.** This is not an unexplored frontier — it is standard
practice at institutions with capital, latency and data budgets Genesis does not have.

**Verdict: A — import**, and the most contested of the four.

### Fast news attribution — structurally closed, for the same reason D1 was

The methodological problem is real, acknowledged, and its solution is hardware Genesis cannot
have.

> *"A large number of transactions and quote changes have identical timestamps"* — the provider
> *"stamps the time on package arrival rather than when transactions were actually executed"*.
> *"If your clock cannot resolve events with sufficient precision, you cannot definitively
> reconstruct which order arrived first or whether a trade was reactive or anticipatory."*

The remedies are PTP and GPS-synchronised network cards resolving to nanoseconds. Genesis
observes from Nairobi with a measured **291 ms floor**. Attributing a price move to a news event
at the resolution the problem requires is not available from here.

This is the **same structural objection that closed D1**, arriving independently in a different
literature: the part that would be worth doing needs precision Genesis has already measured
itself out of.

### What actually survives on this branch

Slow news effects — daily and multi-day — do not need millisecond attribution. But at that
horizon the effect is exactly what the sentiment literature already covers, and the only
unanswered question is again **transaction costs**.

---

## The result across all five areas

**Every area audited returns A — import.** Book state fast, book state slow, cross-section,
volatility, external information. The map's two branches were drawn as asymmetric — audited on
the left, untouched on the right. **They are not asymmetric. They are the same.**

And the residual question is identical on both:

> **What does a known effect do at a 291 ms latency floor, a ~4 h cost floor, and retail fee
> tiers?**

The literature does not answer this, not because it is hard, but because **no one else has these
constraints**. That is a measurement, not a discovery, and it is the only thing left that is
both unanswered and reachable.

## A correction the assistant owes

The right-hand branch was described as untouched ground on 2026-08-18, twice, in a map handed to
the researcher as a basis for choosing direction. It was not checked before being described.

That is the **fifth** instance today of the same error: **asserting an absence without
searching for it.** The previous four — the Phase-5 constraint, `src/` being empty by rule, the
vision statement, and the recommendation of D1 without a literature check — are recorded in C5,
C2, C3 and this document's D1 section.

The pattern is now well enough evidenced to state as a rule rather than an observation: *this
assistant's claims about what does not exist should be treated as unverified until searched, in
every domain, without exception.*

---

## The recorder and BAV-1 — reviewed 2026-08-18

Both outside readers independently flagged the recorder as the quietly impressive component: a
gap-honest, integrity-verified logger whose completeness label was *validated* to carry
information (p = 0.0165) rather than assumed to. Neither could say whether that was novel.

**Searched three framings. The answer was in the third, and it is the most interesting result
in this audit.**

**1 — Market data engineering.** Dataset-quality metrics are treated as first-class concerns in
current work: clock drift, dropped messages, duplicate payloads, reconnect gaps, stale book
state, out-of-order events. Gap-aware recording is standard. But this is *detection*, not
validation of the detector.

**2 — General data quality.** Completeness and accuracy are treated as **separate dimensions,
assessed independently**. Completeness is measured by population rates against required
attributes; accuracy requires *"a reference point: what is the ground truth?"* Nothing in this
framing treats a completeness flag as a *predictor* of accuracy. That is the BAV-1 question, and
it is not a standard question here.

**3 — Remote sensing and earth observation. This is where it lives.** Satellite products carry
quality flags stating whether data are *"of good, acceptable or unreliable qualities"*, and
validating those flags against independent in-situ measurement is a mature practice with its
own infrastructure — match-up databases, HYPERNETS, NOAA's VIIRS and MODIS validation
programmes.

**So BAV-1's method is not new. It is the match-up-database validation pattern from earth
observation, independently re-derived and applied to market data.**

**Verdict: A — import**, from remote sensing rather than from finance.
*Confidence: moderate. Three searches, no paper read in full.*

### Two things worth keeping, neither of them a novelty claim

**The field being imported from says its own version is often done badly.** Flag effectiveness
*"varies and often lacks rigorous assessment"*, and validation is *"performed with little (if
any) assessment on their impacts to both the quality and quantity of the matchup dataset as a
whole."* BAV-1 did assess exactly that — it reported cell counts, exclusions, strata, and the
power limitation, and it separated fidelity from completeness rather than merging them. Doing
an established thing more carefully than the field that established it is not a contribution,
but it is not nothing either.

**BAV-1 is more honest about its reference than the pattern it re-derives.** Remote-sensing
match-ups validate against in-situ ground truth. BAV-1 explicitly refuses that framing:
*"Neither channel is ground truth. This validates consistency between two Binance-delivered
representations."* The imported pattern assumes a privileged reference; BAV-1 states it does not
have one.

### The pattern this repeats

DR0002 closed the cognitive-architecture programme on finding that its foundations were
established science, independently re-derived. **This is the same finding, a second time, in a
different field.** The project's most distinctive-looking asset is a competent re-derivation of
earth-observation validation practice.

That is worth recording plainly, because it is the second instance of a pattern and the first
was significant enough to close a research programme.

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

- [x] ~~Search the **slow** version of D1 — book state at ≥4 h.~~ Done. Closes as import.
- [x] ~~Review the completeness-validation question.~~ Done. Closes as import, from remote
      sensing.
- [ ] Read Fischer & Krauss, the Realized Illiquidity paper, and the Hawkes and
      liquidity-withdrawal papers in full, rather than summaries.
- [ ] Search the breadth-stability question at half-year resolution — the one narrow
      measurement Genesis holds that has not been checked against anything.
- [ ] Search whether the match-up validation pattern has been applied to **market data**
      specifically. Established in earth observation; unknown in finance.
- [ ] Give the statistics to someone literate who is neither the researcher nor an assistant —
      the "no second pair of eyes" gap an outside reader named.

Nine searches and three sources read. Every verdict above is provisional in exactly the way its
confidence marking says, and no verdict of "novel" or "open" appears anywhere in this document
— by design, and for the reason given in the discipline note.
