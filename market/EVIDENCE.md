# Evidence — market

Raw recordings are large and append-only hash-chained. Committing them would bloat the
repository to preserve a property the chain already provides.

**What is committed:** the checkpoint sidecar and the derived report for every recording, plus
the SHA-256 of the raw log below.
**What is archived outside the repository:** the raw logs, at `~/genesis-evidence/`.

The committed checkpoint records the chain head. Any modification to an archived log —
insertion, deletion, truncation, or an edited byte — breaks the chain and fails verification
against it.

**Nothing is deleted.** Failed and superseded runs are archived exactly like successful ones.

## Verifying an archived log

```sh
shasum -a 256 ~/genesis-evidence/q3/btcusdt-q3.jsonl     # compare with the digest below
.venv/bin/python recorder/health.py ~/genesis-evidence/q3/btcusdt-q3.jsonl
```

`health.py` re-derives the chain and reports `integrity_verified`. **Exit status is the
verdict:** `0` verified, `1` not verified, `2` could not check at all. The digest catches
substitution of the whole file; the chain catches everything inside it.

> Until 2026-08-17 `health.py` had no command-line entry point, so the command above printed
> nothing and exited 0 — a documented integrity check that reported success without reading a
> single event. Fixed, with regression checks in
> [`../tests/test_health_cli.py`](../tests/test_health_cli.py). If you verified an archived log
> before that date, the verification did not happen.

---

## EXEC-1 — Q3 order-book recording, 2026-08-10 → 2026-08-17

Contract [`CONTRACT-execution.md`](CONTRACT-execution.md), frozen before the recording began.
Record: [`../research/experiments/0009-exec-1-maker-advantage.md`](../research/experiments/0009-exec-1-maker-advantage.md).
Defects found at close: [`../research/exec-1-recording-defects.md`](../research/exec-1-recording-defects.md).

| | |
|---|---|
| Log | `~/genesis-evidence/q3/btcusdt-q3.jsonl` |
| SHA-256 | `740fc04d4cf40d81ab60090d3717266c1bc7d6f2e81d8e7880e34193e8381d63` |
| Size | 3.4 GB — 580,658 events |
| Market | Binance spot, BTCUSDT, `depth` diff stream anchored by REST `depthSnapshot` |
| First event | `2026-08-10T13:58:23.770905Z` |
| Last event | `2026-08-17T17:52:31.941051Z` |
| Recorder runs | 1 — unbroken, no restarts, watchdog never fired |
| Integrity | **verified** · 0 sequence gaps · 0 malformed · 0 uninterpretable |
| Complete time | **93.4%**, across 82 incomplete intervals |
| **Analysis window** | `2026-08-10T13:58:23.770905Z` → `2026-08-17T13:58:23.770905Z` (168.00 h) |

The recording ran 3 h 54 m past the analysis window because `--seconds` is enforced against a
monotonic clock that does not advance while the host sleeps (defect D-1). The host slept 6.28 h
across 18 episodes. **The analysis window excludes the overrun**; the raw log retains it, since
nothing is deleted.

The contract's §3 states the start as `16:58 UTC`. That is the local (EAT) time; the recording
actually began `13:58 UTC` (defect D-2). The window above uses the observed first event.

Committed alongside:
`evidence/q3-recording.checkpoint` · `evidence/exec1-report.json` · `evidence/ledger.checkpoint`

### Trials

All four declared before the data existed, all recorded, none outstanding. Family size fixed by
the grid; Bonferroni α = 0.0125.

| Trial | Question | Outcome |
|---|---|---|
| `3488b1e1` E3 | Does >100% of the maker advantage survive at the touch at 60 s? | **No** — 39.07% lost, 60.93% survives. Kill condition §6 **not** triggered. |
| `ad6c400b` X5 | Worse in quiet hours than the US session? | **No**, and opposite in direction. Not separated. |
| `a4cd747a` X6 | Does doubling latency worsen adverse selection? | **No measurable difference** — see structural limitation. |
| `c228c389` X7 | Worse further from the touch? | Direction consistent, **not separated** — see structural limitation. |

### The limitation that governs X3, X4, X6 and X7

At the median order price of **$63,476.05** with `TICK = 0.01`, the declared 0–5 tick offset
grid spans **0.0079 bps** — **151× smaller** than the 1.19 bps adverse move it was intended to
modulate. The two latency arms differ by 359 ms against a 300 s TTL, 0.12% of an order's life.

Those nulls are properties of the declared grid as much as of the market. They are recorded
rather than withdrawn, because a declared trial cannot be un-declared, but they must not be
cited as evidence that distance or latency do not matter to execution.

## MEASURE-1

Committed: `evidence/measure1-report.json`, `evidence/power-analysis.json`.
Record: [`../research/experiments/0008-measure-1-cost-of-being-right.md`](../research/experiments/0008-measure-1-cost-of-being-right.md).

## The trial ledger

`~/genesis-evidence/ledger/trials.jsonl`, hash-chained, checkpoint committed at
`evidence/ledger.checkpoint`. 27 trials declared, 27 recorded, 0 outstanding, chain verified.

```sh
.venv/bin/python -c "import sys; sys.path.insert(0,'market'); import ledger; print(ledger.Ledger().verify())"
```

---

The archive is on one machine and is not backed up. That is a known and accepted gap — the
derived reports and the integrity record are what the project's claims rest on, and those are
in git.
