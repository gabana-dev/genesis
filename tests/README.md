# tests/

Validation of the implementation. **This project uses its own runner and is not
pytest-compatible** — see below for why, and why that is enforced rather than documented.

## Running

```
.venv/bin/python tests/run_all.py            # every suite; non-zero exit on any failure
.venv/bin/python tests/run_all.py recorder   # only suites matching a substring
.venv/bin/python tests/test_recorder.py      # one suite directly
```

Each suite runs in its own process. The suites insert different paths onto `sys.path` and
hold module-level state, so running them in one interpreter would let one suite's imports
change another's behaviour. A test that passes only because of what ran before it is not
evidence.

## Suites

| Suite | Checks | Covers |
|---|---|---|
| `test_recorder.py` | 12 | Append-only log, hash chain, gaps, both clocks, replay, restart visibility |
| `test_recorder_audit.py` | 17 | Audit regressions F1–F3 and PARTIALs 4–8 — duplicates, truncation, unknown side, strict JSON, clock steps, health |
| `test_recorder_decimal_qty.py` | 9 | NF-1 — decimal quantities from the real observed REST shape |
| `test_recorder_validity.py` | 11 | D1–D5 — uninterpretable fields, validity by role, negative zero |
| `test_rdb_series.py` | 8 | RDB-1 ingestion: resolution transition, interval-ending, DST, holdout lock |
| `test_closed_loop.py` · `test_sparse_loop.py` | — | Milestones 1 and 2 |
| `test_laboratory{,2,3}.py` | — | Laboratories 1–3 |

Every recorder regression suite was **written before the fix it covers**, and each check
returns a one-line description that is printed with its result. That output is part of the
record — it is quoted in commit messages and reports.

## Why not pytest

`tests/conftest.py` makes `pytest` fail with a pointer to `run_all.py`. This is deliberate.
Measured before it was added:

```
31 collected -> 19 passed, 12 errors

test_recorder.py             12 collected, all ERROR (fixture 'tmp' not found)
test_recorder_audit.py        0 collected  (17 real checks, silently skipped)
test_recorder_decimal_qty.py  0 collected  ( 9 real checks, silently skipped)
test_recorder_validity.py     0 collected  (11 real checks, silently skipped)
```

pytest reported **19 passed** while silently omitting **37 of the recorder's 49 checks** —
every audit regression among them. The three files carrying F1–F3, NF-1 and D1–D5 contributed
zero tests, because their check functions are not named `test_*`.

That is the recorder's own failure mode reproduced in its tooling: a green summary asserting
completeness it has not earned, with the incompleteness unmarked. The repository has an
invariant against exactly this. An error is better than a false pass, so the error is enforced
in code rather than left to documentation.

**The counter-argument, recorded honestly.** A custom runner gives up `-k` filtering,
parametrisation, `--pdb`, coverage integration and the CI ecosystem. If this project ever
takes contributors or runs CI, that cost compounds and the right answer flips: move to pytest
properly — `tmp_path` instead of `tmp`, assertions instead of returned descriptions, and the
descriptions moved into docstrings. Today the evidence-quality property is worth more than the
tooling ecosystem. That is a judgement about what Genesis is for, and it should be revisited
if that changes.
