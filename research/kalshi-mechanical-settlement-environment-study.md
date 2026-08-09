# Kalshi Mechanically-Settled Price Markets — Environment Study

**Date:** 2026-08-09
**Status:** **CLOSED.** Investigation complete. A factual finding, not a direction decision.
**Classification:** environment study under
[`decisions/0003-engineering-posture-real-data.md`](decisions/0003-engineering-posture-real-data.md).
Not an experiment. Nothing was built, modelled, traded, or run. No dataset was downloaded; one
public methodology PDF was fetched and read as a primary source.
**Companion studies:** [`nem-battery-environment-study.md`](nem-battery-environment-study.md);
the prediction-market lifecycle traces recorded in the session record.

---

## 1. Executive finding

**The hypothesis survives the test that killed the battery, and fails a different one.**

The battery died because Genesis would have had to **author the world's state transition** —
state of charge was unpublished, so its evolution needed invented parameters. Polymarket died
because the **consequence was voted on** and the **rules were mutable**.

Neither failure recurs here. The world's state transition is computed by an FCA-authorised
benchmark administrator under a **published, versioned, dated methodology**, and the settlement
formula is a fixed arithmetic average. **Genesis would author no dynamics and no consequence.**

It fails instead on **access and historical record**:

1. **Kalshi's official API does not publish historical order-book snapshots** — only trades and
   candlesticks. Historical depth exists only as third-party *sampled reconstructions*, the
   earliest beginning **2026-01-07**, one of which is already being deprecated.
2. **The settlement reference's historical values are licence-gated.** CF Benchmarks requires a
   commercial licence and per-stream authorisation for `STREAM_HISTORICAL_VALUES`. Genesis
   cannot independently reproduce a settlement without buying access.

So the information set at each historical decision point **was never publicly recorded**, and
the consequence **cannot be independently verified**. That is a different and structurally
better failure than the previous two — it is a failure of *availability*, not of *authorship* —
but for historical reconstruction it is decisive.

## 2. Concrete market investigated

**[FACT]** `KXBTC15M` — "Bitcoin price up/down", 15-minute cadence. Kalshi also lists hourly,
daily, weekly, monthly and yearly Bitcoin contracts.
*Example instance observed:* `kxbtc15m-26jun161400`.

**[FACT]** *"All crypto market contracts are settled by averaging 60 seconds of CF Benchmarks
Real-Time Indexes (RTIs), which report a price once per second."* In the final 60 seconds before
close the relevant RTI is sampled once per second — approximately 60 prints — averaged into a
single settlement value.

**[FACT]** *"15-minute, hourly, daily, weekly, monthly, and yearly bitcoin contracts all settle
on a 60-second average of the CF Benchmarks Bitcoin Real-Time Index. The cadence changes; the
reference rate does not."*

**[FACT]** Contract terms and named Source Agencies are filed with the CFTC under
self-certification. The Kalshi rulebook is versioned (`Version: [1.18]` on a July 2025 filing)
and publicly available through the CFTC portal with dated submissions.

**What this proves:** the settlement formula is fixed, arithmetic, and publicly stated.
**What it does not prove:** that the terms for *this specific market instance at its trading
time* are retrievable at market-level granularity — see §8.

## 3. Lifecycle trace

| Stage | Mechanism | Classification |
|---|---|---|
| Contract creation | Terms + Source Agency self-certified to CFTC | FOUND (class granularity), UNKNOWN (per-market) |
| Trading | Public API: order book, depth, trade prints, candlesticks, per-market maker/taker fees — **live only** | FOUND live, **not FOUND historically** for depth |
| Close | Fixed expiration timestamp | FOUND |
| Measurement | BRTI sampled 1/second for final 60s | FOUND-in-principle, **licence-gated in practice** |
| Settlement | Arithmetic mean of ~60 prints → $1 / $0 | **DERIVED** — no venue judgment in the formula |
| Payout | Fully collateralised binary payout | DERIVED |

## 4. Information-set reconstruction

**[FACT]** *"Kalshi's public API doesn't expose historical order book snapshots — only trades and
candles."* Kalshi's official API serves live trading and current state.

**[FACT]** Historical depth is available only from third parties that **poll the live book and
persist snapshots**:
- Predexon — historical order-book snapshots **from 2026-01-07**; the endpoint *"will be
  deprecated soon."*
