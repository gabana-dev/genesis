# Current focus

**One thing at a time. This file names it.**

---

## Now

**The research program is closed. The laboratory remains capable of doing disciplined
engineering.**

Two decision records were ratified on 2026-08-09 and together they define the whole of the
current state:

- [`../research/decisions/0002-close-the-genesis-research-program.md`](../research/decisions/0002-close-the-genesis-research-program.md)
  — **RATIFIED.** The cognitive-architecture thesis is retired (established science,
  independently re-derived); the axiology/install question is retired as philosophy, not a
  Genesis objective; the Research OS is useful but its novelty is unvalidated and unclaimed; the
  toy-milestone sequence is closed at M2; PsTally is not a Genesis phase. **No research
  direction is selected.** Reopening requires a genuinely unresolved problem arriving from real
  constraints and surviving the prior-art gate — nothing internal reopens it.
- [`../research/decisions/0003-engineering-posture-real-data.md`](../research/decisions/0003-engineering-posture-real-data.md)
  — **RATIFIED.** Engineering against real, *externally recorded* environments is permitted,
  labelled as engineering, claiming nothing. Genesis-authored simulators remain barred. Every
  milestone states its import/build classification before it runs. Accumulated engineering is
  never retrospectively recast as research.

**Active work: RDB-1**, the real-data bridge.
[`../research/experiments/0006-rdb-1-real-data-bridge.md`](../research/experiments/0006-rdb-1-real-data-bridge.md).
Classification **import + build, no novelty claimed**. Public AEMO NSW1 data under a frozen
protocol. Development period complete; **the holdout is unopened.**

## What RDB-1 established (development period only)

- **Adaptation matters, decisively.** Rolling 26 weeks beats an expanding window by +101.59 MAE,
  block-bootstrap 95% [+65.20, +141.72]. Stable across every year and season; largest in summer.
- **The model does not reliably beat "yesterday at this clock time."** Rolling vs persistence
  straddles zero (−15.96, [−49.32, +19.51]). Expanding fails to beat seasonal-naive at all.
- **Slice and specification are separable.** The training slice moved accuracy ~24% and moved
  calibration essentially not at all. Both arms carry the same fat-tail signature: intervals too
  wide at 50%, too narrow at 95% — on a smooth, well-behaved series.
- **Nothing consumes the forecast.** No cost, no decision, no consequence for being wrong — the
  condition [`0005`](../research/experiments/0005-sparse-observation-decision-relevance.md) §E
  identified as making usefulness undemonstrable.

## Open — the researcher's, not yet decided

1. ~~Whether to open the RDB-1 holdout.~~ **CLOSED 2026-08-10** by
   [`../research/decisions/0004-close-rdb-1.md`](../research/decisions/0004-close-rdb-1.md).
   RDB-1 answered its question; no design was ever frozen, so the holdout would evaluate
   nothing. It stays sealed and the lock stays in place — a holdout kept open indefinitely
   stops being one.
4. **What the next capability is.** Chosen from what the evidence exposed, one step at a time.
   **No sequence is pre-authorized** — DR0003 (10) forbids adopting a roadmap of future
   milestones in advance, and DR0001 classifies the capability graph as **F — abandon**.

**Environment search — one candidate investigated and closed.** The NEM battery environment was
studied and the study is closed:
[`../research/nem-battery-environment-study.md`](../research/nem-battery-environment-study.md).
Finding: the **consequence** is genuinely external (money someone paid, computed from published
settlement prices, against an industry benchmark), but the **dynamics** cannot be obtained
without authoring them — battery state of charge is not published anywhere in AEMO's public data
model and must be integrated through an assumed efficiency, parasitic-loss rate and initial
condition. SOC is the coupling that makes the problem sequential, so authoring it means
authoring the mechanism. **Answer to the clean test: no.** Whether to use the environment anyway
under declared assumptions is undecided and is the researcher's.

