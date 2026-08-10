# DR0004 — Close RDB-1; the holdout stays sealed

**Date:** 2026-08-10
**Status: DECIDED by the researcher.** Recorded here on their instruction of 2026-08-10:
*"Also formally close RDB-1 so it isn't left hanging."*

Supersedes the open item "whether to open the RDB-1 holdout" carried in
[`../../ai/current_focus.md`](../../ai/current_focus.md) since 2026-08-09.

---

## The decision

**RDB-1 is closed. The holdout (2023-01 → 2026-06) is not opened, now or later.**
The technical lock stays as it is: the months are not downloaded, and `ingest`/`series` raise
`HoldoutLocked` unless `rdb_data/DESIGN_FROZEN` exists. That file is not created.

## Why

RDB-1 asked whether imported state-estimation and adaptation machinery survives contact with a
real, untuned sequential dataset ([`../experiments/0006-rdb-1-real-data-bridge.md`](../experiments/0006-rdb-1-real-data-bridge.md)).
It answered:

- **Adaptation matters, decisively.** Rolling 26 weeks beat an expanding window by +101.59 MAE,
  block-bootstrap 95% [+65.20, +141.72], stable across every year and season.
- **The model does not reliably beat "yesterday at this clock time."** Rolling vs persistence
  straddles zero.
- **Slice and specification are separable**, and both arms carry the same fat-tail signature.
- **Nothing consumed the forecast.** No cost, no decision, no consequence for being wrong.

That is a complete answer to the question asked. The holdout was reserved for a *final*
evaluation of a design that had been frozen — and no design was ever frozen, because the
project moved to a different environment before one was chosen.

Opening it now would evaluate nothing. There is no candidate to test, no decision that consumes
the output, and no successor work in the NEM environment: the environment study closed with the
finding that battery state of charge is not published and would have to be authored
([`../nem-battery-environment-study.md`](../nem-battery-environment-study.md)). The market
direction of 2026-08-10 supersedes it.

## Why it is not merely paused

A holdout that is kept open indefinitely stops functioning as a holdout. Its value comes
entirely from the credibility of never having been looked at, and that credibility decays with
every month it sits available to a project that has an incentive to look. Closing it while it
is still clean preserves the one thing it was for.

Should the NEM environment ever be reopened with a frozen design and a decision that consumes
the forecast, the holdout is intact and the lock is honest. Nothing is destroyed by this
decision; the option is simply no longer carried as open work.

## What is preserved

- The experiment record, the evidence, and the protocol stand unchanged.
- The finding that **adaptation matters** is the transferable result and is not retracted.
- The classification stands: **import + build, no novelty claimed** (DR0003).
- The observation that RDB-1 had no consumer for its forecast remains the reason the project
  went looking for an environment with a priced consequence — which is how it arrived at
  markets.

## What this does not decide

Nothing about the market direction, MEASURE-1, or any future environment. This closes one
experiment and one open question, and selects nothing.
