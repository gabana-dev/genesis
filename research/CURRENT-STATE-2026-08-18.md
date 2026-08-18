# Genesis — canonical state, 2026-08-18

**Type: mixed.** §1–§2 are a factual snapshot (Type-2), assembled by the assistant from the
repository and verifiable against it. §3–§4 are a **survey offered as a proposal** — no
direction is selected here, and nothing in this document amends a contract, declares a trial,
or enters the canon. Per DR0005 and `ai/collaboration.md`.

Assembled after EXEC-1 closed. Every figure below was re-read from the repository rather than
recalled; where a claim could not be verified it is marked **UNVERIFIED** and named.

---

# 1. Current state

## 1.0 The classification that governs everything below

Every market result Genesis holds is classified, *by its own experiment record*, as import or
engineering:

| Record | Classification |
|---|---|
| 0006 RDB-1 | IMPORT + BUILD — engineering validation. Not research. No novelty claimed. |
| 0007 BAV-1 | BUILD — engineering validation. Not research. No novelty claimed. |
| 0008 MEASURE-1 | **IMPORT — every method established and cited. No novelty claimed.** |
| 0009 EXEC-1 | BUILD — engineering measurement. Not research. No novelty claimed. |

**So the answer to "engineering measurement versus research finding" is that there are
currently no research findings.** Not none that succeeded — none *claimed*. Every market
number Genesis holds is an engineering measurement or an imported method applied competently.
That is a deliberate posture (DR0003), not an oversight, and it should be stated plainly
before anything else, because it bounds what the rest of this document can mean.

## 1.1 MEASURED — Genesis's own data, reproducible from the repository

**Observation and its trustworthiness**
- 580,658 events over 168 h, one unbroken run, **0 sequence gaps**, 0 malformed, integrity
  verified. Log `740fc04d…`.
- The recorder's completeness label **predicts** agreement with an independent channel:
  97.5% vs 66.7% in the pre-registered stratum, Fisher exact **p = 0.0165**; Jaccard median
  difference 0.0647, bootstrap [0.0273, 0.1191]. *(BAV-1)*
- Reconstruction fidelity and completeness are **independent properties**: M4 and M6 size
  errors were exactly 0.000000 in both the complete and the deliberately-stale arm. Staleness
  costs *which levels exist*, not the numbers in them.
- 93.4% of the EXEC-1 recording is labelled complete across 82 incomplete intervals.

**Physical and cost constraints**
- Nairobi→Binance latency floor **≈291 ms**, median ≈430 ms. A boundary, not a backlog.
- Spread ≈ **1 tick**; slippage at $10k notional < 0.00002%. Cost is 500–2,000× spread+impact
  at this size — **cost binds, depth does not**.
- Break-even accuracy at 1 h, best tier, φ=0.5: **66.9%**. Affordability begins at **~4 h**.

**Price structure** *(all linear; variance ratio and linear regression only)*
- Well-powered rejections of the random walk at **15 m (VR 0.9357)** and **60 m (VR 0.8933)**.
- 5 m rejected but **underpowered for an effect that size** — should not be cited.
- 4 h, 1 d, 3 d: **blind**. The observed VR sits inside the zone the study could never resolve.
- Per-year decay of that structure: 8.4 se below random walk in 2021 → ~0.5 se from 2022 on.
- After Bonferroni and BH: **1 of 8 years** individually significant, not 3. The 8-of-8 sign
  consistency stands, being a sign test.

**Volatility vs direction** — same data, same features, same walk-forward procedure
- next-day **volatility**: OOS R² **+0.26 … +0.39** per year, never zero in any year.
- next-day **return**: OOS R² **−0.0037** — worse than predicting the mean.
- log-volatility autocorrelation still **+0.19 at 132 days**; return signal exhausted within
  an hour.

**Cross-section** *(28–33 perps, 4 h bars, 2021→2026, fixed universe)*
- **Directional breadth 1.77–2.98 across 5.5 years, no trend** (2.49 → 2.33). Thirty perps
  have been ~2 bets the entire time.
- Residual breadth after removing PC1: ~22–23 (2021) → **~16–19** (2024H2–2026H1), a 20–25%
  decline. PC1 rose 62% → peak 74.8%, now 65%. Mean residual correlation −0.031.