**Second candidate investigated and closed — Kalshi mechanically-settled price markets.**
[`../research/kalshi-mechanical-settlement-environment-study.md`](../research/kalshi-mechanical-settlement-environment-study.md).
**The authorship test passes**: settlement is a fixed 60-second arithmetic mean of the CF
Benchmarks Bitcoin Real Time Index, computed by a regulated administrator under a published,
versioned methodology; agent state is exactly accounting-derived. **It fails on record and
access instead** — Kalshi publishes no historical order-book depth (third-party sampled
reconstructions only, from 2026-01-07), and the reference's historical values are licence-gated,
so the consequence cannot be independently reproduced. **Answer to the central question: no**,
for historical reconstruction. Nothing selected or rejected.

An environment distinction is on record but selects nothing:
[`../research/journal/2026-08-09-real-data-is-not-a-simulator.md`](../research/journal/2026-08-09-real-data-is-not-a-simulator.md)
notes that the environment-first gate ruled on Genesis-*authored* simulators and never ruled on
externally recorded data. DR0003 permits considering a harder recorded target; **it selects
none.**

## Direction (researcher, 2026-08-10)

**Genesis is for financial markets. Everything built from here pushes toward paper trading**,
with the foundation and architecture orchestrated properly first. Market literacy is the
researcher's own task and is not a Genesis work item.

### Hard constraints — measured, not assumed

| Constraint | Value | What it eliminates |
|---|---|---|
| Latency floor, Nairobi to Binance | **~291 ms**, median ~430 ms | **all sub-minute strategies** — HFT, latency arb, microstructure scalping |
| Round trip cost | 0.20% spot · 0.10% futures taker · 0.04% futures maker | anything whose edge is smaller than its cost |
| BTC daily volatility | ~1-2% | sets the horizon at which cost is affordable |
| Solo team, small capital | — | capacity-constrained and breadth strategies |

**Surviving design space: horizons of hours to days, few instruments studied deeply,
counterparties who are structurally price-insensitive.** The latency figure came from the
BAV-1 skew investigation and is the most strategically useful measurement the project owns.

### Phase gates

0. Trustworthy observation — **COMPLETE.** BAV-1, run 3, 2026-08-10:
   [`../research/experiments/0007-bav-1-book-agreement-validation.md`](../research/experiments/0007-bav-1-book-agreement-validation.md).
   The completeness label predicts agreement with an independent channel — 97.5% vs 66.7% in
   the pre-registered stratum, Fisher exact p = 0.0165. Fidelity and self-knowledge measured
   separately and not merged.
1. Market literacy — the researcher's own
2. **Measure the environment, do not trade it** — **ACTIVE.** Contract drafted, not frozen:
   [`../market/CONTRACT-measurement.md`](../market/CONTRACT-measurement.md) — **FROZEN**
   2026-08-10, `sha256 f74e8cf28f48fdd636b8ed0189a3522bdad136c8283fe222ef6a7c0e46b395d2`.
   Three separated questions: is there directional structure (Q1), does it survive costs (Q2),
   can Genesis capture it (Q3 — **out of scope, needs the fill simulator**). Headline
   deliverable is the break-even hit-rate table `p* = 1/2 + c/2m` per horizon and fee tier.
   Note the correction recorded there: the constraint table below counts **fees only** and
   therefore understates true round-trip cost.
   **RESULT 2026-08-10:** [`../research/experiments/0008-measure-1-cost-of-being-right.md`](../research/experiments/0008-measure-1-cost-of-being-right.md).
   Q1 finds linear structure at minute scale (VR 0.89 at 60m, p 9e-06, same direction in 8 of
   8 years) and none at 4h+. Q2 finds affordability only at 4h+. **The two do not overlap.**
   Kill condition not triggered -- 4h futures maker 58.7%, 1d futures maker 52.8%. Spread is
   one tick and impact at $10k is 0.00002%, so fees are 500-2,000x the non-fee cost:
   **cost binds, depth does not.** Q3 (fills, latency, adverse selection) entirely unmeasured.
   **Power correction (§8):** the 4h+ null is *absence of evidence*, not evidence of absence —
   at daily scale only VR ≤ 0.851 was detectable, and 80% power against VR = 0.95 would need
   **68 years** of history. The overlap question is **open**, and the variance ratio cannot
   ever settle it at that horizon. A structural limit of the same kind as the 291 ms floor.
   **Long Q3 recording started 2026-08-10**, `~/genesis-evidence/q3/btcusdt-q3.jsonl`,
   7 days, ends ~2026-08-17 17:00.
