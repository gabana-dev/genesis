# Decisions

The record of what was chosen and why. This folder is the backbone of provenance: every
principle, ontology entry, or commitment in the canon traces back to a decision record
here.

A decision record captures not just the choice but the reasoning and what was given up, so
a future collaborator can reconstruct *why* — not just *what*.

## Format

One file per decision: `YYYY-MM-DD-short-slug.md`, numbered if you prefer (`0001-...`).

```
# <Decision title>

**Date:** YYYY-MM-DD
**Status:** proposed | accepted | superseded by <link>
**Reversibility:** easy | costly | one-way

## Context
<the situation and question that forced a choice.>

## Decision
<what was chosen, stated plainly.>

## Reasoning
<why this and not the alternatives.>

## What we gave up
<the roads not taken, and what they would have offered.>
```

## The records

Maintained by the assistant as a factual index. A ratified decision that cannot be found is a
decision that gets lost — which has happened twice, so this list exists.

| | Decision | Status |
|---|---|---|
| [DR0001](0001-research-triage-reframe.md) | Research triage — no lab for anything already solved in the literature; the opportunity map (A–F) becomes the authority on what is worth researching | ratified 2026-08-08 |
| [DR0002](0002-close-the-genesis-research-program.md) | **Close the cognitive-architecture research programme.** The thesis is established science; the axiology question is retired as philosophy. No research direction is selected | ratified 2026-08-09 |
| [DR0003](0003-engineering-posture-real-data.md) | **Engineering against real, externally recorded environments is permitted**, labelled as engineering, claiming no novelty. §9 retains protocol discipline in full; §10 forbids a pre-planned roadmap | ratified 2026-08-09 |
| [DR0004](0004-close-rdb-1.md) | Close RDB-1; the holdout stays sealed and is not opened, now or later | ratified 2026-08-10 |
| [DR0005](0005-orientation-layer.md) | Build the orientation layer ([`../../status.py`](../../status.py)). **It reports; it does not decide** — no trial declared, no contract amended, no direction chosen | ratified 2026-08-18 |
| [DR0006](0006-no-prediction-without-a-consumer.md) | **No predictive experiment without a named consumer** — the contract must name the consumer, the decision changed, a do-nothing baseline and a wiring kill condition, or it is not declared | ratified 2026-08-18 |

The operational rules these produced are collected in
[`../../canon/operations.md`](../../canon/operations.md).

## Notes

- Authored by the researchers. AI maintains structure, links, and status pointers (e.g.
  marking a record superseded when a later one replaces it).
- A superseded decision is never deleted — it is marked and linked forward. The path stays
  visible.