**Carry**
- 7,212 eight-hour funding periods since 2020; longs paid shorts **85.7%** of the time.
  Annualised **+30.6% (2021) → +1.94% (2026)**. Round trip ≈0.30% is earned back in 3.6 days
  (2021) vs **56 days** (2026).
- **One third of all funding observations sit at exactly +0.01000%** — the venue's default when
  the premium index is neutral. Much of "funding is positive" is a constant in the formula.

**Execution** *(EXEC-1)*
- Reach 65.29%; fill ambiguity bracket **0.0033 pp** — effectively zero, and zero away from the
  touch too.
- Adverse selection, median bps: −0.6014 (1 s), −0.8550 (10 s), **−1.1871 (60 s)**, −1.1722
  (300 s). Fraction negative decays 98.9% → 62.5%.
- **E3: 39.07% of the 3 bps maker advantage is lost at the touch at 60 s. 60.93% survives —
  1.828 bps.** 95% CI [0.3676, 0.4139]; Bonferroni 98.75% [0.3592, 0.4195]. Stable across all
  8 days (0.3168–0.4574).

**Data quality**
- Three defects in Binance's public kline archives, found by verification rather than trust.

## 1.2 FALSIFIED — pre-registered predictions that failed

**MEASURE-1:** P2 (1 h magnitude), P6 (VR≈1 at 1 h), **P7** (minute-scale reversion is *not*
bid-ask bounce — lag-1 autocorrelation is positive and Roll returns 665× the measured spread),
P8 (signature plot flat to 1 minute), P12 (partly — 4 h clears as maker, 1 d as taker), P9
(confirmed as 1 tick but the magnitude was wrong by 65×).

**EXEC-1:** X3 (ambiguity does not rise away from the touch), X4 (reach does not fall — 65.58%
→ 65.00% against a predicted <20%), X5 (quiet hours are *better*, not worse), X6 (no
measurable latency effect). X7 direction consistent, separation not established.

**A retracted claim of Genesis's own.** MEASURE-1 §7 asserted that structure and affordability
do not overlap. §8 withdrew the second half: at ≥4 h the study was **blind**, so failure to
reject is absence of evidence, not evidence of absence. *The overlap question is open, not
closed.* This retraction is the single most important correction in the repository.

## 1.3 INFERRED — reasoning from measurements, not themselves measured

- **Three unrelated effects decayed on the same schedule** (minute-scale reversion, funding
  carry, volatility predictability). The professionalisation reading is explicitly *not*
  proven and is labelled as such in the exploration.
- **The tick-scale explanation for X3/X4/X7.** At $63,476 with a $0.01 tick, the 0–5 tick grid
  spans 0.0079 bps — 151× smaller than the 1.19 bps move it was meant to modulate. This is
  arithmetic, but the *conclusion* that the nulls are therefore uninformative about markets is
  an inference.
- **X6's null is structural**: 359 ms against a 300 s TTL is 0.12% of an order's life.

## 1.4 IMPORTED FROM LITERATURE — everything methodological

Lo & MacKinlay variance ratio (heteroskedasticity-robust) · Roll effective spread · Amihud
illiquidity · Corsi (2009) HAR-RV · Grinold's fundamental law · Künsch (1989) and
Politis & Romano (1994) moving-block bootstrap · Bailey & López de Prado deflated Sharpe ·
Benjamini–Hochberg · Hume's is/ought (via the prior-art map).

MEASURE-1 is classified IMPORT in its entirety. **No estimator in this project is novel.**

## 1.5 UNKNOWN — not established, and in some cases not establishable this way

- **Whether linear structure exists at ≥4 h.** Not resolvable by variance ratio on this
  instrument: 80% power at 1 d against VR = 0.95 needs **68 years** of a seven-year-old
  instrument. A hard boundary of the same kind as the latency floor. MEASURE-1 §8 names the
  only escapes: *conditional, cross-sectional, or event-based* evidence.
- **Whether any measured structure is exploitable.** Execution being affordable is necessary,
  never sufficient — CONTRACT §6 says so explicitly.
- **Non-linear or conditional dependence.** Every Genesis measurement is linear. Nothing is
  known either way.
- **Order-flow information.** The recording carries **no trade stream**. Every fill is
  inferred from book evolution.