3. **Phase 3 open — EXEC-1**, [`../market/CONTRACT-execution.md`](../market/CONTRACT-execution.md),
   **FROZEN 2026-08-10 before the data exists**,
   `sha256 11c6a8ec684a69a453d450d4500b2bae60ee05fcc8067912598855ad911cb351`. Answers Q3:
   what execution costs, and what portion of the 3 bps maker advantage survives adverse
   selection. Instrument [`../market/fills.py`](../market/fills.py) built and tested first.
   Predictions X1-X7 and the four decision trials are declared in the ledger and outstanding.
   **Nothing to do until the recording completes.**
3. One decision, one real cost, against a do-nothing baseline
4. Paper trading at deployable size — fills from recorded depth, latency from the measured
   distribution, using the existing DECISION -> INTENT -> EXECUTION schema
5. Pre-registered hypothesis search — trial counter, deflated Sharpe, held-out untouched
6. Edge-decay monitoring — the completeness machinery pointed at strategies
7. Real capital, small

**LLM enters at Phase 5** for hypothesis generation, anomaly explanation, unstructured events
and the research record. **Never the signal.** **Agents: none until Phase 5**, then one at a
time, each justified by a measured decision the current system gets wrong.

### Standing questions for any strategy proposal

- Who is on the other side, and why are they losing? No answer means noise, or we are the
  ones being harvested.
- How many trials have been run? Two hundred tests produce several brilliant-looking accidents.
- What does it cost at the fee tier actually available?

**Largest unbuilt component: the fill/execution simulator.** It is where edges die.

## Kill criteria (researcher, 2026-08-09)

Stated so that abandoning a line of work is a planned outcome rather than a failure, and so
that "intellectually interesting" is never sufficient reason to continue.

| Condition | Response |
|---|---|
| Live validation reveals the recorder is fundamentally flawed | **Fix it** |
| The recorder works beautifully but no meaningful application emerges | **Reconsider the application** |
| An application requires assumptions Genesis cannot legitimately observe | **Reject it** |
| The system grows more complex without producing evidence | **Stop and simplify** |
| An established product already does exactly what Genesis does | **Do not pretend we invented it** |
| A genuinely valuable capability is found | **Investigate commercialisation aggressively** |

These govern the current engineering line. They are recorded here rather than in a new
document because the project's stated priority is less documentation and more real
connection. If they should bind at the decision layer, that is a decision record for the
researcher to author.

## What "better" means

A milestone succeeds when the system becomes **more capable, more adaptive, more measurable, or
more grounded in reality** — not when a score improves. A well-measured failure exposing a real
limitation is a success. A score improvement obtained by choosing a friendlier target is not.
(DR0003, "What better means here".)

## Standing rules still in force

- **Prior-art gate first.** Anything classified import (A) in
  [`../research/prior-art-and-opportunity-map.md`](../research/prior-art-and-opportunity-map.md)
  gets no laboratory.
- **Environment-first gate** (DR0002, preserved there, deliberately **not canon**). Full force
  against any environment Genesis would author.
- **Protocol discipline**, undiminished for engineering: contract fixed in advance, checksummed
  snapshots, leakage controls, serious baselines, paired intervals on per-origin records,
  technical holdout locks, and disclosure of which analysis choices were fixed when.
- **The form/substance boundary** ([`collaboration.md`](collaboration.md)). Unchanged by any of
  the above. Claude does not author substance or set direction.

## Superseded, kept on record

The capability-construction gate and the frozen Method of Discovery remain in the history
(journal entries of 2026-08-07 and the `0001` triage) but no longer govern selection: the
prior-art rule subsumes them, and no laboratory runs for anything classified import.

## Not in focus

- **Abandoned (F):** primitive-counting; the "differentiator sentence" search; re-deriving
  established estimation/control theory as discovery; the capability graph as a research roadmap.
- **Import if needed (A), never as research:** dynamic-state filtering, unsupervised
  observation-model learning, closed-loop RL, causal inference.
- **Frozen:** `0002` Emergence, `0003` Time, `constitution.md`, `ontology.md`, the caring fork.
- **Open but unchosen (D/E):** Research-OS validation; reflexive/performative decision-making;
  the axiology/install problem. Retired as Genesis objectives by DR0002.

---

*Last updated: 2026-08-10.*
