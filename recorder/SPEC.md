# Genesis Prospective Environment Recorder — Specification

**Status:** specification, written before implementation.
**Classification:** engineering under
[`../research/decisions/0003-engineering-posture-real-data.md`](../research/decisions/0003-engineering-posture-real-data.md).
**Import + build. No novelty claimed.**

**Scope: the recorder only.** No strategy, no model, no signal, no backtest, no order
submission, no counterfactual fill simulation, no profitability claim. Those are out of scope by
construction, not by omission.

---

## 1. Purpose

Preserve an auditable record of:

> what the environment showed → what Genesis knew → what Genesis decided → what Genesis
> requested → what actually happened → what was eventually paid.

The recorder's single obligation: **a later evaluation must be able to determine exactly what
Genesis could have known at any decision boundary, and must never be able to mistake a
reconstruction for an observation.**

## 2. The five classes

| Class | Meaning |
|---|---|
| `OBSERVATION` | What Genesis received, wrapping verbatim what the venue reported |
| `DECISION` | What Genesis decided, and on what information |
| `INTENT` | What Genesis requested |
| `EXECUTION` | What actually happened at the venue |
| `RECORDER` | The recorder's own lifecycle, failures and gaps |

### 2.1 A deliberate interpretation — WORLD lives inside OBSERVATION

The task specifies WORLD and OBSERVATION as separate classes. This specification nests WORLD
**inside** OBSERVATION as a separate, never-merged sub-object rather than emitting two events.

Reason: Genesis has no unmediated access to the world. Every world fact it holds exists *because
it observed it*, and an un-observed world event is by definition absent from the log. Emitting a
standalone WORLD event would assert knowledge of the world independent of observing it — which is
the exact epistemic error the record is meant to prevent.

The invariant the task actually requires is preserved and strengthened: `body.world` (verbatim
venue payload, venue sequence, venue timestamp) and `body.observation` (receipt timestamp,
connection, subscription) are distinct objects, never merged, never overwriting each other.

**Flagged for review.** If the intent was two physical event records, this is a one-line change
to the emitter.

## 3. Event envelope

One JSON object per line, append-only:

```json
{
  "event_index":  0,
  "event_id":     "uuid4",
  "event_class":  "OBSERVATION",
  "event_type":   "orderbook_delta",
  "recorded_at":  "2026-08-09T12:00:00.123456+00:00",
  "recorder_run": "uuid4",
  "body":         { },
  "prev_hash":    "0000…",
  "hash":         "sha256…"
}
```

`recorded_at` is the Genesis clock at write time and is **never** a substitute for either the
venue timestamp or the receipt timestamp.

## 4. Bodies

### OBSERVATION

```json
{
  "observation": {
    "received_at":     "RFC3339 with microseconds, Genesis clock",
    "connection_id":   "uuid of the connection that carried it",
    "subscription_id": "venue sid, if present"
  },
  "world": {
    "raw":           { "verbatim venue message, unmodified" },
    "venue_seq":     12345,
    "venue_ts_ms":   1786282117728,
    "market_ticker": "KXBTC15M-…",
    "channel":       "orderbook_delta"
  }
}
```

**`world.raw` is authoritative.** Extracted fields are indexing conveniences and may be `null` if
the venue omits them. Extraction never mutates `raw`.

### DECISION

```json
{
  "boundary_at":     "the declared decision boundary, Genesis clock",
  "model_id":        "identifier",
  "model_version":   "identifier",
  "inputs_hash":     "sha256 over the observation event ids that formed the information set",
  "input_event_ids": ["…"],
  "decision":        { "free-form, model-defined" },
  "rationale":       "optional text"
}
```

### INTENT

```json
{
  "client_order_id": "…", "market_ticker": "…", "side": "yes|no",
  "action": "buy|sell", "count": 20, "price_dollars": "0.43",
  "order_type": "limit|market",
  "decision_event_id": "…",
  "submitted_at": "Genesis clock"
}
```

### EXECUTION

```json
{
  "kind": "ack|reject|fill|partial_fill|cancel|modify|settlement",
  "client_order_id": "…", "order_id": "…", "market_ticker": "…",
  "count": 7, "price_dollars": "0.43", "fee_dollars": "0.02",
  "venue_ts_ms": 1786282117728,
  "received_at": "Genesis clock",
  "raw": { "verbatim venue message" }
}
```

### RECORDER