- KalshiBackTest — continuously polls the live book, sub-second snapshot resolution, free tier
  covering BTC/ETH/SOL/DOGE/XRP 15-minute markets.
- DepthFeed — polls the public REST order book *"roughly every 1.5 seconds"* across seven crypto
  assets on 15-minute and daily series.

**[INTERPRETATION]** Three consequences, and they compound:

1. **Historical depth is not a venue record.** It is a sampled reconstruction by a third party,
   with the sampling cadence as its resolution limit. A ~1.5-second poll is not an event stream:
   between polls, the book's evolution is unobserved.
2. **Coverage begins in 2026 at the earliest.** For any earlier period the information set at
   time *t* does not exist anywhere and cannot be recovered. This is not a gap in searching; the
   data was never recorded.
3. **Queue position is never recoverable**, at any cadence, from snapshot data.

**The leakage channel, identified.** The most dangerous available shortcut would be to read a
market's *current* description page, metadata, or settlement value and apply it to a decision at
time *t*. Kalshi's live API returns current state by construction, so any reconstruction that
reads "the market" rather than "the market as recorded at *t*" imports post-*t* information.
Distinct from Polymarket's failure: there the rules themselves changed; here the risk is that
the tooling only offers a present-tense view.

## 5. Settlement-reference reconstruction

This is the load-bearing component and it was traced to primary source: *CME CF Cryptocurrency
Real Time Indices Methodology Guide*, **Version 16.8, dated 29 June 2026**.

> *Method note: the PDF is glyph-positioned; text was extracted and inter-character spacing
> removed. Wording below is exact; whitespace was reconstructed.*

**[FACT] Construction.** RTIs are *"calculated in real time based on the Relevant Order Books of
all Constituent Exchanges"* — consolidated order books, quality-screened, with a weighted
mid-price derived through price-volume curves. Dissemination is once per second, top-of-second,
every day of the year.

**[FACT] Contingency rules (Section 5).** The document defines: 5.1 Delayed Data, 5.2 Erroneous
Data (5.2.1 Erroneous Books, 5.2.2 Erroneous Prices), 5.3 Potentially Erroneous Data, 5.4 Expert
Judgement, 5.5 Calculation Failure.

**[FACT] The index carries internal state.** Under 5.3, an exchange whose mid-price deviates from
the cross-exchange median beyond the Potentially Erroneous Data Parameter is disregarded — and
*"shall continue to be disregarded from the calculation of the affected index until the absolute
deviation … is less than 50% of the Potentially Erroneous Data Parameter."* That is a hysteretic,
path-dependent exclusion rule.

**[INTERPRETATION]** The index is therefore **not a pure function of the current world state**.
Reproducing a historical BRTI print would require the constituent order books *and* the
exclusion state carried in from prior seconds.

**[FACT] Discretion exists, and its governing policy is not public.** Section 5.4: *"The
Administrator does not utilise expert judgment in the day to day calculation of the Reference
Rates. In extraordinary circumstances Expert Judgement may be exercised by the Administrator in
accordance with its codified policies and processes which are available upon request."*

**What this proves:** day-to-day calculation is mechanical. **What it does not prove:** that
every historical print was mechanical — the extraordinary-circumstances channel exists and its
codified policy is available only on request, i.e. not publicly documented.

**[FACT] Calculation failure is defined**, occurring when all constituent books exceed the
Retrieval Lag Threshold or are all flagged erroneous / potentially erroneous.

**[INFERENCE, not FACT]** No clause providing for **restatement, revision, recalculation or
republication** of already-published values was found in the document. This is consistent with
published prints being final, but **absence of a clause is weak evidence** and should not be
treated as an immutability guarantee.

**[FACT] Historical values are licence-gated.** The CF Benchmarks REST historical-values endpoint
requires an API key *"obtained by contacting CF Benchmarks for a license"*, and *"the user has to
be authorized for the index and the `STREAM_HISTORICAL_VALUES` data stream."* Free access to
historical values is not available.

**[INTERPRETATION]** The desired structure — world → external measurement → deterministic formula
→ settlement — **is genuinely the structure**. But Genesis cannot *verify* the middle term
without a commercial licence. Settlement would have to be taken on the venue's word.

