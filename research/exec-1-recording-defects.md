# EXEC-1 recording — defects found at close

**Date:** 2026-08-17
**Status:** engineering defects. **Not research.** No hypothesis tested, no claim about markets.
**Scope:** the Q3 recording `~/genesis-evidence/q3/btcusdt-q3.jsonl` and the code that produced it.
**Effect on data:** none. Every defect below concerns duration control, documentation, or
verification ergonomics. The record itself verifies: `integrity_verified: True`, 0 sequence
gaps, 0 malformed messages, 0 uninterpretable messages, single recorder run, no restarts.

Drafted by AI as a record of observed facts. Placement, adoption and any consequent decision
are the researcher's.

---

## The recording, as it ended

| | |
|---|---|
| First event | `2026-08-10T13:58:23.770905Z` |
| Last event | `2026-08-17T17:52:31.941051Z` |
| Wall span | 7 d 3 h 54 m 08 s = **171.90 h** |
| Events | **580,658** |
| Size | 3.4 GB |
| Integrity | **verified** |
| Sequence gaps | **0** |
| Healthy (complete) time | **93.4%**, 82 incomplete intervals |
| Recorder runs | 1 — unbroken, watchdog never fired |

Stopped deliberately by SIGTERM at the researcher's instruction, before its own deadline. The
last line is complete; there are no trailing fragments.

---

## D-1 — `--seconds` measures awake time, not wall-clock time

**Where:** `recorder/binance.py:58`

```python
deadline = None if stop_after is None else loop.time() + stop_after
```

`loop.time()` is the asyncio event loop's monotonic clock. On macOS the monotonic clock **does
not advance while the system is asleep**. So `--seconds N` bounds *N seconds of wakefulness*,
not *N seconds of elapsed time*, and the two diverge by exactly the time the host spends
suspended.

**Measured on this run.** The host slept **18 times** during the recording, totalling
**22,611 s = 6.28 h**. Three were consequential; the rest were maintenance sleeps.

| Start (local) | Duration | Cause |
|---|---|---|
| 2026-08-15 19:04:50 | 91.8 min | Low Power Sleep, battery 0%, AutoPowerOff |
| 2026-08-11 00:44:30 | 68.9 min | — |
| 2026-08-16 12:54:10 | 49.3 min | — |

Consequently the run was still going 3 h 54 m past its nominal end, and at the moment it was
stopped had accrued only ~596,237 s of monotonic time against a 604,800 s deadline — roughly
**2.4 h short of stopping itself**.

**Why it matters beyond this run.** The failure is silent and unbounded. A host that sleeps
overnight would produce a recording that runs a day long with nothing in any log to say why.
The duration parameter reads like a wall-clock guarantee and is not one.

**FIXED 2026-08-18** — `recorder/binance.py` now computes the deadline from `time.time()`.

This was originally deferred on the grounds that changing duration semantics affects what a
pre-registered window means. On reflection that framing was wrong: wall clock is what a caller
passing `604800` already meant, and what the EXEC-1 contract's "7 days" already meant. The
monotonic clock was a defect, not a design choice, so this **restores** the intended semantics
rather than changing them. NTP can step the wall clock, but by seconds over a week — negligible
beside the hours a monotonic clock loses to host sleep.

**Second-order observation.** Because the deadline is monotonic, the overrun partially
*compensated* for the observation gaps the sleeps caused. This was accidental. It should not
be relied on and does not make the behaviour correct.

---

## D-2 — the contract states the start time in UTC; it is EAT

**Where:** `market/CONTRACT-execution.md` §3

> `~/genesis-evidence/q3/btcusdt-q3.jsonl` — BTCUSDT depth, recording started 2026-08-10 16:58
> **UTC**, 7 days, hash-chained.

The first event in the log is timestamped `2026-08-10T13:58:23.770905Z`. The recording started
at 16:58 **EAT** (UTC+3) = 13:58 UTC. The contract recorded local time and labelled it UTC.

**Error: 3 hours.**

**Consequence.** It changes where a 7-day window closes. Read literally, the declared window
ends `2026-08-17T16:58Z`; read against the actual start, it ends `2026-08-17T13:58Z`. Any
truncation to "the declared seven days" must choose, and the second is the one the data
supports.

**Note on amendment.** The contract is frozen. This is a factual error in a descriptive field
rather than a threshold, exclusion or grid parameter — but whether to correct it, annotate it,
or leave it and record the discrepancy here is the researcher's call. Nothing was edited.

---

## D-3 — a documented verification command that verifies nothing and reports success

**Where:** `recorder/health.py`, and `recorder/EVIDENCE.md` line ~25

EVIDENCE.md documents this as the way to verify an archived log:

```sh
.venv/bin/python recorder/health.py ~/genesis-evidence/bav-1/bav3.jsonl
```

> `health.py` re-derives the chain and reports `integrity_verified`.

`health.py` has **no `if __name__ == "__main__"` block.** Run as documented it imports the
module, defines its functions, prints nothing, and **exits 0**.

Verified on the EXEC-1 log: no output, exit status 0, elapsed 0.3 s on a 3.4 GB file — a
runtime that alone should have given it away. The real check takes 6 m 47 s via
`health.report()` and `health.render()`.

**Why this one matters most.** It is the project's own recurring pattern, in the project's own
verification tooling: *a status claim the available evidence did not support, with the
contradicting evidence one query away.* A command documented as the integrity check succeeds
silently without checking anything, and its success is indistinguishable from a real pass.

This is the same shape as the `sc query PsTallyMonitor` case and BAV-1 run 2. Whatever else
follows, this is the defect to fix first: an unusable verifier is worse than a missing one,
because it answers.

---

## Observation, not a defect — the sleep gaps are already handled

The host sleeps produced observation gaps. The completeness rule labelled them, as it labelled
every other interruption; they sit among the 82 incomplete intervals and are excluded by
CONTRACT §3 (*"intervals the recorder labels incomplete are excluded"*).

The 11 August window previously flagged for a keep-or-exclude decision resolves the same way.
`health.py` bounds it precisely:

```
2026-08-11T17:45:38Z -> 2026-08-11T18:26:26Z  (all markets)
  error in the observation path: ConnectionClosedError
```

40 m 48 s, already labelled incomplete. **No exclusion decision is required** — the frozen rule
handles it. An earlier note claiming the rule silently vouched for this window was wrong: it
searched only the 14:00 and 15:00 UTC hours and the invalidating error is at 17:45.

Two larger gaps, both likewise already labelled:

- `2026-08-12T07:50:20Z -> 2026-08-12T10:02:44Z` — 2 h 12 m
- `2026-08-12T06:30:38Z -> 2026-08-12T06:51:29Z` — 21 m

---

## Open, for the researcher

1. Whether to truncate analysis at `2026-08-17T13:58Z`, at the contract's literal
   `16:58Z`, or to use the full record and report the span as observed.
2. Whether D-2 warrants a contract annotation.
3. D-3 should be fixed before the next archived log is verified by anyone relying on that
   documented command.