`RECORDER_STARTED`, `RECORDER_STOPPED`, `CONNECTION_OPENED`, `CONNECTION_CLOSED`,
`SEQUENCE_GAP`, `SUBSCRIPTION_CHANGED`, `MALFORMED_MESSAGE`, `TIMESTAMP_ANOMALY`, `ERROR`.

`SEQUENCE_GAP` body:

```json
{ "channel": "orderbook_delta", "market_ticker": "…",
  "last_seq": 100, "received_seq": 137, "missing_from": 101, "missing_to": 136 }
```

## 5. Invariants

1. **Append-only.** No event is ever modified or deleted.
2. **Two clocks, never merged.** Venue timestamps and Genesis timestamps coexist; neither is
   overwritten or inferred from the other.
3. **Verbatim world.** `world.raw` is stored exactly as received.
4. **Gaps are recorded, never repaired.** On `seq(n+1) != seq(n) + 1` the recorder emits
   `SEQUENCE_GAP` and does **not** synthesise the missing deltas.
5. **Incompleteness is inherited.** Any projection spanning a gap is flagged incomplete until the
   next authoritative `orderbook_snapshot` for that market.
6. **No inference across classes.** EXECUTION is never derived from OBSERVATION. An unfilled
   order is recorded as unfilled, never as a hypothetical fill.
7. **Restart is visible.** Every process start emits `RECORDER_STARTED` with a fresh
   `recorder_run`. Two runs never appear as one continuous observation.
8. **Hash chain.** `hash = sha256(canonical_json(event_without_hash) || prev_hash)`. The first
   event's `prev_hash` is 64 zeros.
9. **Canonical decimals, enforced at ingestion.** Every price **and every quantity** is
   normalised to one decimal string (`Decimal.normalize`, no exponent) and stored in
   `world.canonical` **at ingestion**, beside the verbatim `raw`. `"0.50"`, `"0.5000"` and
   numeric `0.5` are one book key. Replay reads the canonical view, never the raw spelling.

   **Quantities are decimals, not integers.** Live public REST data for `KXBTC15M` returns
   order-book sizes as decimal strings with fractional values — `"0.01"`, `"5.01"`, `"191.00"` —
   under a `tapered_deci_cent` price-level structure with tick steps of `0.0010`. Every
   quantity is therefore carried as `Decimal` through book state, position state, fills and
   settlement, and rendered as a canonical decimal string. **Float is never used for a
   quantity or a price**, and a quantity is never coerced to `int`.

   *Provenance of this rule: the fractional-quantity shape is **observed REST evidence**
   (`orderbook_fp`). The WebSocket shape (`yes_dollars_fp` / `delta_fp`) is **unobserved**; that
   it matches is **inferred** from the shared `_fp` convention, not established. Supporting
   decimals costs nothing if the WS turns out to send integers, so the recorder accepts both.*

   **Zero is always `"0"`.** `-0.00`, `0.00` and `-0.0` collapse to one key; a signed zero
   would otherwise split a level in two.

15. **Validity is by role, not by type.** Sharing a representation does not mean sharing
    validity rules:

    | Role | Sign | Canonicaliser |
    |---|---|---|
    | price — what one unit costs | non-negative | `canon_price` |
    | size — a resting quantity at a level | non-negative | `canon_size` |
    | qty — a delta amount, a position change | signed | `canon_qty` |
    | money — cash, fees, realised P&L | signed | `canon_money` |

    Venue range policy (Kalshi binary contracts trade in [0,1]) is deliberately **not**
    enforced: it is the venue's rule, it can change, and encoding it would silently reject real
    data if it did.

16. **An uninterpretable field makes the projection incomplete.** A value the recorder cannot
    interpret — an unparseable price, a non-decimal quantity, a negative resting size, an
    unrecognised side, a malformed level — is **never dropped, defaulted, or rounded into
    something plausible**. The observation is still recorded (we did see the message), a
    `UNINTERPRETABLE_FIELD` anomaly names the offending fields, the value is not applied, and
    the book is marked `complete: false` until the next fully-interpretable snapshot.

    A zero resting size is not an uninterpretable value — it is simply not a level, and is
    dropped from a snapshot exactly as a delta pops a level at zero.
10. **Replay is a pure function of the log.** Projections take the log and nothing else.
11. **Duplicates are never applied twice.** A repeated `venue_seq` is recorded as a
    `DUPLICATE_MESSAGE` anomaly carrying the payload, and no second OBSERVATION is emitted. If
    the repeat's content differs from the original, the interval is marked incomplete — which
    of the two the venue meant is unknowable from the record.