- **Queue position.** The hypothetical order never exists in the book.
- **News, macro, sentiment, on-chain.** Entirely untouched. Not one measurement.
- **Generality.** One symbol, one venue, one week (EXEC-1) or 7.6 years of one instrument
  (MEASURE-1), one geography, one fee snapshot.

## 1.6 OPEN CLAIMS

- `research/hypotheses/` holds five hypotheses; **four are unwritten** and all five are from
  the cognitive-architecture era. **There are no market hypotheses in the framework at all** —
  market work has proceeded through frozen contracts instead. Two parallel systems exist and
  only one is in use.
- Trial ledger: **27 declared, 27 recorded, 0 outstanding**, chain verified.
- No kill condition is currently triggered. MEASURE-1's and EXEC-1's both passed, and both
  contracts state that passing licenses nothing.

---

# 2. Provenance audit — contradictions found

**Nothing below has been silently resolved.** Each names the decision required.

### C1 · `research/PROGRAM-STATUS.md` is nine days stale and describes a superseded state as current

Last updated 2026-08-09. It says *"Active engineering: RDB-1 … Undecided and the researcher's:
whether to open the holdout."* RDB-1 was **closed by DR0004 on 2026-08-10** and the holdout was
sealed. The document does not mention MEASURE-1, BAV-1 or EXEC-1 — the entire market programme.

Its stated purpose is *"Navigation — so that months from now, with a much larger repository,
orientation is instant."* It is maintained by the assistant as a Type-2 factual snapshot, to be
updated whenever a milestone completes. **This is my failure, not an ambiguity.**

**Decision required:** none on substance — but confirm you want it rewritten to current state
rather than preserved-and-superseded like the triage section. `ai/project_state.md` (also
2026-08-09) has the same problem.

### C2 · `src/` and `tests/` are documented as empty in three places; both contain code

| Document | Claim |
|---|---|
| `README.md` :14 | *"The one rule right now: do not implement cognitive architecture. `src/` and `tests/` stay empty until the foundations in `canon/` and `research/` are ready."* |
| `README.md` :26–27 | table: `src/` — *"Empty by design. Not yet"*; `tests/` — same |
| `canon/architecture.md` :48 | *"implementation and its validation. Empty by design until the foundations are ready."* |
| `src/README.md` | *"**Intentionally empty.** No cognitive architecture is implemented yet, by rule."* |

Reality: `src/` holds 8 modules — `agents.py`, `closed_loop.py`, `environment.py`,
`genesis.py`, `laboratory.py`, `laboratory2.py`, `laboratory3.py`, `sparse_loop.py` — and
`tests/` runs 18 suites.

The sharp part: the rule forbids implementing **cognitive architecture**, and the contents of
`src/` are precisely that (agents, belief-state laboratories, closed loops). So this is not
merely a stale README; either the rule was superseded when Labs 1–3 were authorised, or the
laboratory code was placed somewhere the rule forbids.

**Decision required — choose one:**
1. The rule was superseded by the Labs; update all four documents to say so and record when.
2. The lab code belongs elsewhere (`lab/`), and `src/` returns to reserved-and-empty.
3. The rule stands and the Labs are a knowing, annotated exception.

I will not choose. Any of the three is coherent; they mean different things about what `src/`
is *for*.

### C3 · **This entry was wrong — withdrawn 2026-08-18**

The original entry claimed `canon/vision.md` still frames Genesis as the programme DR0002
closed, and that it was unclear whether the text was history or canon.

**It is entirely clear.** `canon/vision.md` opens with a 60-line **SUPERSESSION NOTICE dated
2026-08-10**, above the historical text, which states what was retired, what Genesis is
exploring now, that quality of knowing is a property of *the structure* rather than of a knower
inside it, that **no application has been selected and Genesis is not a trading system**, and
that a negative outcome is a legitimate result.

The assistant quoted line 102 — which sits *inside the preserved historical text, explicitly
marked as superseded* — and reported it as the current framing, without reading the top of the
file. The same failure as C5: partial reading reported as a finding. Two in one document.

**What survives as a real, smaller defect.** The notice says the two open questions are
*"Stated in full in `roadmap.md`"*. They are not in `canon/roadmap.md` at all —
that document knows only Phase 0. So the deferral points nowhere.

The two questions, as the notice states them:

> **1. Can Genesis reliably know what is happening?**
> **2. Can that capability produce something practically or financially valuable?**
>
> Question 1 is what is currently being investigated. **Question 2 has barely been tested.**

