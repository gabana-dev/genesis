# Contract — Book Agreement Validation (BAV-1)

**Status:** **PRE-REGISTERED, revision 2. No implementation exists.** Written before any code,
any run, and any sight of a result.
**Classification:** engineering validation under
[`../research/decisions/0003-engineering-posture-real-data.md`](../research/decisions/0003-engineering-posture-real-data.md).
**Import + build. No novelty claimed. Not a research experiment.**

> **Standing restriction, per the researcher, 2026-08-09.** If the resulting data has
> implications for hypothesis `0001 · Quality of Knowing`, those implications are recorded
> **separately, as observations**. This contract does **not** test 0001, and nothing here may
> be described as testing it, or used to modify it, unless a separate decision record
> authorises that.

---

## 1. The two questions

The recorder makes claims — *"the book at time T is this"*, *"complete"*, *"incomplete"*.
**Nothing has ever checked whether any of them were true.**

**Question A — boundary detection.** When stream continuity is broken, does the recorder
correctly enter an incomplete state and remain there until a fresh valid anchor is
established?

**Question B — fidelity association.** Does the recorder's `complete` / `incomplete` status
correspond to differences in agreement with an independent REST-channel observation?

Two distinct questions. The first validates replay and reconstruction; the second tests
whether the recorder's completeness status is load-bearing or decorative. **They are reported
separately and never collapsed into one claim.** A recorder can correctly detect an
uncertainty boundary even if the resulting `incomplete` label does not predict poor agreement.
Both results are informative.

## 2. Design

```
live Binance WebSocket recording
        ↓
randomly timed REST comparison probes during recording
        ↓
REST response preserved as evidence in the same log
        ↓
offline replay of the WebSocket-derived book
        ↓
comparison against the REST observation
        ↓
Question A and Question B, reported separately
```

1. At pseudorandom moments during a live recording, fetch an **independent REST-channel
   snapshot** (§4).
2. Record it in the same log as an observation, tagged as a comparison probe.
3. Later, offline, replay the WebSocket-derived book at the probe's `response_received_at`.
4. Compare.

**Probes are fetched during recording, not after.** Fetching later would compare a replayed
past against a present book, which is not a comparison at all.

## 3. ANTI-CIRCULARITY — binding

> **Comparison-probe observations are evidence only. They are excluded from the WebSocket book
> reconstruction path and cannot influence the replayed book used in the comparison.**

The replayed book is reconstructed **exclusively** from WebSocket-derived evidence: the
`depthSnapshot` anchors fetched by the recorder's own reconnection procedure, and the
`depthUpdate` stream. A comparison probe's payload never enters that reconstruction.

Probes are therefore recorded with a distinct marker (`probe_id` present) and the replay path
must exclude any observation carrying one. Without this the comparison could measure REST
against itself.

## 4. REST is not ground truth

The REST response is **independent of the WebSocket recorder path** — a different endpoint, a
different transport, a different code path. It is **not independent of Binance**.

> **This experiment validates consistency between two Binance-delivered representations. It
> does not establish that either representation is a ground-truth representation of the
> underlying market.**

Both channels could be wrong in the same way, and this design cannot detect that. The limit is
inherent, not a defect of the method. The term "independent snapshot" is avoided throughout in
favour of **independent REST-channel snapshot**.

## 5. Comparison timing and its uncertainty

- Replay is **always** evaluated at `response_received_at`. This is a **pre-committed
  comparison boundary**, fixed here, before implementation.
- It is chosen because it is the latest moment Genesis can claim knowledge of, which removes
  any freedom to select a favourable offset after seeing results.
- **The REST endpoint does not expose the exact server-side instant its snapshot represents.**
  The interval `request_sent_at → response_received_at` is therefore an **uncertainty interval
  around the REST observation**, not a measurement of it.
- **Do not infer that the REST book represents the exact state at `response_received_at`.** It
  represents some instant within that interval, unknown to us.
