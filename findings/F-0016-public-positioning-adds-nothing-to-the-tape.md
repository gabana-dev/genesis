---
id: F-0016
title: Across six years, none of eight public market-state variables separates forward trading conditions once trailing realised range is held constant
status: PRELIMINARY
observation: "band-controlled lift for all eight candidates sits between 0.914 and 1.129 in raw form, and z-scoring each against its own 30-day history collapses every one toward 1.000 (1.129 to 1.039, 1.126 to 1.052, 0.914 to 0.964). The raw long/short lift reverses sign by year: 1.170, 0.990, 0.948, 0.869, 1.164, 1.232, 1.178 for 2020 through 2026"
sample: 66,397 hours of BTCUSDT, ~51,000 usable per candidate; Binance 5-minute metrics from 2020-09 joined to 1-minute klines
method: "outcome is realised range over the following 24h; control is realised range over the previous 24h, banded; inside each band the candidate is split at its own median and the ratio of median forward ranges taken, then averaged across bands by weight"
evidence: market/screen.py
confidence: 24h windows stepped hourly overlap ~24-fold, so the effective sample is nearer 2,000 than 51,000 and a residual lift of 4-5% is far inside the noise. One venue, one asset, one horizon, one outcome family. A screen, not a pre-registered test — its authority is only to eliminate
market_gap: none. Every variable here is public and anyone could run this; that it has apparently not been run is not the same as it being ours
first_recorded: 2026-08-22
last_updated: 2026-08-22
supersedes: none
---

The research question had been reframed, correctly, from *"what liquidation feature can we build"*
to *"what information does a leveraged trader lack?"* — with the suggestion that the product might
be a **decision framework** rather than a number:

> *Volatility: elevated · Open interest: elevated · Funding: positive · Concentration: elevated*
> *→ "Leveraged longs are taking more risk than they were 24h ago."*

That is a testable proposition, so it was tested before it was designed.

## The screen

Eight candidates, against forward 24-hour realised range, **controlled on trailing 24-hour range**
— the control CASCADE-1 lost to. **The outcome is deliberately not price direction**: F-0005
measured that direction at this horizon needs 4,900 independent observations, so any screen
against it is unpowered before it starts. Trading *conditions* are the one outcome family this
project has ever beaten a control on (IMPACT-1).

| candidate | R² vs trailing | lift |
|---|---|---|
| OI level (z, 30d) | 0.017 | 0.972 |
| OI change 24h | 0.010 | 1.047 |
| OI change 1h | 0.000 | 1.022 |
| OI / trailing range | 0.252 | 0.834 |
| top traders L/S (size) | 0.011 | 0.914 |
| top traders L/S (count) | 0.030 | **1.126** |
| all accounts L/S | 0.024 | **1.129** |
| taker buy/sell ratio | 0.004 | 1.003 |

**Lift 1.00 means the candidate adds nothing the trailing tape already said.**

`OI / trailing range` is excluded rather than celebrated: it is trailing range in the denominator,
so inside a band it is mechanically anti-correlated with the control. Its R² of 0.252 against the
control — an order of magnitude above every other candidate — is that contamination, not a signal.

## The two survivors did not survive

Long/short ratio looked like the exception at ~1.13, with almost no correlation to the tape. Two
checks killed it.

**It is a level, and the level marks a regime.** Z-scored against its own 30-day history, the lift
collapses to **1.039** and **1.052** — and with 24-fold overlapping windows, a 4% lift is far
inside the noise.

**And the raw direction reverses by year.**

| 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| 1.170 | 0.990 | 0.948 | **0.869** | 1.164 | 1.232 | 1.178 |

Below 1 in 2022–23, above it in 2024–26. **A variable whose sign flips by year is describing the
regime, not the next 24 hours.** Split at a six-year median, "unusually long" mostly means "it is
2021" — and that is why the raw number looked informative.

## What this eliminates

The dashboard of adjectives. *"Open interest: elevated · Positioning: crowded"* is a percentile
dressed as an insight; on this evidence the percentile does not know anything about the next day
that the last day did not already say. Shipping it would be `product/IA.md §7`'s forbidden risk
rating with better typography.

## What it does not eliminate, and this is the important half

**Every variable screened here is public.** Binance publishes all eight, free, and anyone can run
this. Their failure says nothing about the quantities that are actually ours — per-wallet
`withdrawable`, position concentration, exposure measured against the standing book (F-0014) —
because **those cannot be screened yet.** The per-wallet archive is three days old and this test
needed six years.

So the honest reading is narrow and it points somewhere specific: **the public tape has been
searched and it is empty at this horizon. The unsearched ground is the archive we are still
building, and the only way to search it is to keep collecting.**

That is an argument for patience, not for another feature.
