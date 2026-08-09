# NEM Battery Environment Study — closed

**Date:** 2026-08-09
**Status:** **CLOSED.** Investigation complete. A factual finding, not a direction decision.
**Classification:** environment study under
[`decisions/0003-engineering-posture-real-data.md`](decisions/0003-engineering-posture-real-data.md).
Not an experiment. Nothing was built, downloaded, modelled, or run.
**Outcome:** the environment **does not satisfy** DR0003's found-not-invented test for the
*dynamics*. It does satisfy it for the *consequence*.

---

## The question

> Can we obtain a sufficiently real sequential decision environment in which Genesis controls
> the decision but does not author the environment's dynamics or consequence?

Asked of the Australian National Electricity Market, specifically grid-scale battery operation,
after RDB-1 exposed the limitation that **nothing consumed the forecast** — no cost, no
decision, no consequence for being wrong
([`experiments/0006-rdb-1-real-data-bridge.md`](experiments/0006-rdb-1-real-data-bridge.md)).

## Method and its limits

Public documentation only: AEMO's MMS data model reports, the Electricity Data Model v5.7
(May 2026), the AEMC rule-change record, AEMO IESS programme documents, industry analysis, and
peer-reviewed storage-optimisation literature.

**One limitation is material.** `aemo.com.au` returns **HTTP 403 to programmatic clients** —
the same obstacle `rdb/README.md` already records for the AEMO licence page. Several primary
sources were therefore read via the accessible mirrors (`nemweb.com.au`,
`visualisations.aemo.com.au`, `tech-specs.docs.public.aemo.com.au`), and one page could not be
read at all. It is named in *Unresolved*, below.

## Findings — the found/invented ledger

| Component | Status |
|---|---|
| Unit identity (`HPRG1`/`HPRL1`, Hornsdale Power Reserve, Neoen, commissioned 2017-12-01) | **Found** |
| Power/energy rating (150 MW / 193.5 MWh after the 2020 expansion) | **Found** — published by operator, ARENA, AEMO |
| Prices, demand, dispatch outcomes at 5-minute resolution | **Found** |
| Actual charge/discharge behaviour of the real operator | **Found** — `DISPATCH_UNIT_SCADA`, per unit, per interval |
| Information set at each historical decision point | **Found** — see below |
| Monetary consequence (energy) | **Found** — arithmetic on published settlement prices |
| Benchmark | **Found** — "percentage of perfect foresight", an industry-standard metric with published comparators |
| **State of charge** | **INVENTED** — not published; must be integrated through an assumed efficiency, parasitic-loss rate and initial condition |
| **Clearing / execution** | **INVENTED** — assumes a bid transacts at the spot price |
| **Objective scope** | **INVENTED** — energy-only, omitting FCAS co-optimisation |
| **Price-taking** | **INVENTED** — and documented false at fleet scale |

## The four gaps, resolved

**1. Bid publication timing — closed, and favourably.** From the MMS data model, verbatim:
*"BIDDAYOFFER data is confidential to the submitting participant until made public after 4am the
next day."* `BIDPEROFFER_D` *"updates daily shortly after 4am"*; `DISPATCHLOAD` is
*"Private; Public Next-Day"*.

This **strengthened** the environment rather than merely documenting it. Other participants'
bids were provably invisible before gate closure (~20 seconds before each interval), so a
reconstruction that withholds them is *faithful to what the decision-maker faced*, not a
convenient simplification. The information boundary is set by a published confidentiality rule,
not by our judgement. Combined with AEMO's archived `P5MIN` and `PREDISPATCH` forecasts, the
information set at each historical moment is exactly reconstructable.

**2. Post-IESS representation — closed.** IESS completed 2024-06-03, replacing separate
charge/discharge DUIDs with a single `BIDIRECTIONAL` DUID (transition to 2025-03-03). The
convention is signed: `BDU_CLEARED` is *"Cleared Generation (positive) or Consumption
(negative)"*. Charge and discharge remain separable by sign. **A representation change, not an
information loss** — structurally the same as the 30-minute → 5-minute break RDB-1 already
detected from the files and normalised.

**3. Archive depth — partially closed.** NEMWeb is tiered (`CURRENT` 24h, `ARCHIVE` 13 months,
`MMSDM` monthly back to 2009 or earlier); `PREDISPATCHPRICE` and `P5MIN_REGIONSOLUTION` are
listed among public MMSDM reports. Per-table start dates differ. Settleable by a directory
listing; not settled here, as that edges toward downloading.

**4. State of charge — closed, negatively. This is the finding that ends the study.**

- The current `DISPATCHLOAD` table carries `INITIALMW`, `TOTALCLEARED`, ramp rates, AGC status
  and the full FCAS enablement set — **and no state-of-charge, stored-energy or storage-level
  field.**