- **No post-hoc timestamp alignment procedure is permitted.** The comparison timestamp is fixed
  by this document.

`skew_ms = response_received_at − request_sent_at`. Trials are stratified by skew and reported
in buckets: `<100ms`, `100–300ms`, `300–1000ms`, `>1000ms`.

**Trials with `skew_ms > 2000` are excluded**, recorded as excluded with the reason, and
counted. Threshold fixed now.

Skew is expected to degrade agreement. **A skew–agreement relationship is not a finding about
the recorder** — it is the confound behaving as predicted. Question B is answered only after
conditioning on skew.

## 6. The comparison interval — exact definition

REST exposes a bounded number of levels; the replayed book may contain more. Comparison is
restricted to a price range covered by **both** books, so that REST's truncation is never
measured as recorder disagreement.

Let `Rb`, `Ra` be the REST bid/ask price sets and `Pb`, `Pa` the replay bid/ask price sets,
all after excluding non-positive quantities.

**Bids** (higher price is better):

```
floor_bids   = max( min(Rb), min(Pb) )
interval_bids = { p : p >= floor_bids }
```

**Asks** (lower price is better):

```
ceil_asks    = min( max(Ra), max(Pa) )
interval_asks = { p : p <= ceil_asks }
```

The interval is bounded only on the **truncated** side. The best bid and best ask are always
inside it, so a genuine disagreement at the top of the book is never hidden by the interval.

`A = Rb ∩ interval_bids`, `B = Pb ∩ interval_bids` (and likewise for asks).

**The implementation has no discretion to redefine the interval.**

## 7. Metrics — fixed in advance

All are computed and reported every valid trial, per side. None may be added, removed or
redefined after seeing data.

| # | Metric | Definition |
|---|---|---|
| **M1** | Best-bid/ask agreement | Both books' best bid **and** best ask prices identical. Boolean. Headline for Question A/B reporting. |
| **M2** | Spread agreement | `spread_replay == spread_rest`. Boolean. |
| **M3** | Price-level overlap | `Jaccard(A, B) = |A ∩ B| / |A ∪ B|`, where `A` and `B` are the price-key sets after applying the §6 comparison interval. Per side. |
| **M4** | Relative quantity error | Over prices in `A ∩ B`: median and p95 of `abs(q_replay − q_rest) / q_rest`. Per side. Most diagnostic. |
| **M5** | Exclusive levels | Within the comparison interval, price levels occurring in exactly one book. Reported as **`replay_only`** and **`rest_only`**, kept separate internally; the report may also show their sum. |
| **M6** | Absolute quantity error | **DIAGNOSTIC ONLY.** Over prices in `A ∩ B`: median and p95 of `abs(q_replay − q_rest)`, per side. Distinguishes a large percentage error on a tiny quantity from a small percentage error on a very large one. **Creates no PASS/FAIL criterion.** |

## 8. Probe identity and preserved evidence

Every probe carries a unique identifier, assigned in order: `BAV-001`, `BAV-002`, …

Minimum metadata preserved for every probe, including failed and excluded ones:

```
probe_id
request_sent_at
response_received_at
skew_ms
recorder_status_at_comparison_boundary     (complete | incomplete + reason)
rest_http_status  /  rest_error
replay_comparison_timestamp                (== response_received_at)
probe_outcome_classification               (§10)
raw REST payload, verbatim
```

**The raw REST payload is preserved.** Derived metrics are never the only record — the
observation must remain independently auditable.

## 9. Sampling — reproducible

- Probe intervals are drawn from a **uniform distribution over [20, 60] seconds**.
- Drawn from `random.Random(seed)` — Python's Mersenne Twister, chosen for reproducibility
  rather than statistical quality, which is irrelevant at this sample size.
- **The seed is selected before the run and recorded in the manifest**, inside the hash chain.
- **Probe timing cannot be manually selected after observing the stream.** The full probe
  schedule is a deterministic function of the seed and the run start time.

