# Operations — how research is actually conducted here

**Status: RATIFIED by the researcher**, 2026-08-18, on their instruction: *"ratified"*.
**Type: 2 (factual).** Drafted by the assistant, 2026-08-18.

> **This document invents nothing.** Every rule below is already in force and already sourced
> to a decision record, a frozen contract, or an experiment that produced it. It exists because
> the practices were never written down anywhere canonical, and a rule nobody can find is a
> rule that gets lost — which happened twice: the Phase-5 constraint (DR0005) and the
> named-consumer requirement (DR0006), both of which existed and were mislaid.
>
> **If any line here is something the researcher does not recognise, that is a defect in this
> document, not a new commitment.** Nothing acquires force by appearing here.

## What this is, and what it is not

[`research-methodology.md`](research-methodology.md) is the *epistemic* account — how Genesis
thinks knowledge is formed. It was written before the market line existed and does not describe
the working method; that gap is recorded as **C9** in
[`../research/CURRENT-STATE-2026-08-18.md`](../research/CURRENT-STATE-2026-08-18.md).

This document is the *operational* account: what you must actually do to run an experiment
here. The two are complementary and neither supersedes the other.

---

## 1. Every result carries a classification

Before anything else, work declares what kind of thing it is: **import**, **build**, or
**research**. Import means established method, correctly applied, cited. Build means
engineering validation. Research means a novelty claim — and none has been made.

What this work **may** claim: that established machinery was correctly implemented, that it
behaved a particular way on a particular environment, and what that cost.
What it **may not** claim: novelty of any kind.

*Source: [DR0003](../research/decisions/0003-engineering-posture-real-data.md) §3, §4, §5.*

## 2. Before the data — the frozen contract

Protocol discipline is retained in full and is not relaxed because the stakes are labelled
engineering: **pre-declared contract, snapshot with checksums, leakage controls, serious
baselines, holdout locks, and disclosure of which analysis choices were fixed when.**

*Source: [DR0003](../research/decisions/0003-engineering-posture-real-data.md) §9.*

A contract is frozen — committed, with its sha256 recorded — **before the data exists**. In
practice it states:

| | |
|---|---|
| The questions | separated, numbered, in the order they matter |
| The grid | every parameter fixed in advance, so the family size is known and cannot grow |
| Exclusions | which data is dropped and why, decided before seeing it |
| Pre-registered predictions | each with a falsification criterion |
| **The kill condition** | what result would close this line — written before results exist |
| What it cannot establish | the limits, stated up front |
| Analysis order | raw outcomes before interpretation |

Worked examples: [`../market/CONTRACT-measurement.md`](../market/CONTRACT-measurement.md),
[`../market/CONTRACT-execution.md`](../market/CONTRACT-execution.md),
[`../recorder/CONTRACT-book-agreement.md`](../recorder/CONTRACT-book-agreement.md).

**A threshold that turns out to be unmeetable is not amended.** EXEC-1's PASS condition was set
at a network delay below 300 ms; the measured floor from this location is ~291 ms with a median
near 430 ms, making it structurally unevaluable. It was left unchanged and reported as
unevaluable rather than passed.

*Source: [0007 BAV-1](../research/experiments/0007-bav-1-book-agreement-validation.md) §2.*

### 2a. Predictive experiments must name their consumer

If the contract claims *this output tells you something about a future state*, it must also
name: the **consumer** (an existing code path, by file), the **decision changed**, the
**do-nothing baseline**, and a **wiring kill condition**. If the consumer cannot be named, the
experiment is not declared.

Descriptive measurement is unaffected and needs no consumer.

*Source: [DR0006](../research/decisions/0006-no-prediction-without-a-consumer.md).*

## 3. The trial ledger

Every test that could produce a number the project might act on is **declared before it is
run**, and cannot be un-declared. A declared trial with no result stays visible forever as
outstanding.

- The ledger is a hash-chained append-only log. A counter that can be quietly edited is worth
  nothing.
- **The family is fixed by the grid**, so it cannot grow to accommodate a search.
- `family` is required and never inferred — it is the set of results you would have been
  equally happy to find.
- `preregistered` is False for anything decided after seeing data. Exploratory work is
  legitimate; exploratory work mislabelled is not.
- **Descriptive measurements are recorded as CONTEXT, not trials**, so the boundary between
  *looking* and *claiming* is itself auditable rather than remembered.
- Corrections are applied and reported: Benjamini–Hochberg, Bonferroni, and the deflated Sharpe
  ratio, which prices how many attempts preceded a result.

*Source: [`../market/ledger.py`](../market/ledger.py);
[`../market/CONTRACT-execution.md`](../market/CONTRACT-execution.md) §7;
[0008 MEASURE-1](../research/experiments/0008-measure-1-cost-of-being-right.md) §9.*

## 4. The record — what may be trusted

- **Nothing is invented.** Gaps are reported, never interpolated. A halt is a hole in the
  record, not a bar.
- **Data semantics are verified against the raw bytes**, not assumed. Three defects were found
  in Binance's own public archives this way.
