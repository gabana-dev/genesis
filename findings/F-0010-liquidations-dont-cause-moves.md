---
id: F-0010
title: Forced liquidation does not move price more than a volatility-matched random minute in the same hour
status: MEASURED
observation: 15m mean +40.07 bps in the forced direction against a matched control of 44.52 bps; no horizon clears both benchmarks
sample: 228 independent episodes >=$250k across 28 symbols (n=106 with price data), Binance market-wide, 2026-08-18 to 2026-08-20
method: CASCADE-1, contract frozen sha256 7dee22eed9cdaecb before any outcome; episodes not events; permutation null plus same-symbol same-hour control
evidence: research/cascade-1-result.md, market/cascade1.py
confidence: K1 met at 228 episodes, so this is not an underpowered null; three days, one venue, and only two of four declared benchmark tiers were implemented
market_gap: no liquidation product publishes a volatility-matched control
first_recorded: 2026-08-21
last_updated: 2026-08-21
supersedes: none
---

At 15 minutes the raw effect is large and would make a compelling screenshot: **+40 bps, 60% hit
rate, clearing a permutation null.** Take any other minute from the same hour in the same symbol
and you get **more** continuation.

Liquidations happen when markets are already moving. The move is the volatility; the liquidation
is a symptom of it.

**What this closes.** The cascade forecast product. The defensibility metric (F-0001) and the
cascade model both work and both attach to a phenomenon that does not measurably move price.

**What it does not touch.** F-0002 — the book thins to 0.846 during large moves — is a fact about
microstructure and stands independently.