## 10. Trial classification — fixed now

### 10.1 The three completeness outcomes

Every probe is classified into exactly one of these at the comparison boundary:

| Outcome | Definition |
|---|---|
| **`complete`** | Replay reports `complete: true` at the boundary. |
| **`incomplete_with_book`** | Replay reports `complete: false` **and a replayable book exists** — see §10.2. |
| **`incomplete_no_book`** | Replay reports `complete: false` and **no replayable book exists**. |

**Only `incomplete_with_book` counts toward the required incomplete sample for Question B.**
An absent book cannot disagree with anything, so it carries no fidelity signal.

**`incomplete_no_book` remains valid evidence for Question A** — it shows the recorder
refusing to produce a book it cannot justify — and is **reported separately, never silently
discarded.**

### 10.2 `incomplete_with_book` — exact definition

A **replayable book exists** at the comparison boundary when, after excluding non-positive
quantities:

```
len(book.bids) >= 1  AND  len(book.asks) >= 1
```

Both sides are required because M1 and M2 need a best bid **and** a best ask. A one-sided book
cannot produce them.

`incomplete_with_book` is therefore: `complete == false` **and** a replayable book exists.
This is the **stale-book** case — the recorder holds a book it no longer vouches for — and it
is the only incomplete case in which Question B is answerable.

If `complete == true` but no replayable book exists, the trial is `no_book`, excluded, and
**flagged as a defect report**: the recorder should not claim completeness over an empty book.

### 10.3 Exclusion rules

| Situation | Ruling |
|---|---|
| REST request fails | `probe_failed` + error. Excluded from metrics, counted. **Never retried to obtain a better sample.** |
| REST returns < 100 levels per side | `thin_book`. Excluded from M3/M4/M5/M6, retained for M1/M2. Threshold fixed now. |
| Level in one book only, inside the interval | Counted in M5 (`replay_only` / `rest_only`). **Excluded from M4 and M6** — a missing level has no error, and imputing zero would manufacture agreement or disagreement. |
| Replay returns no book at the boundary | `no_book`. Excluded, counted. |
| Zero or negative quantity in either book | `anomalous`. Excluded from metrics, payload preserved. **This is a defect report, not a data point.** |
| Crossed book (best bid ≥ best ask in either) | `crossed`. Excluded from M1/M2, retained for M3/M4/M6, flagged loudly. |
| Sequence gap between last applied update and boundary | Recorded; falls in the `incomplete` stratum by construction. |

## 11. Natural versus deliberate incompleteness

Incomplete trials are split into two strata that are **never silently combined in reporting**:

- **`natural_incomplete`** — arising from naturally occurring interruptions. Evidence about
  the environment as it actually behaves.
- **`forced_incomplete`** — arising from a deliberate reconnect. Valid experimental
  manipulation that tests the recorder's handling of an **intentionally created information
  boundary**.

Every forced reconnect is recorded with `deliberate: true`; natural reconnects carry
`deliberate: false`. **A forced reconnect presented as a natural one would be fabricated
evidence.**

> **The controlled condition is an engineering manipulation designed to guarantee that the
> recorder is evaluated while its continuity guarantee is intentionally invalidated. It is
> NOT evidence about the natural frequency of incomplete states.** Any statement about how
> often incompleteness occurs may draw only on `deliberate: false` observations.

### 11.1 Required reporting cells

These are reported separately and **never pooled**:

| Cell | Meaning |
|---|---|
| `complete` / natural | The expected majority case |
| `incomplete_with_book` / natural | Naturally occurring stale book |
| `incomplete_with_book` / deliberate | Controlled stale book — the Question B workhorse |
| `incomplete_no_book` / natural | Question A evidence only |
| `incomplete_no_book` / deliberate | Question A evidence only |
| `complete` / deliberate | **Protocol deviation** — a controlled probe that landed outside the incomplete interval. Reported explicitly and counted against the 14. |
| `probe_failed` | With error |
| Other excluded | `thin_book`, `skew_excluded`, `crossed`, `anomalous`, `no_book`, each with counts and reasons |