**[FACT] A design property with direct bearing on this environment.** The methodology states that
by relying solely on order-book data, the RTIs are *"both a Markov process and a martingale"*,
and that *"the martingale property implies that the best prediction of the next CME CF
Cryptocurrency Real Time Index value is its current value"*, making them *"useful for
applications that require an unbiased estimator of the future price."*

**What this proves:** the administrator explicitly designs the reference so its own history
carries no predictive signal about its next value. **What it does not prove:** that realised
BRTI data is a martingale, nor anything about whether the *market price* of a contract is
efficient — those are separate empirical questions. Recorded because it is a stated property of
the thing any decision here would be decided against.

## 6. State-transition analysis

**[INTERPRETATION]** The proposed identity holds, and this is the environment's strongest
property:

```
position(t+1) = position(t) + filled_quantity
cash(t+1)     = cash(t) − price × filled_quantity − fees
```

Contracts are binary and **fully collateralised** — maximum loss equals premium paid — so there
is no margin call, no variation margin, no financing, no carry, no roll, no dividend, no
corporate action, and no decay parameter. Settlement is terminal at $1 or $0.

**Hidden-state search — what was looked for and what was found:**

| Candidate hidden state | Finding |
|---|---|
| Margin / collateral | None beyond full collateralisation — DERIVED |
| Financing / carry | Does not exist for this instrument |
| Contract expiration | Fixed, published — FOUND |
| Fees | Per-market maker/taker rates returned by the API — FOUND **live**; historical fee schedule **UNKNOWN** |
| Position limits | Exist under CFTC regime — a constraint on action, **historical values UNKNOWN** |
| Settlement adjustments | Fee refunds on disputed settlements exist as a standing policy — ASSUMED |

**Conclusion: agent state is accounting-derived, with no authored physics.** This is the exact
thing the battery could not offer. The two residual unknowns — historical fee schedule and
historical position limits — are record-availability questions, not dynamics questions.

## 7. Execution analysis

Separating the two cases as required.

**A. Actual historical fills** — FOUND. Trade prints are served by the official API and carry
price, size and timestamp.

**B. Counterfactual order fills** — **ASSUMED, and the evidence does not currently support
defensible bounds for the historical period.**

Reasoning:
- Bounding a counterfactual fill requires depth at the decision instant. Kalshi does not publish
  historical depth.
- Third-party depth is *sampled* (≈1.5s in one case; sub-second in another) and begins in 2026.
  Between polls the book is unobserved, so a bound derived from the nearest snapshot is an
  interpolation, not an observation.
- Queue position is unrecoverable from snapshots at any cadence, so even a marketable-order
  assumption cannot be verified against what was actually resting.

**[INTERPRETATION]** For markets covered by a sub-second third-party feed, *approximate* bounds
on marketable orders capped at observed resting size are arguably defensible and would need to be
declared as an assumption. For anything outside that coverage — which is all history before 2026
— no bound is supportable at all. I will not claim a hypothetical order "would have filled."

## 8. Historical rules / version analysis

**Kalshi side.** **[FACT]** The rulebook is versioned and filed publicly with the CFTC with dated
submissions. **[FACT]** In July 2026 the CFTC directed Kalshi and Polymarket to **stop bundling
event contracts into broad self-certification templates**, requiring class certification or
slower pre-clearance instead.

**[INTERPRETATION]** The second fact bears directly on retrievability: if historical contracts
were certified under blanket templates, the public filing record may be **coarser than one dated
document per market**. Whether the terms of a *specific historical `KXBTC15M` instance* can be
recovered exactly as they stood at its trading time is **UNKNOWN**.

**Reference side.** **[FACT]** The methodology document contains a complete dated version
history from v1.0 (10 November 2016) to v16.8 (29 June 2026), several entries carrying explicit
effective timestamps — e.g. v2.0: *"Effective: 18 March 2017, 16:30:00 London time."*

**[INTERPRETATION]** This is a genuinely excellent property and better than anything in the NEM
study: the settlement reference publishes its own structural-break log with dates.

## 9. Structural breaks

Dated from the primary-source version history. All are detectable and normalisable **because the
dates are published**.

