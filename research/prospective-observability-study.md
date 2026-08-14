# Prospective Observability Study

**Date:** 2026-08-09
**Status:** **CLOSED.** Investigation complete. A factual finding, not a direction decision.
**Classification:** environment study under
[`decisions/0003-engineering-posture-real-data.md`](decisions/0003-engineering-posture-real-data.md).
Nothing was built, traded, backtested, paper-traded, or downloaded. No environment is selected.
**Companion studies:** [`nem-battery-environment-study.md`](nem-battery-environment-study.md),
[`kalshi-mechanical-settlement-environment-study.md`](kalshi-mechanical-settlement-environment-study.md).

---

## 1. Executive finding

**YES — with one precisely bounded residual trust.**

The question is whether Genesis can enter an environment prospectively such that the decision →
interaction → externally-determined-consequence loop is captured well enough for a genuinely
auditable evaluation later.

For Kalshi mechanically-settled price markets the answer is yes, and the reason the historical
study said no does not carry over. **Kalshi's live WebSocket API emits a full order-book snapshot
followed by incremental deltas, each carrying a sequence number and an exchange-side
millisecond timestamp.** That is an event stream, not a sample. The third-party 1.5-second
polling that made historical reconstruction impossible is an artefact of nobody having recorded
the stream — not a property of the venue.

What remains is a single, nameable residual: **Genesis can record what it was paid, but cannot
verify that the venue computed the payment correctly** without a commercial data licence for the
settlement reference. That is trust in the venue's arithmetic, not in its record.

## 2. The distinction this study establishes

> **An environment can be historically unreconstructable while being prospectively recordable.**
>
> That is materially different from an environment requiring authored dynamics. Data
> availability and environmental authorship are separate properties, and conflating them
> discards environments that are in fact sound.

Kalshi is the proof case: the *same venue* returns different answers depending on the direction
of time. Looking backward, the information set at time *t* was never recorded and cannot be
recovered. Looking forward, every field needed is emitted live, timestamped and sequenced.

> **Proposed, NOT adopted.** Following the precedent by which DR0002 preserved the
> environment-first gate without promoting it, and by which the NEM study recorded its
> consequence/state observation without elevating it: this principle has now governed two
> decisions (the Kalshi historical verdict, and this one). That is not yet enough to promote it
> into DR0003 or canon, and this document does not.

## 3. The minimum sufficient event log

Specified as a record requirement, not a design. Five streams that must never be collapsed:

```
what the world said → what Genesis knew → what Genesis decided
   → what Genesis requested → what actually happened
```

| Stream | Contents |
|---|---|
| **World** | Raw inbound messages, verbatim, with venue sequence + venue timestamp + local receipt timestamp |
| **Knowledge** | The information set as of a declared decision boundary, derived only from World records whose receipt timestamp precedes it |
| **Decision** | Boundary timestamp, inputs hash, decision, model/version identifier, rationale |
| **Request** | Order submitted: side, size, price, client order id, local submit timestamp |
| **Outcome** | Acknowledgement, fill, partial fill, cancel, reject, settlement, fees — each with venue timestamp |

The load-bearing property is that **Request and Outcome are separate streams**. Collapsing them
is what makes counterfactual and observed execution indistinguishable later.

## 4. Field-by-field capture analysis

### Environment observation

| Field | Class | Evidence |
|---|---|---|
| Order-book state | **FOUND** | `orderbook_snapshot` then incremental `orderbook_delta` |
| Sequence number | **FOUND** | `seq` — *"Sequential number that should be checked if you want to guarantee you received all the messages. Used for snapshot/delta consistency."* |
| Exchange timestamp | **FOUND** | `ts_ms` — *"Unix timestamp for when the orderbook change was recorded"*; `ts` (RFC3339) deprecated |
| Genesis-caused changes | **FOUND** | `client_order_id` present in a delta *"only when you caused the change"* |
| Bid / ask | **FOUND** | `yes_bid_dollars`, `yes_ask_dollars`; book fields `yes_dollars_fp`, `no_dollars_fp` |
| Depth | **FOUND** | `price_dollars`, `delta_fp`, `side` per delta |
| Recent trades | **FOUND** | public `trade` channel |
| Ticker | **FOUND** | public `ticker` channel |
| Market status / lifecycle | **FOUND** | public `market_lifecycle_v2` channel |
| Fees | **FOUND** | per-market maker/taker rates via API; **`Get Series Fee Changes`** and **`Get Event Fee Changes`** endpoints exist |
| Contract terms at timestamp | **DERIVED** | recordable by snapshotting the market record at each boundary; requires Genesis to capture it, nobody preserves it otherwise |
| Expiration | **FOUND** | published contract field |
| Position limits | **UNKNOWN** | not established; `Get Total Resting Order Value` exists |
| Settlement reference values | **UNAVAILABLE without licence** | see §5 |