- **Fail safe on the unknown.** An unrecognised error invalidates completeness rather than
  being exempted; the exemption list is deliberately empty.
- **Bracket what cannot be known.** Where the data cannot settle a question, the answer is a
  reported interval, not a point.
- **Nothing is deleted.** Failed runs are archived exactly like successful ones — BAV-1 runs 1
  and 2 failed and are the most instructive records the project holds.
- **Intervals the recorder labels incomplete are excluded**, and that label was *validated* to
  carry information (p = 0.0165) rather than assumed to.

*Source: [`../ai/engineering-standards.md`](../ai/engineering-standards.md) §5;
[0007 BAV-1](../research/experiments/0007-bav-1-book-agreement-validation.md).*

## 5. After the data — reporting

- **Raw outcomes before interpretation**, and interpretation in a separately marked section.
- **Per period as well as pooled.** A figure unstable across days is not a figure; and a pooled
  statistic can describe a population that never existed.
- **Power before claiming a null.** MEASURE-1 §7 asserted that structure and affordability do
  not overlap; §8 withdrew it, because at ≥4h the test was blind. *Failure to reject is not
  evidence of absence*, and saying so cost the project its headline claim.
- **Structural limitations are recorded with the result, not instead of it.** EXEC-1's X6 and
  X7 nulls carry a "read before citing" block explaining that the declared grid spanned 151×
  less than the effect it was meant to modulate.
- **A declared trial is never withdrawn** because its result became inconvenient. It is
  recorded with its limitation.

*Source: [0008 MEASURE-1](../research/experiments/0008-measure-1-cost-of-being-right.md) §8;
[0009 EXEC-1](../research/experiments/0009-exec-1-maker-advantage.md) §9, §12.*

## 6. Sequencing

**One step at a time, chosen from evidence.** No sequence of future milestones is adopted in
advance; each is chosen from what the previous one exposed. A pre-planned technology roadmap is
the capability-graph failure mode DR0001 classified **F — abandon**.

*Source: [DR0003](../research/decisions/0003-engineering-posture-real-data.md) §10.*

## 7. Kill criteria

**Authored by the researcher, 2026-08-09.** Relocated here from `ai/current_focus.md` on
2026-08-18 — verbatim, unedited — because that file is designated working memory holding "state
and activity, never project substance", and these bind. Resolves half of **C5**.

> Stated so that abandoning a line of work is a planned outcome rather than a failure, and so
> that "intellectually interesting" is never sufficient reason to continue.

| Condition | Response |
|---|---|
| Live validation reveals the recorder is fundamentally flawed | **Fix it** |
| The recorder works beautifully but no meaningful application emerges | **Reconsider the application** |
| An application requires assumptions Genesis cannot legitimately observe | **Reject it** |
| The system grows more complex without producing evidence | **Stop and simplify** |
| An established product already does exactly what Genesis does | **Do not pretend we invented it** |
| A genuinely valuable capability is found | **Investigate commercialisation aggressively** |

**Which have fired, as of 2026-08-18.**

*"An established product already does exactly what Genesis does → do not pretend we invented
it."* — **FIRED.** [`../research/market-prior-art-audit.md`](../research/market-prior-art-audit.md)
returns **A, import** for all five candidate areas, including the recorder's own
completeness-validation method, which is the match-up validation pattern from earth
observation. The response is discharged: the finding is recorded publicly and no novelty is
claimed anywhere in the repository.

*"The recorder works beautifully but no meaningful application emerges → reconsider the
application."* — **not fired.** No application has been tried.

The remaining four have not fired.

## 8. Who may decide what

The AI operates on the **form** of the work; the researcher owns its **substance**. The AI may
not introduce a principle, change direction, alter definitions, or reinterpret a conclusion.
Nothing enters the canon without a Source link to the reasoning that earned it.

The orientation layer ([`../status.py`](../status.py)) reports state and never decides — it may
not declare a trial, record a result, amend a contract, or choose a direction.

*Source: [`../ai/collaboration.md`](../ai/collaboration.md);
[DR0005](../research/decisions/0005-orientation-layer.md).*

---

## Where each rule came from

| Practice | Source |
|---|---|
| Classification: import / build / research | DR0003 §3–5 |
| Frozen contract, checksums, disclosure of what was fixed when | DR0003 §9 |
| Unmeetable thresholds are not amended | BAV-1 §2 |
| Named consumer for predictive work | DR0006 |
| Declare before running; cannot un-declare | `market/ledger.py` |
| Family fixed by the grid; CONTEXT vs trial | CONTRACT-execution §7 |
| Multiple-comparison correction | MEASURE-1 §9 |
| Power before a null | MEASURE-1 §8 |
| Structural limitations recorded with the result | EXEC-1 §9 |
| Gaps reported, never interpolated; nothing deleted | `ai/engineering-standards.md` §5 |
| Completeness label validated, not assumed | BAV-1 |
| One step at a time, evidence-led | DR0003 §10 |
| Form/substance division; provenance | `ai/collaboration.md` |
| Reports, never decides | DR0005 |
