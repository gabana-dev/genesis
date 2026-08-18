# DR0006 — No predictive experiment without a named consumer

**Date:** 2026-08-18
**Status: RATIFIED by the researcher**, 2026-08-18, on their instruction: *"ratified"*.
**Reversibility:** easy in code, costly in discipline. Rescinding it would remove the only
forcing function between measuring and committing.

> **Provenance.** The rule was proposed by an outside reader of the public repository on
> 2026-08-18, who observed that RDB-1 died because nothing consumed its forecast and that the
> same pattern could repeat a third time unless the consumer were named in the contract
> *before* the experiment ran. The condition it formalises was already recorded in this
> repository twice, as a finding. This record converts a finding into a constraint. Drafted by
> the assistant; the researcher authors, edits or rejects.

---

## Context

The project keeps producing measurements that nothing acts on.

**It has been recorded twice, as a diagnosis, and never as a rule.**

[`0005-sparse-observation-decision-relevance.md`](../experiments/0005-sparse-observation-decision-relevance.md)
§E identified the condition: a forecast with no cost, no decision and no consequence for being
wrong makes usefulness **undemonstrable**. Not unproven — undemonstrable, because the
experiment contains nothing that could show it.

[`0006-rdb-1-real-data-bridge.md`](../experiments/0006-rdb-1-real-data-bridge.md) then met it
head on:

> **Nothing consumes the forecast.** There is no cost, no decision, and no consequence attached
> to being wrong — the exact condition `0005` §E identified as making usefulness
> undemonstrable. RDB-1 measures forecast quality, not decision quality.

RDB-1 was closed for this reason ([DR0004](0004-close-rdb-1.md)), and its own closure record
names it as *"the reason the project went looking for an environment with a priced
consequence"*.

So the diagnosis was correct, written down, and acted on **once** — by changing environment.
It was never made binding, which means nothing prevents the next predictive experiment from
arriving in the same condition. The measurement line since (MEASURE-1, EXEC-1) has been
descriptive rather than predictive, so the gap has not yet been tested.

**And the project already knew the answer.** The phase list carried in
[`../../ai/current_focus.md`](../../ai/current_focus.md) names the phase after EXEC-1 as:

> *One decision, one real cost, against a do-nothing baseline*

That is this rule, written by the researcher, and then lost track of — because it lives in a
file the collaboration contract designates as working memory rather than canon (see
[DR0005](0005-orientation-layer.md) and the C5 entry in
[`../CURRENT-STATE-2026-08-18.md`](../CURRENT-STATE-2026-08-18.md)).

## Decision

**No predictive experiment may be declared in the ledger unless its frozen contract names what
will consume the prediction.**

The contract gains a mandatory section, frozen with the rest of it, stating four things:

| | |
|---|---|
| **Consumer** | The existing code path that takes this output, by file. Not a plan to build one. |
| **Decision changed** | What happens differently when the prediction says X rather than Y. |
| **Do-nothing baseline** | What the consumer does today, without the prediction. The comparison the experiment is against. |
| **Wiring kill condition** | What result would mean *do not connect it* — declared before the data, like every other kill condition. |

**The enforcement is a refusal: if the consumer cannot be named, the experiment is not
declared.** Not deferred, not run descriptively and reconsidered later. Not declared.

### What this does not forbid

**Descriptive measurement remains fully permitted** and needs no consumer. MEASURE-1 measured
the environment; EXEC-1 measured execution economics; the exploration studies measured decay.
None of them predicted anything and none would be affected. The ledger already distinguishes
these — descriptive measurements are recorded as CONTEXT, not trials
(`CONTRACT-execution.md` §7) — and this rule attaches to the same boundary.

The rule binds a specific claim: *this output tells you something about a future state.* That
is the claim that has twice arrived with nothing to receive it.

## Why a rule rather than continued good judgement

Because good judgement already failed twice at exactly this point, and the second failure
happened **after** the first was written down. A diagnosis in an experiment record is read once,
by whoever wrote it. A required contract section is read every time a contract is frozen, which
is the moment the decision is actually made.

It is the same mechanism as the trial ledger: the ledger works because declaring happens before
running and cannot be undone. This works because naming the consumer happens before freezing
and cannot be added afterwards to rescue a result that turned out interesting.

## What it costs

**It will block work that looks worth doing.** Some predictive question will arrive with no
plausible consumer, and this rule says do not run it — even if the question is interesting, and
even if the data is already recorded. That is the intended cost. "Intellectually interesting"
is already listed as insufficient reason to continue in the standing kill criteria.

It also front-loads effort: naming a consumer and a do-nothing baseline is real design work,
done before any result is known, when motivation is lowest.

## Worked example — not an adoption

If the book-state direction (D1 in [`../CURRENT-STATE-2026-08-18.md`](../CURRENT-STATE-2026-08-18.md))
were ever chosen, the section would read approximately:

- **Consumer:** [`../../market/fills.py`](../../market/fills.py) and
  [`../../market/exec1.py`](../../market/exec1.py) — the resting-order lifecycle already built
  and calibrated for EXEC-1.
- **Decision changed:** whether to hold or withdraw a resting order as conditions change,
  rather than always holding to a fixed TTL.
- **Do-nothing baseline:** EXEC-1's declared grid — a fixed 300 s TTL, no adaptation — whose
  adverse-selection outcome is already measured at 39.07% of the maker advantage lost.
- **Wiring kill condition:** if adaptive holding does not beat the fixed TTL on that measure,
  the predictor is not connected regardless of its accuracy.

That the consumer already exists in code, calibrated, with a measured baseline, is the property
this rule is designed to require. **Recording it here selects nothing.** No direction is chosen
by this decision record.

## What this does not decide

Nothing about which direction Genesis takes next, nothing about D1, D2 or D3, and nothing about
whether any predictive experiment should be run at all. It constrains the form of the contract
if one is ever written.
