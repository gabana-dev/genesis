# Findings

A **Finding** is something Genesis believes, with a status, an evidence base, and a history of
being wrong.

The repository has 47 research documents and, before this, no way to ask *"what do we actually
believe right now, and how strongly?"* Documents record what happened on a day. Findings record
what survives.

## Why this exists, concretely

On 2026-08-19/20, four claims of mine inverted inside two days:

| claim | what it turned out to be |
|---|---|
| the wallet universe is exhausted at 20.24% coverage | 53.3% on a properly aged universe |
| Coinglass is free | $35–879/month |
| nobody publishes data-coverage metrics | 0xArchive ships them via API |
| nobody sells per-wallet account state | HyperTracker does, with 16 months of history |

Each was asserted confidently, inherited by the next document, and looked better established with
every restatement. **In a pile of documents that is invisible. In a registry with a status field
it is a state change with a date on it.**

## Status values

| status | means |
|---|---|
| `MEASURED` | established by a measurement that could have come out otherwise |
| `PRELIMINARY` | measured, but on a sample too small or too narrow to lean on |
| `ASSUMED` | believed and load-bearing, **not** tested — the most dangerous category |
| `REFUTED` | we believed it, we were wrong, and the correction is recorded |
| `SUPERSEDED` | replaced by a better measurement of the same thing |

**`REFUTED` findings are never deleted.** A registry that only keeps its wins is a marketing page.

## The rule this enforces

> *"Nobody publishes X"* is a fact about the market.
> It is **never** evidence that X can be known.

Those are separate fields here — `market_gap` and `evidence` — precisely so the first can never
quietly become the second. That failure has a name in this project: letting the product thesis
become the evidence.

## Format

One file per finding, `F-NNNN-slug.md`, with the front matter block shown in
[`TEMPLATE.md`](TEMPLATE.md). Machine-readable form is generated, never hand-written —
see `findings/index.json`.