- The current Electricity Data Model (v5.7) documents **no such table or column anywhere**.
  Bidirectional units appear only as signed cleared MW.
- A practitioner enumeration of the public datasets lists no SOC data.
- **Decisively:** WattClarity, which publishes the NEM's best-known battery state-of-charge
  analysis, **derives** it — mean of SCADA `InitialMW` across each 5-minute interval, a
  conversion loss rate applied to both charge and discharge, and an assumed constant parasitic
  loss. The domain's own expert analysts author exactly the assumptions we would have to author.
  If AEMO published SOC, they would read it.

## Verdict

**The consequence is genuinely not authored.** That half is real, and it is more than Genesis
has ever had: a cost measured in money that someone actually paid, computed from published
prices, against a benchmark the industry maintains and a competitor set whose actual decisions
are public.

**The dynamics cannot be obtained without authoring them.** State of charge is not published, so
the state must be reconstructed through parameters Genesis chooses. This is not an incidental
parameter — **SOC is the coupling that makes the problem sequential.** Authoring how it evolves
means authoring the mechanism that makes this a sequential decision problem at all.

So the answer to the central question is **no** — established from sources, not from a gap in
searching. The last load-bearing assumption is **unavoidable**, not merely unresolved.

**What this does not decide.** Whether to use the environment anyway, under fully declared
assumptions and labelled as such, is a decision the researcher has not made and this document
does not make. The finding is that it cannot be done *cleanly*, not that it cannot be done.

## Where the research/engineering boundary fell

Worth recording, because this study is the first real test of the DR0002/DR0003 split.

- **Nothing here was research.** Every modelling component encountered — MILP and MINLP
  degradation-aware arbitrage, multi-stage stochastic programming with dynamic programming,
  convex aging-aware control, price forecasting — is category **A, import**. Under DR0003 (6)
  none of it warrants a laboratory.
- **The one thing that looked like an opening was not one.** The NEM fleet captures ~32% of
  perfect-foresight revenue, and the gap is attributed to price-spike uncertainty and
  state-of-charge commitments made hours ahead. A gap between practice and a perfect-foresight
  bound is **not** evidence that established methods fail; it is consistent with the future
  simply being unknowable. Recording it as an opening would have been the third repetition of
  the DR0001 failure mode.
- **The boundary did real work.** DR0003's found-vs-invented rule produced a determinate answer
  on a real environment, and the answer was inconvenient. That is the first evidence that the
  posture governs rather than decorates.

## What this study produced

A negative result, which DR0003 (4) makes a first-class output, and which is not rescued here.

Also produced: the observation that **an environment can supply a real consequence while still
requiring an authored state**, and that these two properties are independent. Genesis's prior
framing treated "real environment" as a single property. It is at least two.

> **Proposed, NOT adopted.** Following the precedent by which DR0002 preserved the
> environment-first gate without promoting it: a lesson learned during an investigation is not
> automatically a rule. This observation has governed exactly one decision — this one. That is
> not enough to elevate it, and it is recorded here rather than in any gate.

## Unresolved

- The AEMO change schedule titled *"Bid Validation Data and State of Charge (SOC) related
  Data"* could not be read (403). It implies SOC flows through participant-facing bid-validation
  systems; whether any of it is public is unread. Given that the NEM's professional analysts
  estimate SOC rather than read it, the odds of this overturning the finding are low — but it is
  the one primary source not consulted.
- Exact earliest month of the `P5MIN` and `PREDISPATCH` archives.
- The unit's actual round-trip efficiency and degradation trajectory, as opposed to the
  literature range of 86–92%.

## Source

[`decisions/0002-close-the-genesis-research-program.md`](decisions/0002-close-the-genesis-research-program.md);
[`decisions/0003-engineering-posture-real-data.md`](decisions/0003-engineering-posture-real-data.md);
[`experiments/0006-rdb-1-real-data-bridge.md`](experiments/0006-rdb-1-real-data-bridge.md);
[`experiments/0005-sparse-observation-decision-relevance.md`](experiments/0005-sparse-observation-decision-relevance.md) §E
(costless environments); [`journal/2026-08-09-real-data-is-not-a-simulator.md`](journal/2026-08-09-real-data-is-not-a-simulator.md);
[`prior-art-and-opportunity-map.md`](prior-art-and-opportunity-map.md).

External sources are listed in the session record rather than duplicated here; the load-bearing
ones are the MMS Data Model `DISPATCHLOAD` and BIDS package definitions, the Electricity Data
Model v5.7, the AEMO IESS transition plan, and WattClarity's stated state-of-charge methodology.
