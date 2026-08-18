# Roadmap

> Maintained by Claude (form only) per the
> [Governing Principle](../ai/collaboration.md#governing-principle). **Type: mixed** — the
> research direction (the phases) is Type-1, authored by the researchers; the factual
> Phase-0 status is Type-2, recorded by Claude.

**Purpose:** Where we are and what comes next. Honest about the present, prompted for the
future.

---

## Phase 0 — Build the laboratory *(complete, 2026-08-18)*

Establish the research operating system before any cognitive work begins.

- [x] Repository and directory structure created.
- [x] Collaboration contract written (`ai/collaboration.md`).
- [ ] Canon scaffolds populated with authored content (`vision`, `constitution`, `ontology`).
- [ ] First entries in `research/` (journal, first questions).

Phase 0 is complete when the laboratory can hold serious research without losing its
thread — the docs are real, the working memory is live, and the discipline is in place.

> **Marked complete 2026-08-18.** The laboratory has held four experiments (0006–0009), six
> decision records, a hash-chained trial ledger, and ~11,400 lines of Python under 19 test
> suites. The two unticked boxes above are stale rather than outstanding: `constitution` and
> `ontology` were left unpopulated when the cognitive-architecture thesis they would have
> served was retired by [DR0002](../research/decisions/0002-close-the-genesis-research-program.md).
> Resolves half of **C6**.

---

## When an LLM may enter the loop

**Authored by the researcher.** Relocated here from `ai/current_focus.md` on 2026-08-18 —
verbatim, unedited — because that file is designated working memory holding "state and activity,
never project substance", and this binds. Resolves half of **C5**.

> **LLM enters at Phase 5** for hypothesis generation, anomaly explanation, unstructured events
> and the research record. **Never the signal.** **Agents: none until Phase 5**, then one at a
> time, each justified by a measured decision the current system gets wrong.

*This constraint was asserted from assistant memory on 2026-08-18, searched for in `canon/` and
`research/` but not `ai/`, and wrongly recorded as absent in
[DR0005](../research/decisions/0005-orientation-layer.md). An outside reader of the public
repository found it. The correction is in that record; the constraint itself was always real.*

**The Phase 5 it refers to belongs to the market phase list, not to this document.** That list
is still in `ai/current_focus.md` and has **not** been promoted here — see the note below.

---

## Later phases

> Authored by the researchers. What comes after the laboratory is built — the research
> direction itself — is yours to define. AI leaves this open.

> ### Note added 2026-08-18 — two roadmaps, and why the other one was not merged here
>
> A **7-phase market sequence** exists in [`../ai/current_focus.md`](../ai/current_focus.md):
> trustworthy observation → market literacy → measure the environment → execution economics →
> one decision with one real cost → paper trading → pre-registered hypothesis search →
> edge-decay monitoring → small capital. Phases 0–3 are complete (BAV-1, MEASURE-1, EXEC-1).
>
> **C10 resolved 2026-08-18, in favour of the canon.** The sequence formerly headed *"Genesis
> is for financial markets, everything built from here pushes toward paper trading"* has been
> **restated as conditional** on the researcher's instruction. No application is selected.
> Markets are the environment Genesis has been measured against, not a destination.
>
> The sequence is therefore recorded here as **conditional and unauthorised** — what the order
> *would be* if markets were pursued, so that adopting it later is a visible decision rather
> than a drift.

### The market sequence — CONDITIONAL, selects nothing

**Nothing below is authorised.** Recording an order is not choosing to walk it, and DR0003 §10
still forbids adopting a roadmap of future milestones in advance. This exists so that a later
decision to proceed has to be made explicitly.

| | | |
|---|---|---|
| 0 | Trustworthy observation | **complete** — [BAV-1](../research/experiments/0007-bav-1-book-agreement-validation.md), p = 0.0165 |
| 1 | Market literacy | the researcher's own; not a Genesis work item |
| 2 | Measure the environment, do not trade it | **complete** — [MEASURE-1](../research/experiments/0008-measure-1-cost-of-being-right.md) |
| 3 | Execution economics | **complete** — [EXEC-1](../research/experiments/0009-exec-1-maker-advantage.md), 1.83 bps survives |
| 4 | **One decision, one real cost, against a do-nothing baseline** | not started — the next phase if pursued |
| 5 | Paper trading at deployable size | not started |
| 6 | Pre-registered hypothesis search — trial counter, deflated Sharpe, held-out untouched | not started |
| 7 | Edge-decay monitoring — the completeness machinery pointed at strategies | not started |
| 8 | Real capital, small | not started; **no decision record authorises this** |

Phase 4 is the one [DR0006](../research/decisions/0006-no-prediction-without-a-consumer.md)
shapes: any predictive contract must name its consumer, the decision it changes, a do-nothing
baseline, and a wiring kill condition. EXEC-1 already supplies the baseline — a fixed 300 s TTL
losing 39.07% of the maker advantage.

The constraints that would bind, all measured rather than assumed, are in
[`../ai/current_focus.md`](../ai/current_focus.md): a ~291 ms latency floor eliminating every
sub-minute strategy, round-trip costs setting affordability at roughly four hours, and a solo
operator with small capital ruling out capacity-constrained approaches.

_(unwritten)_