**Decision required (small):** put those two questions in `canon/roadmap.md` so the deferral
resolves, or restate them in `vision.md` and drop the pointer.

### C4 · The "authority on what is worth researching" predates the only domain now worked in

`canon/architecture.md` designates `prior-art-and-opportunity-map.md` as *"The authority on
what is worth researching."* That map is dated 2026-08-08, and its A–F verdicts concern
cognitive architecture, axiology and the Research OS. **It contains no prior-art audit of
financial econometrics or market microstructure** — the only field Genesis has worked in since.

Its bottom line — *"Genesis is a research method in search of a problem worthy of it"* — was
written before markets were adopted and has never been revisited against them.

**Status 2026-08-18 — materially closed, one decision left.**
The market survey now exists: [`market-prior-art-audit.md`](market-prior-art-audit.md), twelve
searches across five areas, **all returning A — import**. The map now carries a scope note
stating what it covers and pointing at it.

**Decision required (the remaining half):** whether the market audit's verdicts are **imported
into this map's A–F classification** — making them part of the authority `canon/architecture.md`
designates — or remain a survey beside it. Merging them would adopt a direction, so it was not
done. §3 below predates the audit and is superseded by it.

### C5 · **RESOLVED 2026-08-18** — the constraint was real, mislocated, and is now in canon

The constraint and the kill criteria have been relocated **verbatim** into
[`../canon/roadmap.md`](../canon/roadmap.md) and
[`../canon/operations.md`](../canon/operations.md) §7 respectively. Both were researcher-authored
and both were sitting in a file the collaboration contract says holds no substance. Moving
authored text is form, not authoring, so it was done.

**Not moved:** the market phase list and the direction sentence that heads it — see C10.

The original entry, kept because the error is the point:

### C5 (original) · The Phase-5 / LLM constraint — **this entry was wrong; corrected 2026-08-18**

The original entry said the constraint *"is not in this repository."* **It is**, in
[`../ai/current_focus.md`](../ai/current_focus.md):

> **LLM enters at Phase 5** … **Never the signal.** **Agents: none until Phase 5**, then one at
> a time, each justified by a measured decision the current system gets wrong.

The assistant searched `canon/` and `research/` but not `ai/`, using paraphrases rather than
the literal wording, and reported the absence as a finding. Caught by an outside reader.

**The real contradiction, which is worse than the one recorded.** A binding research constraint
lives in a file `ai/README.md` defines as assistant-maintained working memory that "describes
state and activity, **never project substance**." Substance is in a form-only file the
assistant may edit. Related: `ai/current_focus.md` also carries a **7-phase market roadmap**
(market literacy → measure → execution → one real decision → paper trading → hypothesis search
→ edge-decay → small capital), while `canon/roadmap.md` — the document `canon/architecture.md`
names as authoritative for phases — knows only Phase 0. **There are two roadmaps and the real
one is in working memory.**

**Decision required:** promote the constraint and the phase list into `canon/roadmap.md` in
your words, or explicitly designate `ai/current_focus.md` as substance-bearing and amend
`ai/README.md` to match. The present arrangement contradicts the collaboration contract.

### C6 · **RESOLVED 2026-08-18**

Phase 0 is now **marked complete** in [`../canon/roadmap.md`](../canon/roadmap.md), with a note
explaining that the two unticked boxes are stale rather than outstanding: `constitution` and
`ontology` were left unpopulated when the thesis they would have served was retired by DR0002.

**RESOLVED in full 2026-08-18.** With C10 settled, the market sequence is now in
[`../canon/roadmap.md`](../canon/roadmap.md) as a **conditional, unauthorised** sequence —
recording what the order *would be* if markets were pursued, so that adopting it later is a
visible decision rather than a drift. There is now one roadmap.

The original entry:

### C6 (original) · `canon/roadmap.md` still shows Phase 0 as *current*

Phase 0 is "build the laboratory", with two of four boxes unticked — including *"Canon
scaffolds populated with authored content"*. Last touched 2026-08-06. Meanwhile four
experiments and five decision records have completed.

**Decision required:** is Phase 0 complete? If so it needs marking, and "later phases" remains
yours to author or to formally leave open.

### C9 · `canon/research-methodology.md` does not describe the research method in use