| Date | Version | Change |
|---|---|---|
| 2017-03-18 | 2.0 | Static → dynamic depth (explicit effective time) |
| 2019-12-02 | 7.0 | Order size cap static → dynamic |
| 2020-02-10 | 8.0 | Potentially-erroneous-data parameter changed |
| 2020-07-31 | 10.0 | Expert Judgement and Methodology Review sections **added** |
| 2020-09-14 | 11.0 | Implementation of Potentially Erroneous Data Parameter changed |
| 2024-02-08 | 15.6 | Definition of Retrieval Time updated |
| 2024-06-11 | 15.7 | Potentially Erroneous Data Parameter 10% → 5% |
| **2026-05-18** | **16.6** | **Effective Time and Retrieval Lag Threshold updated for BRTI** (and ETHUSDRTI, SOLUSDRTI, XRPUSDRTI) |
| 2026-06-08 | 16.7 | Index spacing parameter → Dynamic across all indices |
| 2026-06-29 | 16.8 | Current version |

**[INTERPRETATION]** The 2026-05-18 change is material and recent: it altered BRTI's own timing
parameters three months before this study. Note also that Expert Judgement did not exist as a
documented provision before 2020-07-31.

Non-methodology breaks: Kalshi API changes (changelog exists, not audited here); fee-schedule
changes (UNKNOWN); the July 2026 CFTC filing-practice directive; regulatory changes around
prediction markets generally.

## 10. Component ledger

| Component | Class | Note |
|---|---|---|
| **Environment dynamics** | | |
| BRTI construction methodology | **FOUND** | Published, versioned, dated |
| BRTI historical values | **UNKNOWN to Genesis** | Licence-gated |
| Index internal exclusion state | FOUND (rule) / UNKNOWN (values) | Hysteretic per §5.3 |
| Constituent exchange order books | Not public at index granularity | — |
| **Consequence calculation** | | |
| Settlement formula (60s mean) | **DERIVED** | Fixed arithmetic, no venue judgment |
| Settlement value | DERIVED **from an unverifiable input** | Cannot reproduce without licence |
| Administrator discretion | **ASSUMED** | §5.4, policies "available upon request" |
| Venue discretion (voids, carveouts) | **ASSUMED** | Demonstrated elsewhere on Kalshi |
| **Agent interaction / execution** | | |
| Position & cash | **DERIVED** | Exact accounting identity |
| Trades | FOUND | Official API |
| Historical order-book depth | **not FOUND** | Third-party sampled, 2026+ only |
| Counterfactual fill | **ASSUMED** | Bounds unsupportable pre-2026 |
| Fees (live) | FOUND | Per-market via API |
| Fees (historical) | **UNKNOWN** | — |
| Position limits (historical) | **UNKNOWN** | — |
| Per-market historical contract terms | **UNKNOWN** | Blanket-filing granularity issue |
| Other participants' actions | **not available** | No counterparty data |

## 11. Failure-mode analysis

Actively attempting to kill the environment:

- **Benchmark revisions** — no restatement clause found, but absence is not proof. **UNKNOWN.**
- **Missing historical order books** — **CONFIRMED KILL** for pre-2026 reconstruction. Not
  recoverable by any means; the data was never published.
- **Missing historical contract terms** — **UNKNOWN**, aggravated by blanket self-certification.
- **Hidden settlement discretion** — **CONFIRMED PRESENT** at two levels: administrator Expert
  Judgement (policy not public) and venue void/carveout powers.
- **Timestamps that do not represent information availability** — **CONFIRMED RISK.** Third-party
  snapshot timestamps record when a *poller observed* the book, not when the book changed.
- **Retrospective fee changes** — **UNKNOWN**; a standing fee-refund policy for disputed
  settlements exists, which is a retrospective adjustment by construction.
- **Unavailable historical depth** — **CONFIRMED** (as above).
- **Look-ahead channel** — **CONFIRMED**: live-only API means present-tense metadata is the
  default view, and using it for a decision at *t* imports future information.
- **Reflexivity** — low at small size; not investigated further.
- **Paper vs real money** — execution assumption is removable only by real orders.

## 12. What remains UNKNOWN

1. Whether historical per-market contract terms are retrievable at market-level granularity from
   CFTC filings for the relevant period.
