# Engineering standards

**Standing instruction from the researcher, 2026-08-10. Binding on all Genesis code, whoever
writes it.**

> Genesis code must always practise proper data structures and algorithms, proper programming
> practice, refactoring, and testing.

[`collaboration.md`](collaboration.md) governs what Claude may and may not decide. This governs
how the code is written, and is not a matter of taste — in a research repository, sloppy
engineering does not merely age badly, it **produces wrong results that look right**.

Every rule below is here because it was violated in this repository and something broke. The
citations are the point; a standards document with no incident behind each line is decoration.

---

## 1. Data structures and algorithms

**Convert once on write, never repeatedly on read.** Establish the cost of an operation
against the *size of the data it will actually see*, not the size in the test.

> The order book holds ~4,834 levels. `_size_at` linear-scanned all of them to find one price,
> per order, per frame, re-parsing every price string on every comparison. Correct on three
> hours of BAV-1 data; would not have finished EXEC-1. Found only because someone asked whether
> the code was any good.

**Know the shape of the data, not just the timing.** A benchmark that reports speed and not
structure tells you something is slow without telling you why.

> "476 frames/s" was uninformative. "4,834 levels per frame" identified the fault immediately.

**Choose the structure the access pattern wants.** A lookup by key belongs in a dict. A repeated
extremum belongs in a cached value invalidated on change, not recomputed by scanning.

## 2. One implementation per idea

**Never write the same rule twice.** Two implementations of one idea always drift, and the drift
is silent until it produces a wrong answer.

> The completeness rule was written once in `replay` and once in `health`. They diverged on six
> conditions. One of those six caused BAV-1 run 2 to report `complete` through fourteen
> disconnections the recorder had announced itself, wasting a full run. Consolidated into
> `completeness.py`; `replay` and `health` now ask rather than decide.

Where two views of one thing are genuinely needed, build one implementation and adapt it —
`book.stream` yields the live book and `book.walk` adapts it, rather than two book builders.

## 3. Testing

**Write the test before the fix.** Every defect gets a check that fails first, so the fix is
demonstrated rather than asserted.

**Test against answers known in advance.** A method validated only on real data is validated
against nothing, because the data contains no ground truth to check it with.

> The Lo-MacKinlay z-statistic carried a stray factor of `n`, making it too small by `sqrt(n)`.
> On real data it would have returned "no rejection at any horizon" — exactly the pre-registered
> prediction — and been indistinguishable from the truth. Caught only by a synthetic series with
> a known answer.

**Test the silent failures hardest.** Code that crashes when wrong is safe. Code that returns a
plausible wrong number is not.

> The cached best price does not crash when stale; it quietly corrupts every fill. Its test
> compares the cache against full recomputation across 4,000 random updates.

**Isolate every test.** Shared state between checks produces both false passes and false
failures.

> Twice in one day: a shared ledger filename let counts accumulate across checks, and a shared
> log filename let `EventLog` resume the previous test's chain.

**Know what the runner actually runs.** A pass count is a claim, and it must be true.

> pytest silently collected 12 of 49 checks, and `run_all.py` omitted two suites. "10/10 suites
> pass" was corrected in a commit message once the real number was known.

## 4. Refactoring

**Refactoring must not change behaviour, and that is verified rather than asserted.** Re-run a
prior measurement and compare against the committed evidence.

> After the book was rewritten, `measure_CD` reproduced BAV-1 run 3 exactly — same 2,042
> samples, same median depth to the last digit, zero delta on every spread and round-trip
> figure. That check, not the passing suite, is what licensed the change.

**Refactor when the third instance appears**, not in anticipation of it. Premature abstraction
and duplicated rules are both failures; the difference is which one the evidence shows.

**Leave the reason, not the narration.** Comments record why something is non-obvious — a
constraint, a venue quirk, a bug that would otherwise be reintroduced. Never what the code
plainly does.

## 5. Correctness practices specific to this repository

- **Never invent an observation.** Gaps are reported, never interpolated. A halt is a hole in
  the record, not a value to fill in.
- **Verify the data's semantics against the raw bytes.** Assuming cost nothing until it did:
  the kline check found halt-truncated bars, an unreliable `close_time`, and a silent switch to
  microsecond timestamps that would have placed every 2025+ bar 50,000 years in the future.
- **Fail safe on the unknown.** An unrecognised error kind invalidates completeness rather than
  preserving a claim that cannot be defended.
- **Bracket what cannot be known.** Where the data cannot settle a question — queue consumption
  without a trade stream — report bounds and the width between them, never a guess dressed as a
  measurement.
- **Preserve all evidence.** Failed runs are archived exactly like successful ones. BAV-1 runs 1
  and 2 answered nothing and are the most instructive records in the repository.

## 6. The standard behind all of it

> **Ask "have we actually measured that?"** — it has a better hit rate than any other question
> asked in this project.

Every serious defect here was found by measurement, never by reasoning about the code: the six
recorder defects, the broken variance-ratio statistic, the missing power analysis, the
uncounted trials, the linear scans. The reasoning was almost always fine. What was missing was
a number.