**[INTERPRETATION]** The fee-changes endpoints are a notable finding: they turn "historical fee
schedule" from the UNKNOWN it was in the Kalshi historical study into something queryable.

### Agent state

| Field | Class |
|---|---|
| Cash, position | **DERIVED** — exact accounting identity from recorded fills and fees |
| Reserved collateral | **DERIVED** — binary contracts are fully collateralised; max loss = premium |
| Realised P&L | **DERIVED** |
| Unrealised P&L | **DERIVED**, but only against a declared marking convention — mark choice is **ASSUMED** |
| Fees paid | **FOUND** — fills and settlement records carry fee fields (`MiscFeeAmt`, `CollateralAmountChange`) |
| Open orders, fills | **FOUND** — private `fill` channel, connection-authenticated |

**No hidden state.** No margin, financing, carry, roll, dividend, corporate action, or decay
parameter exists for this instrument. The battery's failure mode does not recur.

### Decision and interaction

All Genesis-side fields (boundary timestamp, inputs, model identifier, rationale) are **DERIVED**
— Genesis authors them, which is legitimate: they describe the agent, not the world.

Venue-side interaction — acknowledgement, fill, partial fill, cancel, reject — is **FOUND** on the
authenticated channels, though the documentation set I could read does not enumerate reject and
cancel payloads as explicitly as it does fills. **UNKNOWN** at field granularity.

## 5. Settlement reference — investigated separately

**[FACT]** Kalshi's settlement documentation states that *"positions are automatically resolved
and funds transferred"* and that *"markets typically settle shortly after expiration, but timing
can vary based on market type, data source availability, and manual review requirements."*
Settlement records carry `CollateralAmountChange` and `MiscFeeAmt`, summing to the pre-rounding
value.

**[FACT]** The documentation **does not indicate that Kalshi publishes the underlying reference
or index value** used to determine the outcome — only the resulting outcome and payout.

**[FACT]** Verifying settlement therefore requires the CF Benchmarks BRTI values directly. Those
require a licence: all customers must sign a **Market Data License Agreement (MDLA)**, and *"the
creation and distribution of derived works require a separate Derived Data License Agreement."*
CF Benchmarks grants non-exclusive, non-transferable licences, typically one-year initial term
with automatic renewal, covering only the indices scheduled in the agreement.

**Answering the specific questions posed:**

| Question | Finding |
|---|---|
| Historical values obtainable prospectively? | Yes, under licence — `STREAM_HISTORICAL_VALUES` authorisation |
| Commercial licence required? | **Yes** — MDLA |
| Licence permits archival storage? | **UNKNOWN** — not established from public terms |
| Redistribution permitted? | **No, not without a separate Derived Data License Agreement** |
| Can Genesis store the exact one-second observations settlement consumes? | **UNKNOWN** — depends on MDLA terms |
| Can published values be revised? | **UNKNOWN** — no restatement clause found in methodology v16.8, but absence is not proof |
| Can expert judgement alter a value? | **Yes in extraordinary circumstances** — §5.4; codified policies *"available upon request"*, i.e. not public |
| Enough information to independently reproduce a value? | **No.** Reproduction needs constituent-exchange order books *and* the hysteretic exclusion state carried from prior seconds (§5.3) |
| Calculation failure? | Defined — occurs when all books exceed the Retrieval Lag Threshold or are all flagged erroneous |
| Methodology changes communicated? | **Yes, well** — dated version history, some entries with explicit effective times |