2. Whether published BRTI values are ever restated, corrected or republished.
3. The contents of CF Benchmarks' codified Expert Judgement policy (available on request only).
4. Kalshi's historical fee schedule and historical position limits.
5. Whether any third-party depth archive extends earlier than 2026-01-07.
6. Whether a BRTI licence would grant per-second historical values at the exact granularity the
   settlement formula consumes.

## 13. Verdict

**NO — for historical reconstruction. And the rubric's label does not fit the reason, which is
itself the finding.**

The rubric defines NO as *"environment dynamics or consequence must be authored."* **That is not
what happened here.** For the first time across three environment studies:

- Genesis would author **no environment dynamics.** BRTI is computed by a regulated third party
  under a published, versioned methodology with a dated change log.
- Genesis would author **no consequence.** The settlement formula is a fixed arithmetic mean.
- Agent state is **exactly accounting-derived.** No physics, no efficiency, no initial condition.

The authorship test passes. What fails is **record and access**:

1. The information set at each historical decision point **was never publicly recorded** —
   Kalshi does not publish historical depth, and third-party reconstructions are sampled and
   begin in 2026.
2. The settlement reference's historical values are **licence-gated**, so the consequence cannot
   be independently reproduced.
3. Residual **discretion** exists at both the administrator and venue levels, and one governing
   policy is not public.

So a *historical* reconstruction is not possible without importing information that was never
available, or paying for access and taking parts on trust. The answer to the central question as
asked is **no**.

**The distinction that matters, recorded plainly:** the battery failed because the world would
have had to be invented. This fails because the world was real, computed by someone else, and
**not written down where Genesis can see it**. Those are different problems. The first cannot be
fixed. The second is a question of what was recorded, by whom, and from when — and its character
changes entirely depending on whether one is looking backward or forward.

**This study does not select, reject, or propose anything**, and deliberately does not follow
that last observation anywhere.

## 14. Sources

**Primary.** *CME CF Cryptocurrency Real Time Indices Methodology Guide*, v16.8, 29 June 2026 —
[docs.cfbenchmarks.com](https://docs.cfbenchmarks.com/CME%20CF%20Real%20Time%20Indices%20Methodology.pdf)
(§5.1–5.5, §8, version history). CF Benchmarks REST API historical-values documentation —
[docs.cfbenchmarks.com/api/rest/historical-values](https://docs.cfbenchmarks.com/api/rest/historical-values/).
BRTI index page — [cfbenchmarks.com/data/indices/BRTI](https://www.cfbenchmarks.com/data/indices/BRTI).
KalshiEX LLC Rulebook v1.18, CFTC filing —
[cftc.gov](https://www.cftc.gov/sites/default/files/filings/orgrules/25/07/rules07012525155.pdf).
KalshiEX product filings, January 2025 —
[cftc.gov](https://www.cftc.gov/sites/default/files/filings/ptc/25/01/ptc01222514045.pdf).
Kalshi crypto markets help —
[help.kalshi.com](https://help.kalshi.com/en/articles/13823838-crypto-markets).
Market instance observed — [kalshi.com/markets/kxbtc15m](https://kalshi.com/markets/kxbtc15m/bitcoin-price-up-down/kxbtc15m-26jun161400).

**Secondary (locating and corroborating).**
[Kalshi settlement mechanics](https://predictionmarketspicks.com/articles/how-kalshi-settles-bitcoin) ·
[KXBTC15M 60-second averaging](https://predictionmarketspicks.com/articles/kalshi-bitcoin-15-minute-markets) ·
[Kalshi settlement sources](https://kalshibacktest.com/resources/what-is-kalshi-settlement-source) ·
[Kalshi launch on CF Benchmarks index](https://predictionnews.com/story/kalshi-lists-bitcoin-price-up-down-market-using-cf-benchmarks-index-fbe564e1) ·
[Predexon Kalshi order-book history](https://docs.predexon.com/api-reference/kalshi/orderbooks) ·
[KalshiBackTest historical order book](https://kalshibacktest.com/) ·
[DepthFeed polling cadence](https://depthfeed.com/docs) ·
[CFTC directive on blanket filings](https://www.cryptotimes.io/2026/07/27/cftc-tells-kalshi-polymarket-to-stop-blanket-filings/) ·
[CME BRTI methodology guide v2](https://www.cmegroup.com/trading/files/bitcoin-real-time-index-methodology-version-2.pdf)
