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

## Notes

- Authored by the researchers. AI maintains structure, links, and status pointers (e.g.
  marking a record superseded when a later one replaces it).
- A superseded decision is never deleted — it is marked and linked forward. The path stays
  visible.