## 12. Sample size, controlled interruptions, and stopping rule

### 12.1 Sample

- **60 probe slots**, over a single continuous recording of **at least 60 minutes**.
- **Target: 60 valid trials.**
- **Required: ≥ 10 usable incomplete probes**, where *usable* means `incomplete_with_book`
  **and** passing all §10.3 exclusion rules.
- **If fewer than 10 usable incomplete probes are obtained, Question B is classified
  `INSUFFICIENT`, not `INFORMATIVE-NULL`.** Insufficient evidence is never interpreted as
  evidence that complete and incomplete states behave equally.

### 12.2 Why controlled interruptions are required

Natural incompleteness cannot be relied upon. In the 30-minute run of 2026-08-09 the venue
produced **zero** natural interruptions, and the single forced reconnect held an incomplete
interval open for **11.7 seconds**. At 20–60 second probe spacing, a randomly timed probe would
land inside such a window only rarely. Relying on chance would make Question B unanswerable by
construction — the failure this amendment exists to prevent.

### 12.3 The controlled-interruption protocol — fixed before implementation

**14 of the 60 probe slots are designated controlled-interruption probes**, chosen before the
run (§12.4). For each designated slot with scheduled probe time `T`:

| Offset | Action |
|---|---|
| `T − 5s` | Close the WebSocket. Record `RECONNECT_FORCED {deliberate: true}` then `CONNECTION_CLOSED`. **Do not reconnect yet.** |
| `T` | Fire the REST comparison probe. Its boundary falls **5 s into the incomplete interval**. |
| `T + 15s` | Reconnect, re-subscribe, re-anchor via REST. Incomplete interval closes at the new `depthSnapshot`. |

**Dwell = 20 s. Probe offset = 5 s after close.** Both fixed here.

This makes the probe's position inside the incomplete interval **deterministic rather than a
race**. The dwell is held open by the protocol, not by chance, so the boundary cannot fall
after re-anchoring. The 15 s remaining margin is ~1.3× the 11.7 s reconnect duration measured
on 2026-08-09, and the probe's own round trip is bounded by the 2000 ms skew exclusion.

During dwell the replayed book retains all levels applied before the close — so these probes
are expected to yield **`incomplete_with_book`**, the stale-book case Question B needs.

### 12.4 Why 14

Ten usable are required. Fourteen are scheduled to absorb attrition from `probe_failed`,
`thin_book`, `skew_ms > 2000`, `crossed`, and any protocol deviation. Fourteen tolerates
**4 lost probes (29%)** while still meeting the requirement.

**14 is fixed now.** If more than 4 are lost, the result is `INSUFFICIENT` — *additional
controlled interruptions are not added to recover it.*

Cost: 14 × 20 s = **280 s of dwell**, about 8% of a 60-minute run.

### 12.5 Controlled-slot selection — reproducible

- Slots are numbered `1..60`. **Slots 1–5 are warm-up** and are never controlled, so the book
  is well established before the first interruption.
- Slots `6..59` (54 slots) are partitioned into **14 contiguous blocks** of 3–4 slots.
- **One controlled slot is drawn uniformly within each block** using the same seeded
  `random.Random(seed)` as the probe schedule, drawn **before the run**.
- This guarantees controlled probes are spread across the run and never adjacent.
- The complete schedule — probe times and controlled-slot indices — is a **deterministic
  function of the seed and the run start time**, recorded in the manifest.

### 12.6 Stopping rule

**The run is not extended, repeated, or re-sampled after seeing results.** The number and
timing of controlled interruptions are fixed before the run. **Additional controlled
interruptions are not added because an intermediate result looks inconclusive.** If the sample
is insufficient, that is reported as insufficient.

## 13. Acceptance thresholds