### What trust remains, stated exactly

**Genesis cannot independently verify that a settlement was computed correctly.** It can record
what it was paid, when, and under which contract terms. It cannot reproduce the reference value
without a licence, and even with one, cannot fully recompute it from primary inputs because the
index carries internal state and admits expert judgement.

**[INTERPRETATION]** This is a narrower trust than it first sounds. For evaluating a decision
system, the operative consequence is the cash that actually moved — which is externally
determined, externally recorded, and not authored by Genesis. Verifying the administrator's
arithmetic is a strictly stronger claim than evaluating one's own decisions against real
outcomes. But it is a real residual and it should never be described as "settlement is FOUND."

## 6. Execution observability

**Observed execution — FOUND.** For orders Genesis actually submits: the request carries a
`client_order_id`; fills arrive on the authenticated `fill` channel; and the resulting book
change appears in `orderbook_delta` **tagged with that same `client_order_id`**, present *"only
when you caused the change."* So Genesis's own market impact is directly attributable in the
world stream. This is a genuinely strong property.

**Counterfactual execution — remains ASSUMED.** Recording does not solve it. Even with complete
depth and full delta history:

- **Queue position is not exposed.** Nothing in the documented payloads reveals where an order
  sits within a price level, so whether a resting order would have been filled cannot be
  determined from the record.
- Therefore any statement about an order Genesis did **not** place remains an assumption, and
  this study does not claim otherwise.

**[INTERPRETATION]** The asymmetry is the point. Prospective recording converts execution from
"entirely assumed" to "observed for what was actually done, assumed only for what was not." The
irreducible part shrinks to counterfactuals, and only real orders remove it.

## 7. Information-boundary integrity

**[INTERPRETATION]** The boundary must be defined by **local receipt timestamp**, not by venue
timestamp, and not by what a later query returns.

A record qualifies as available at decision boundary *T* only if Genesis received it before *T*.
A message describing an event at *t < T* that arrives after *T* is **not** available at *T*. This
is why `ts_ms` and local receipt time must both be stored: `ts_ms` says when the world changed,
receipt time says when Genesis could have known.

**The leakage channel this closes.** The Polymarket failure was that rules changed after the
fact and no version history existed. The prospective equivalent is querying any REST endpoint
after *T* and treating the response as knowledge at *T*. Recording market records at each
boundary as part of the World stream removes that channel — but only if the evaluation reads the
recorded snapshot rather than re-querying.

**Gap handling.** `seq` makes missed messages **detectable**. The documentation I could read does
not specify a gap-recovery procedure or any delivery guarantee — **UNKNOWN**. The practical
consequence is favourable: a recorder can mark intervals where the record is known-incomplete,
so the evaluation can exclude them rather than silently interpolate. **Known-incomplete is a
usable state; unknowably-incomplete is not.**

## 8. Comparison of candidate prospective environments

Ranked on the criteria given, not on profitability.

| Criterion | Kalshi mech-settled | Crypto spot/perp | Futures | Equities |
|---|---|---|---|---|
| External determination | High — fixed formula, regulated administrator | High | High | High |
| Observability | **High** — snapshot+delta, `seq`, `ts_ms` | High — many venues stream L2/L3 | High (paid feeds) | High (paid feeds) |
| Timestamp fidelity | **High** — exchange ms + local receipt | High | Very high | Very high |
| Prospective recordability | **High** | High | High | High |
| Settlement verifiability | **Low** — licence-gated reference | Medium — venue trade prints are the settlement | High — exchange-published settlement | High |
| Execution observability | High for own orders; queue not exposed | Same limitation | Same | Same |
| Information-boundary integrity | **High** | High | High | Medium — vendor revisions |
| Structural stability | Medium — active regulatory change | Low — venue failure risk | High | High |
| Cost of observation system | **Low** — one WS connection; free tier data exists | Medium | High | High |
| Irreducible assumptions | Queue position; settlement arithmetic | Queue position | Queue position; roll if continuous | Queue position; corporate actions |