Added 2026-08-18, while placing DR0006.

The canonical methodology document — 290 lines, designated authoritative — contains **zero**
occurrences of: `contract`, `pre-registration`, `ledger`, `kill condition`, `sha256`, `frozen`.

Every practice the project actually runs on is absent from the document that is supposed to
define how it works. Frozen contracts with digests, kill conditions declared before data,
declare-before-run trial accounting, multiple-comparison correction, the CONTEXT/trial
boundary — all of it emerged after 2026-08-10 and none of it was written back.

This is the same shape as C4: a canonical document that predates the practice it governs, still
carrying authority it can no longer exercise. It also explains how a rule can be ratified and
then lost — there is nowhere canonical that a person writing the next contract would look.

`research/decisions/README.md` does not index the decision records either, so DR0001–DR0006 are
discoverable only by listing the directory.

**Decision required:** either `canon/research-methodology.md` is updated to describe the method
in use (with Source links to the decision records that produced each practice, per the
provenance rule), or it is marked superseded and the decision records become the operative
description. DR0006 in particular needs somewhere canonical to live, or it will be as
discoverable as the phase list was.

### C10 · **RESOLVED 2026-08-18 — in favour of the canon**

The researcher's instruction: *"no application is selected — restate the direction section as
conditional."*

[`../ai/current_focus.md`](../ai/current_focus.md) §Direction is now conditional. It states
plainly that **no application is selected**, that markets are the environment Genesis has been
*measured against* rather than a destination, and that the phase sequence records what the order
*would be* so that adopting it later is a visible decision rather than a drift. The original
wording is preserved beneath it, unedited.

`canon/vision.md` governs. Genesis is not a trading system.

**Consequence:** the phase list is now promotable to `canon/roadmap.md` as a conditional
sequence, because doing so no longer imports a selection. That was the blocker on C6.

The original entry:

### C10 (original) · Two researcher-authored direction statements, same date, in direct contradiction

**Found 2026-08-18 while resolving C5/C6. The most consequential contradiction in this list,
because it answers a question the researcher asked directly.**

[`../canon/vision.md`](../canon/vision.md), supersession notice, 2026-08-10:

> **No application has been selected.** Genesis is not a trading system and must not be framed
> as one.

[`../ai/current_focus.md`](../ai/current_focus.md), Direction, 2026-08-10:

> **Genesis is for financial markets. Everything built from here pushes toward paper trading**,
> with the foundation and architecture orchestrated properly first.

Both researcher-authored. Same date. They cannot both govern.

**Why it matters beyond filing.** The researcher asked on 2026-08-18 whether Genesis is only a
trading system. The assistant answered from `vision.md` alone — *"your own canon forbids
describing it as one"* — without having read the Direction section. That answer was given from
half the evidence, and is the sixth instance of the pattern in C7.

It also blocks C6: the market phase list cannot be promoted into `canon/roadmap.md` without
importing the sentence that heads it, which would resolve this contradiction by relocation
rather than by decision.

**Decision required.** Which statement governs? If markets are selected, `vision.md`'s
supersession notice needs amending and the phase list belongs in the roadmap. If no application
is selected, the Direction section needs restating as conditional — *"if markets are pursued,
this is the order"* — and the contradiction disappears.

### C7 · A pattern worth naming

Three assistant-memory claims were checked in two days and **all three failed**: the Phase-5
constraint (C5), `src/` being "empty by rule" (C2 — it is empty by *documentation*, not rule,
and it is not empty), and an unrelated `app.pstally.com` claim in another project.

**No decision required.** Recorded so the weighting is explicit: treat assistant memory as a
lead, never a source. Every claim in §1 above was re-derived from the repository for this
reason.

### C8 · Open engineering defects (already recorded, no decision needed)

D-1 monotonic-clock duration control; D-2 CONTRACT-execution §3 states the start in UTC when it
is EAT. Both in `research/exec-1-recording-defects.md`. D-3 fixed.

---

# 3. Map of the remaining research space

**A survey, not a recommendation, and not an audited prior-art review** (see C4). "Established"
below means *I believe it is well covered in the literature*; it has not been through the
process the prior-art map applied to cognitive architecture.

Throughout: **observation** = measuring what is the case; **prediction** = claiming what will
be. Genesis is demonstrably strong at the first and has, so far, measured mostly that the
second fails.