> These are **pre-committed engineering acceptance thresholds**. They are not claimed to be
> natural, universal, or scientifically derived boundaries. 95% and 1% are engineering
> choices, fixed in advance so they cannot be selected after seeing the data.

**PASS**, all of:
- ≥ 95% of `complete` trials with `skew_ms < 300` achieve M1
- Median M4 relative quantity error < 1% for `complete`, low-skew trials
- Replay deterministic across repeated evaluation of the same log
- Every excluded trial accounted for in the report

**FAIL**, any of:
- `complete` trials systematically disagree at low skew
- Replay non-deterministic
- Any trial reveals silent repair, defaulting or interpolation of state
- Excluded trials exceed 25% of attempts

### Question B outcomes — mutually exclusive

**`INFORMATIVE-NULL`** — a legitimate result, not a failure. Requires **≥ 10 usable incomplete
probes**. If `complete` and `incomplete_with_book` trials show practically indistinguishable
agreement after stratifying on skew, then:

> the experiment provides no evidence that completeness status predicts fidelity under the
> tested conditions.

Not reinterpreted as failure merely because it does not support the expected direction. It
would mean the status is decorative rather than load-bearing — a real and useful thing to
learn.

**`INSUFFICIENT`** — fewer than 10 usable incomplete probes obtained:

> the required incomplete evidence was not obtained.

**`INSUFFICIENT` is never reinterpreted as `INFORMATIVE-NULL`.** They are different results:
one says the difference was not detectable, the other says the data to look for it was not
collected.

**Statistical honesty, stated in advance.** Ten usable probes do **not** establish a
statistically powerful null. If the requirement is met, the observed difference or relationship
is reported using the pre-registered metrics, with the sample size stated beside it. An
INFORMATIVE-NULL at this sample size means *"no difference was detected at n≈10"*, **not**
*"there is no difference."*

**Question A and Question B are independent.** INFORMATIVE-NULL or INSUFFICIENT on B is fully
compatible with a positive result on A: the recorder may detect boundaries correctly while the
label carries no fidelity signal.

**Scope of a null on the controlled condition.**

> A null result for the controlled incomplete condition is a null result **at the
> pre-registered 5-second staleness interval**. It does not establish that completeness status
> is non-informative at other staleness durations or under naturally occurring interruptions.

The 5-second offset is fixed by §12.3 precisely so it cannot be tuned after seeing results —
but a null obtained at 5 s of staleness is evidence about 5 s of staleness, and nothing wider.

## 14. What this cannot establish

The experiment can support a statement of the form:

> *"The WebSocket-derived reconstruction is consistent (or inconsistent) with Binance's REST
> representation under the tested conditions."*

It **cannot** establish:

- that the reconstructed book is objectively correct
- objective market truth, or correctness outside Binance's own representations
- queue position
- prediction, trading advantage, profitability, decision quality, or real-world economic value
- anything about Kalshi — `recorder/kalshi.py` remains unexecuted
- anything about hypothesis `0001`

**Implementation and reporting language must not drift beyond this.**

## 15. Binding rules

1. The recorder is **not modified** during or after the run to improve results. A defect found
   is recorded first, and any fix invalidates the run for reporting.
2. Metrics, thresholds, exclusions, strata, the comparison interval and the comparison
   timestamp are **fixed by this document**. Adding or redefining any of them after seeing data
   invalidates the run.
3. The full contract and the sampling seed are written into the log as event 0, inside the hash
   chain.
4. Excluded trials are reported with counts and reasons. **Silent exclusion is a FAIL.**
5. No post-hoc sampling, re-running, or trial selection.

## 16. Source

[`SPEC.md`](SPEC.md) invariants 5, 10, 16; the 30-minute live run of 2026-08-09 (commit
`cab4602`); [`../research/decisions/0003-engineering-posture-real-data.md`](../research/decisions/0003-engineering-posture-real-data.md);
Binance published depth reconciliation rules.