**[INTERPRETATION]** Kalshi ranks first on cost, information-boundary integrity and simplicity of
agent state, and **last on settlement verifiability**. Conventional futures invert that: exchange
settlement prices are published, but observation costs are far higher. No candidate is best on
every axis, and the trade is legible rather than hidden.

## 9. What remains UNKNOWN

1. Whether the CF Benchmarks MDLA permits archival storage of per-second values.
2. Whether published BRTI values are ever restated.
3. Gap-recovery procedure and any delivery guarantee on the WebSocket feed.
4. Field-level payloads for order rejections and cancellations.
5. Position limits and how they are exposed.
6. Rate-limit tiers and whether a recorder's subscription volume fits a free or low tier.
7. What "manual review requirements" means in Kalshi's settlement path, and how often it fires.

## 10. Verdict

> **Is there an environment Genesis can enter prospectively where the decision → interaction →
> externally determined consequence loop can be recorded sufficiently to permit a genuinely
> auditable evaluation later?**

**YES.**

**What must be recorded:** the five separated streams of §3 — raw venue messages with `seq`,
`ts_ms` and local receipt time; a boundary-stamped knowledge snapshot including contract terms
and fees; the decision with model identifier and inputs; the submitted order with
`client_order_id`; and every venue-side outcome through settlement. Gaps must be marked from
`seq` discontinuities, never interpolated.

**What remains assumed:**
1. **Counterfactual execution** — queue position is not observable, so claims about orders not
   placed remain assumptions. Only real orders remove this.
2. **Settlement arithmetic** — Genesis records what it was paid; verifying that the venue
   computed it correctly requires a licensed reference feed, and even then cannot be fully
   reproduced from primary inputs.
3. **Marking convention** for unrealised P&L.
4. The seven UNKNOWNs in §9.

**What is *not* assumed, and this is the finding:** no environment dynamics, no consequence
formula, no agent-state physics, and — prospectively — no unreconstructable information set.
This is the first candidate across four studies where all four hold simultaneously.

**This study selects nothing**, proposes no experiment, recommends no strategy, and makes no
claim about profitability. It establishes only that the recording problem is solvable and names
precisely what would remain untrusted if it were solved.

## 11. Sources

**Primary — Kalshi.** [WebSocket quick start](https://docs.kalshi.com/getting_started/quick_start_websockets) ·
[Orderbook updates payloads](https://docs.kalshi.com/websockets/orderbook-updates.md) ·
[Market settlement](https://docs.kalshi.com/getting_started/market_settlement.md) ·
[Documentation index](https://docs.kalshi.com/llms.txt) ·
[User fills](https://docs.kalshi.com/websockets/user-fills.md) ·
[Public trades](https://docs.kalshi.com/websockets/public-trades.md) ·
[Rate limits and tiers](https://docs.kalshi.com/getting_started/rate_limits.md) ·
[Series fee changes](https://docs.kalshi.com/api-reference/exchange/get-series-fee-changes.md) ·
[Get settlements](https://docs.kalshi.com/api-reference/portfolio/get-settlements.md)

**Primary — settlement reference.** *CME CF Cryptocurrency Real Time Indices Methodology Guide*,
v16.8, 29 June 2026 ([PDF](https://docs.cfbenchmarks.com/CME%20CF%20Real%20Time%20Indices%20Methodology.pdf)),
§5.3 hysteretic exclusion, §5.4 Expert Judgement, §5.5 calculation failure, version history ·
[Historical values API](https://docs.cfbenchmarks.com/api/rest/historical-values/) ·
[CME CF benchmarks FAQ — MDLA and Derived Data License](https://www.cmegroup.com/articles/faqs/cme-cf-cryptocurrency-benchmarks-faq.html) ·
[CF Benchmarks licence agreement (filed)](https://contracts.justia.com/companies/valkyrie-bitcoin-fund-11951/contract/1263261/)

**Secondary.** [Kalshi WebSocket channel overview](https://www.parlay.run/kalshi-api) ·
[Kalshi order book API](https://www.quantvps.com/blog/kalshi-order-book-api-endpoints-explained)
