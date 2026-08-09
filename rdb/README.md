# RDB-1 — Real-Data Bridge

**Classification: IMPORT + BUILD — engineering validation. Not research. No novelty claimed.**

The first Genesis milestone whose environment was not authored by Genesis. It exists to
answer one question:

> Does the imported state-estimation and adaptation machinery survive contact with a real,
> untuned sequential dataset, under an evaluation protocol that transfers directly to
> market data?

A negative answer is a valid outcome and will not be rescued.

## Data and licence

**Source: AEMO.** NEM public price & demand, region NSW1, monthly CSVs from
`https://aemo.com.au/aemo/data/nem/priceanddemand/`.

Licence verified before implementation — AEMO Copyright Permissions:

> "AEMO confirms its general permission for anyone to use AEMO Material for any purpose,
> but only with accurate and appropriate attribution of the relevant AEMO Material and
> AEMO as its author. You do not need to obtain specific permission to use AEMO Material
> in this way."

Download, storage, processing and publication of derived results are therefore permitted,
conditional on attribution. Required attribution string is in `config.ATTRIBUTION`.
(The live terms page sits behind Cloudflare and returns 403 to non-browser clients; the
text above was read from the Internet Archive snapshot of 2026-07-29.)

## Two data facts established from the raw files, not assumed

1. **The native resolution changes.** Verified row counts: 2021-08 = 1,489 rows and
   2021-09 = 1,441 (30-minute); 2021-10 = 8,929 (5-minute). The change coincides with the
   5-minute settlement go-live and falls *inside* the development period. Months through
   2021-09 are used as-is; from 2021-10 exactly six 5-minute intervals are aggregated per
   30-minute period. Tested explicitly at the September/October join.
2. **NEM market time does not observe DST.** April 2020 has exactly 1,440 intervals and
   October 2021 exactly 8,928 — no missing or duplicated hours at DST boundaries. This
   removes the correctness hazard flagged in the design review.

Timestamps are **interval-ending**: the row labelled 00:30 covers 00:00–00:30. Treating
them as interval-starting would leak 30 minutes of future into every forecast. Verified
per month by `series.verify_interval_ending`.

## Protocol (frozen by contract)

| | |
|---|---|
| Target | `TOTALDEMAND`, NSW1, 30-minute canonical series |
| Horizon | 48 steps (24 hours), daily rolling origins |
| Development | 2015-01 → 2022-12 |
| Holdout | 2023-01 → 2026-06 — **not downloaded, not readable** |
| Baselines | seasonal-naive (serious), persistence, calendar OLS |
| Model | one `statsmodels` structural time-series spec, Kalman-filtered |
| Adaptation test | expanding-window vs rolling-window refit — **no changepoint library** |
| Metrics | MAE, RMSE, skill vs seasonal-naive; 50/80/95% coverage; CRPS; year/season breakdowns |

## Holdout protection

Technical, not disciplinary. The holdout months are **not downloaded**, and both
`ingest.ingest("holdout")` and `series.build("holdout")` raise `HoldoutLocked` unless the
freeze marker `rdb_data/DESIGN_FROZEN` exists. Development and model-selection code cannot
reach it accidentally.

## Layout

| File | Role |
|---|---|
| `config.py` | frozen contract constants, licence, holdout lock |
| `ingest.py` | deterministic download, sha256 manifest, schema validation |
| `series.py` | resolution transition, interval-ending validation, canonical series |
| `baselines.py` | persistence, seasonal-naive, calendar OLS |
| `harness.py` | rolling origins, metrics, calibration, stability breakdowns |
| `model.py` | imported state-space model (no Kalman implementation of our own) |
| `run.py` | development runner |

Checks: `tests/test_rdb_series.py`.

## What is imported vs built

**IMPORT:** Kalman/structural time series (Kalman 1960; Harvey 1989; Durbin & Koopman
2012) via `statsmodels`; naive and seasonal-naive benchmarks (Hyndman & Athanasopoulos);
CRPS (Gneiting & Raftery 2007). **BUILD:** ingestion, snapshotting, canonical series
construction, the evaluation harness, reporting.

**Genesis code reused: none.** The existing `src/` implementations are discrete-state and
1-bit; nothing transfers. What transfers is the experimental discipline.

## Transfer to the market phase

The harness is target-agnostic. Pointing it at AEMO `RRP` — a real market price in the
same files, on the same timestamps — requires changing a column name, not the harness.
