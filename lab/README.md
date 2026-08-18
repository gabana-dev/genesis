# lab/ — the retired cognitive-architecture laboratories

**This is history, kept runnable.** Moved here from `src/` on 2026-08-18.

These modules are Laboratories 1–3 and the closed-loop and sparse-observation studies —
experiments 0001–0005. They were built in the first three days of the project, under the
cognitive-architecture thesis that [DR0002](../research/decisions/0002-close-the-genesis-research-program.md)
retired on 2026-08-09 as established science.

They are kept because **nothing is deleted**, and because their results stand as recorded:
belief state beats memoryless under partial observability, the observation model is learnable,
and choice-over-information produced a clean negative that exposed primitive-counting as
description-relative. The tests still run and still pass.

## Why they were moved

`src/` was reserved by rule for the implementation of a cognitive architecture, and
[`README.md`](../README.md), [`../canon/architecture.md`](../canon/architecture.md) and
`src/README.md` all described it as intentionally empty. It was not — it held these files, and
the rule forbade exactly what they contain. A reader who cloned the repository concluded in
writing that the project had no implementation at all, which was wrong by roughly eleven
thousand lines.

Moving them makes every one of those documents true at once, and names this code as what it
is: superseded experimental work, not the project's implementation.

## Where the implementation actually is

| | |
|---|---|
| [`../recorder/`](../recorder/) | the event recorder — hash-chained log, completeness labels, venue dialects |
| [`../market/`](../market/) | measurement and execution — estimators, fill simulator, trial ledger |
| [`../rdb/`](../rdb/) | the RDB-1 real-data bridge (closed, [DR0004](../research/decisions/0004-close-rdb-1.md)) |
| [`../status.py`](../status.py) | the orientation layer ([DR0005](../research/decisions/0005-orientation-layer.md)) |

## Contents

- `genesis.py` — `receive`, `update`, `initial_belief`: the two primitives and the belief state
- `environment.py` — `PartiallyObservableBit`, the toy environment
- `agents.py` — memoryless, belief, and learning-belief agents
- `laboratory.py`, `laboratory2.py`, `laboratory3.py` — experiments 0001–0003
- `closed_loop.py`, `sparse_loop.py` — experiments 0004–0005

Tests: `../tests/test_laboratory{,2,3}.py`, `../tests/test_closed_loop.py`,
`../tests/test_sparse_loop.py`.