12. **Direction is never guessed.** An execution whose `side` or `action` cannot be resolved —
    from the event itself or a matching INTENT — is listed in `unresolved` and excluded from
    account state. `complete` becomes false. A fill is never assumed to be a buy.
13. **Strict JSON only.** `NaN` and `Infinity` are rejected at ingestion as malformed. Every
    written line parses under a conforming strict parser, so the chain is reproducible across
    implementations.
14. **Log order, not clock order.** Replay iterates the log in append order and *filters* by
    timestamp; it never stops at the first out-of-boundary event. Receipt clocks can step
    backwards, and a clock step must not make eligible events disappear.

## 6. Projections (derived, never stored as truth)

- **Order book at `t`** — apply the latest snapshot at or before `t`, then deltas in `venue_seq`
  order, per market. Returns `(book, complete: bool, reason)`.
- **Account state at `t`** — cash, position, reserved collateral, realised P&L, fees, open
  orders, folded from INTENT and EXECUTION events only.

Both are recomputed from the log on demand. Neither is written back.

## 7. Integrity

Two mechanisms, because one is not enough:

1. **Hash chain** over an append-only file. `hash = sha256(canonical_json(event) || prev_hash)`.
2. **Checkpoint sidecar** at `<log>.checkpoint`, rewritten atomically after every append,
   holding `event_count`, `last_index`, `last_hash`.

A hash chain alone **cannot detect its own tail being cut** — the surviving prefix is
internally consistent. The checkpoint supplies the missing length-and-head attestation. This was
found by audit, not by design, and the claim below is written to match what the mechanism
actually does.

### What is detected

| Attack | Detected by |
|---|---|
| Modification of any event | chain — `hash_mismatch` |
| Insertion of a forged event | chain — `broken_link` |
| Deletion from the middle | chain — `index_out_of_order` |
| Reordering | chain — `index_out_of_order` |
| **Truncation of the tail** | checkpoint — `truncated_tail` |
| Missing checkpoint | `checkpoint_missing` — verification **fails**, never passes quietly |

### What is NOT detected

- An adversary with write access to **both** the log and the checkpoint who recomputes the
  entire chain from the point of alteration. Nothing here is a defence against the operator.
- **No external time anchor exists.** The record attests its own internal consistency and
  length; it does not prove *when* it was written.

Stronger guarantees — external notarisation, write-once storage, signed checkpoints — remain
deliberately deferred, and the absence of them is stated rather than glossed.

## 8. Settlement boundary

The recorder records **what Kalshi paid**, as an EXECUTION event of kind `settlement`.

It does **not** verify that the venue computed settlement correctly. BRTI values are licence-gated
and the index carries internal state and an expert-judgement provision, so independent
reproduction is out of scope until a licence is actually established.

The log must therefore never contain a field implying verification. `OBSERVED` and
`INDEPENDENTLY VERIFIED` are different claims, and only the first is available.

## 9. Execution boundary

INTENT and EXECUTION schemas exist so real execution can later be recorded without redesign.

**No orders are submitted in this phase.** There is no order-submission code path. No
counterfactual fill simulation exists anywhere in the package — queue position is not observable,
so no claim about an unplaced order is representable in the schema.

17. **A snapshot cannot establish completeness unless it is a valid anchor.** Receiving a
    snapshot message does not imply a usable anchor exists. Three states are distinct and
    separately recorded:

    | State | Meaning |
    |---|---|
    | `anchor_received` | A snapshot message arrived. `ANCHOR_RECEIVED` event, always emitted. |
    | `anchor_valid` | It canonicalised into **at least one bid and at least one ask**. |
    | `anchor_applied` | Replay applied it and, if valid, established completeness. |

    An invalid anchor emits `ANCHOR_INVALID` and establishes **nothing** — `complete` stays
    false with the reason attached.

    *Provenance: added 2026-08-10 after the REST/WS key defect described in
    [`README.md`](README.md#correction) let an empty anchor assert completeness.*

## 10. Completion criteria

1. live WebSocket observation
2. sequence-gap detection
3. both clocks preserved
4. append-only capture
5. deterministic order-book replay
6. deterministic account-state replay
7. explicit recorder failures
8. reproducible reconstruction from the log alone
9. integrity verification
10. health / evidence report
