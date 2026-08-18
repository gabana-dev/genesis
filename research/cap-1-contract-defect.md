# D-C1 — a transcription error in CONTRACT-capacity.md, recorded not repaired

**Date:** 2026-08-18
**Status: OPEN as a defect; RESOLVED as an execution decision, on the record.**

CONTRACT-capacity.md was frozen at sha256
`a239531e27d44f451da8f823b24e7e20725d5971d9ac6c4d12927947a99d88e0`. Its §4 grid contains a
line that cannot be satisfied as written.

## The defect

> | TTL | 60,000 ms (as EXEC-1) |

**EXEC-1's TTL is 300,000 ms** (`exec1.TTL_MS`, from CONTRACT-execution.md §4). The number and
the parenthetical disagree, and only one can be honoured.

The contract's own rule applies: *"If a defect is found in the contract it is reported and
recorded, not silently repaired."* This document is that report. **The frozen file is not
edited.**

## The resolution, and why

**TTL = 300,000 ms was used** — the parenthetical, not the literal number.

1. **The governing sentence overrides the cell.** §4 opens: *"Identical to EXEC-1's in every
   respect **except size**, so the size slope is the only thing that varies and any difference
   is attributable."* A 60,000 ms TTL varies a second parameter and destroys precisely the
   attribution the grid exists to preserve. Under it, a difference between size cells could
   not be assigned to size.

2. **It would make K1 fire on a typo.** K1 requires the $10,000 anchor to reproduce EXEC-1
   within 0.05 bps, and voids the entire run if it does not. Under a 5× shorter TTL the anchor
   *cannot* reproduce EXEC-1 — fewer orders survive to fill, and a different population of
   fills is selected. K1 would have reported a defect in the re-simulation when the defect was
   in the contract's transcription.

Honouring the literal number would have produced a run that was void by construction and
misattributed the cause.

## What this costs

**It is a deviation from the literal text of a frozen contract, made by the implementer.**
That is exactly the class of act pre-registration exists to prevent, and calling it obviously
correct does not change its class.

Three things bound it:

- It was found and recorded **before the simulation ran**, not after a result was seen.
- It moves a parameter **toward** EXEC-1's declared value, not toward any outcome. The
  direction of the change was fixed by the contract's own governing sentence, and no result
  was visible when it was made.
- K1 remains armed and unweakened. If the anchor fails, the run is void regardless.

**What it does not do is make the contract clean.** CAP-1's result carries this deviation in
its report body (`ttl_deviation`) and in every statement of the result.

## For the next contract

The grid table should have been checked against `exec1.py`'s constants rather than against
memory of them. Every "(as EXEC-1)" in a future contract needs the value read out of the code
at the time of writing, not recalled.