## A · Price / return structure

| | |
|---|---|
| **Can already measure** | variance ratios at any horizon, per-year; realised volatility; HAR-RV walk-forward; autocorrelation; scaling exponents. Machinery built and tested. |
| **Additional data needed** | none for more of the same. For ≥4 h: *more instruments or more conditions*, not more history. |
| **Already ruled out** | 15 m–60 m reversion is real but **below the cost floor** and has decayed to ~0.5 se. 5 m should not be cited. Direction at daily horizon: OOS R² −0.0037. |
| **Novel vs established** | **Established.** Lo–MacKinlay (1988), Poterba–Summers, Corsi (2009). Genesis reproduced HAR-RV to four decimals. The *decay measurement* across 2019–2026 is mildly novel as description, and is descriptive only. |
| **Horizon** | 15 m–1 d |
| **Testable without fishing** | Only by pre-registering horizon, year and estimator before looking — which is what MEASURE-1 already did. Re-running it invites the multiple-comparison problem with no new information. |

**The hard boundary:** the ≥4 h question cannot be settled here at all. 68 years needed. Any
progress must come from B, C, D or E.

## B · Market microstructure

| | |
|---|---|
| **Can already measure** | full book at 500 ms with validated completeness labels; spread, depth, resilience of *quoted* liquidity; adverse selection after a hypothetical fill (39.07% at 60 s); fill ambiguity brackets. |
| **Additional data needed** | **the trade stream (`aggTrade`)** — the single most valuable missing input. Without it there is no order flow, no signed volume, no trade-to-book causality, and fills are inferred rather than observed. Cheap to add: same venue, same recorder, one more subscription. |
| **Already ruled out** | tick-distance as an economic variable on BTCUSDT (0–5 ticks = 0.0079 bps). Latency 291→650 ms as testable at 300 s TTL. Queue position (structurally unrepresentable). |
| **Novel vs established** | order-book imbalance → short-horizon return is **well established** (Cont–Kukanov–Stoikov 2014). Adverse-selection measurement is standard. **Less established:** using book state to forecast *book state* — liquidity and adverse-selection conditions rather than price. |
| **Horizon** | seconds to minutes |
| **Testable without fishing** | strongly. The targets are observable quantities with no free parameters, and the cost floor does not gate them, because they inform *execution* rather than direction. |

**This is the only branch where Genesis's unique asset — its own validated recording — is
load-bearing rather than incidental.**

## C · External information

| | |
|---|---|
| **Can already measure** | funding only. 7,212 periods, decayed 30.6% → 1.94%, one third at the venue default. |
| **Additional data needed** | everything. News feeds (timestamped to sub-second, which is the hard part), macro calendars, sentiment, on-chain. All new ingestion, all with provenance problems Genesis currently solves for one venue only. |
| **Already ruled out** | funding carry as a standalone at retail cost: 56 days to earn back the round trip, while carrying liquidation risk. |
| **Novel vs established** | news → price is **heavily researched and crowded**. On-chain is younger but crowded. Sentiment is saturated. |
| **Horizon** | event-driven; minutes to days |
| **Testable without fishing** | **hardest of the five.** Event studies have large researcher-degrees-of-freedom: which events, which window, which control. Would need the strictest pre-registration Genesis has yet written. |

**Honest note:** this is the branch you flagged as untouched, and it is — but "untouched by
Genesis" and "untouched by the literature" are very different, and here they diverge sharply.

## D · Cross-sectional / relative value

| | |
|---|---|
| **Can already measure** | breadth machinery built and tested (`market/breadth.py`, 11 checks). Directional breadth **1.77–2.98, no trend over 5.5 years**. Residual breadth ~22 → ~17, mean residual correlation −0.031. |
| **Additional data needed** | none to start — public archives already ingested. Later: borrow costs and per-instrument fees, which differ across the cross-section and will matter. |
| **Already ruled out** | naive multi-coin holding as diversification: 30 perps ≈ 2 bets, consistently. |
| **Novel vs established** | the *method* is established (Fama–French, statistical arbitrage, Grinold). The *crypto cross-section measured this way, with breadth stability tracked per half-year* is less covered. Still: normal research, not a founding contribution. |
| **Horizon** | 4 h and up — **above the cost floor**, which no other branch in A manages. |
| **Testable without fishing** | moderate risk. Cross-sectional searches are where multiple comparisons kill people. Mitigated by: fixed universe (already done — 28 perps held constant), pre-registered ranking variable, and the ledger. |

