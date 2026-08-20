---
id: F-0006
title: Binance order-book behaviour under stress transfers to Hyperliquid
status: ASSUMED
observation: none — nothing has been measured on Hyperliquid
sample: none
method: n/a
evidence: research/ASSUMPTION-binance-physics-may-not-transfer.md
confidence: untested and load-bearing; hl2 began recording Hyperliquid l2Book at nSigFigs=3 on 2026-08-20 to settle it
market_gap: n/a
first_recorded: 2026-08-20
last_updated: 2026-08-20
supersedes: none
---

**The most dangerous category in the registry.** The cascade model calibrates depth evaporation on
three years of Binance data and applies it to Hyperliquid, which has HLP backstopping
liquidations, a different maker population, an order of magnitude less open interest, and
block-paced matching.

If Hyperliquid's book holds up better, our cascade depths are too pessimistic. If worse, too
optimistic — the dangerous direction for anyone acting on a forecast.

**No Hyperliquid cascade figure may be published without this caveat on its face until F-0006
moves to MEASURED or REFUTED.**
