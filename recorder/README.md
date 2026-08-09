# Genesis Prospective Environment Recorder

**Classification: IMPORT + BUILD — engineering. Not research. No novelty claimed.**

The first Genesis system that is meant to run rather than to be studied. It observes the Kalshi
environment prospectively and preserves an auditable record of:

> what the environment showed → what Genesis knew → what Genesis decided → what Genesis
> requested → what actually happened → what was eventually paid.

Specification, written before the implementation: [`SPEC.md`](SPEC.md).

## Scope

**This is not a trader.** There is no strategy, model, signal, backtest, parameter search,
profitability analysis, or order-submission path. No counterfactual fill simulation exists
anywhere in the package — queue position is not observable, so a claim about an unplaced order
is not representable in the schema.

INTENT and EXECUTION schemas exist so that real execution can later be recorded without
redesigning the event model. Nothing writes to them except tests.

## Status — read this before trusting anything here

**The live path has never run.** No Kalshi API credentials were available, so
[`kalshi.py`](kalshi.py) — the only module that touches the network — is written from the
published documentation and has never opened a real connection. Everything else is exercised by
[`../tests/test_recorder.py`](../tests/test_recorder.py) against synthetic fixtures built to the
documented payload shapes.

Until the recorder has actually observed the venue, its health report will show an empty
observation period, and no claim about live behaviour is made.

## Layout

| File | Role |
|---|---|
| `SPEC.md` | Event schema and invariants — written first |
| `events.py` | Envelope construction, canonical JSON, hash chaining |
| `log.py` | Append-only JSONL log, chain resume, integrity verification |
| `stream.py` | Transport-agnostic ingestion, sequence tracking, gap detection |
| `kalshi.py` | WebSocket adapter — **untested against the live venue** |
| `replay.py` | Deterministic projections: order book at *t*, account state at *t* |
| `health.py` | Health and evidence report |
| `run.py` | CLI |

The core is transport-agnostic on purpose: `stream.py` accepts already-received messages, so
everything that carries an epistemic guarantee is testable without a network or credentials,
and the untested surface is confined to one thin module.

## Use

```
.venv/bin/python recorder/run.py verify  <log>
.venv/bin/python recorder/run.py health  <log>
.venv/bin/python recorder/run.py book    <log> <ticker> [--at ISO8601]
.venv/bin/python recorder/run.py account <log> [--at ISO8601]
.venv/bin/python recorder/run.py record  <log> <ticker> [--seconds N]   # live; needs credentials
```

`record` requires `KALSHI_KEY_ID` and `KALSHI_PRIVATE_KEY_PATH`, plus the `cryptography` package
for request signing (imported lazily). `websockets` is required for the live path only.

Checks: `.venv/bin/python tests/test_recorder.py`

## The two guarantees

**Known incompleteness beats fabricated completeness.** Sequence gaps, reconnects, restarts,
malformed messages, clock disagreements and errors are all recorded as first-class events. A
projection spanning any of them is returned with `complete: false` and a reason, never as a
plausible-looking book. Missing deltas are never synthesised.

**Observed is not verified.** Settlement is recorded as what Kalshi paid. The reference values
are licence-gated and the index carries internal state and an expert-judgement provision, so
independent reproduction is out of scope. `observed` and `independently_verified` are separate
fields and the second is always `false` today.