**MEASURE-1 §8 names this branch explicitly as one of the three escapes from the 68-year
boundary.** It is the only branch the repository itself points at.

**Caveats already in the repo, not to be forgotten:** 24.06 is an *upper bound*; the window was
one year; survivorship bias is flagged (28 perps that existed in 2021 *and* still exist).

## E · Market state / regime

| | |
|---|---|
| **Can already measure** | volatility regime (HAR-RV residuals); PC1 share over time (62% → 74.8% → 65%); funding regime; the recorder's own completeness state. |
| **Additional data needed** | none beyond A and D. |
| **Already ruled out** | nothing — untested. |
| **Novel vs established** | **established** (Hamilton regime-switching, Ang–Timmermann). Genesis has no special angle. |
| **Horizon** | days to months |
| **Testable without fishing** | poor. Regime models have many specification choices and a strong tendency to fit the past. High risk. |

## The prediction / observation distinction, and your question

You asked whether the market contains information about its own future state that can be
extracted without rediscovering well-known effects.

What the repository already implies:

1. **It obviously contains some** — volatility is predictable at R² 0.26–0.39 out of sample,
   every year, and funding was structurally positive 85.7% of the time. Neither is novel.
2. **Direction is the part that isn't there**, at least linearly and at affordable horizons:
   OOS R² −0.0037, and the structure that does exist sits below the cost floor.
3. **The genuinely under-worked intersection is B**: using the book's present state to say
   something about the book's *near-future state* — where liquidity will be, what adverse
   selection is about to cost — rather than where price will go.

That third is closest to **observation extended slightly forward in time**, rather than
prediction proper. It is also the only target where being *wrong* is cheap and measurable
immediately, and where Genesis's validated completeness labels do real work rather than
decorating a return series.

---

# 4. Three candidates

Ranked on your five axes. **None is recommended as a decision — the choice is yours, and C4
should probably be resolved first.**

| | **D1 · Book-state → near-future book-state** | **D2 · Cross-sectional residual structure** | **D3 · Volatility at affordable horizons** |
|---|---|---|---|
| **Question** | Does the book's present state carry information about liquidity and adverse-selection conditions seconds-to-minutes ahead? | Does the residual (market-factor-removed) cross-section carry structure at ≥4 h? | Is volatility predictability tradeable after costs at ≥4 h? |
| **Scientific value** | **Moderate–high.** Book→price is crowded; book→*book* is less so. | Moderate. Established method, less-established market. | **Low.** HAR-RV is the standard baseline; reproducing it is not a finding. |
| **Economic relevance** | **High.** Execution is where the one measured edge lives (1.83 bps). | **High.** The only branch above the cost floor with measured room (~17 bets). | Moderate. Requires an instrument to trade volatility; none is in scope. |
| **Data availability** | Good, **after one addition**: the `aggTrade` stream. Same venue, same recorder. | **Best.** Already ingested, machinery built and tested. | Best. Already ingested. |
| **Statistical power** | **Highest.** Millions of book updates; effects at second scale; no 68-year problem. | Good: N instruments × time. Constrained by survivorship and a 5.5-year window. | Moderate: daily observations only. |
| **Risk of fooling ourselves** | **Lowest.** Targets are observable and verifiable within minutes; no return series to overfit; wrong answers surface immediately. | **Highest.** Cross-sectional search is the classic multiple-comparison trap. Needs the fixed universe, a pre-registered ranking variable, and hard family accounting. | Low–moderate. One well-specified baseline, walk-forward already the norm. |
| **What kills it** | If book state adds nothing beyond current spread and depth, that is a clean, publishable null within weeks. | If residual breadth keeps falling, the room closes on its own. | Already nearly dead scientifically; only economics could justify it. |

**If I had to say something.** D1 is the only one that uses what makes Genesis unusual — a
recording it validated itself, with a label proven to carry information — and it is the only
one where the failure mode is a fast, honest null rather than a slow, seductive backtest. D2 is
the one the repository itself points at, and it is also where this project is most likely to
fool itself. D3 is the safest and the least interesting.

That is a reading, not a decision. Nothing here is adopted.
