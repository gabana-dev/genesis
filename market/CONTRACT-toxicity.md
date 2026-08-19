# TOX-1 — is trader informativeness persistent, and does it survive to a horizon Genesis can reach?

**Status: FROZEN 2026-08-19, while the harvest is still running and before any of it has been
looked at.** No score, window, horizon, threshold, prediction or kill condition below may be
changed after this point. If a defect is found it is reported and recorded, not silently
repaired.

**Classification: IMPORT + BUILD.** Question A replicates Zhai (2026), arXiv:2608.04373. No
novelty is claimed for it. Question B is not in that paper and is the one that decides whether
any of this is usable.

---

## 1. Why this contract exists

Binance's trade stream carries no account information, which is why DIR-1's fee-tier
conditioner was discarded as unobservable and why T2.1 sat blocked for weeks. **Hyperliquid
names both counterparty wallets on every trade**, and its `userFillsByTime` endpoint pages
backwards through each wallet's history for free.

Zhai (2026) reports that informativeness is a **persistent wallet attribute**: rank correlation
**0.52** across adjacent ten-day windows, top decile **+2.20 bps** of ten-second markout against
bottom decile **−1.13 bps**.

If that replicates here, Genesis can see something no centralised venue exposes.

## 2. The two questions, and which one matters

**A — replication.** Does a wallet's informativeness rank persist from one ten-day window to
the next?

**B — reachability, and this is the decision.** Zhai measures **one-second** R². Genesis's
measured latency floor is **291 ms** and its reachable region is **one day**
([`CONTRACT-measurement.md`](CONTRACT-measurement.md)). **A signal with a one-second half-life
is not available to Genesis at any price.**

> **B asks: does the informativeness of the top decile survive to a horizon Genesis can act
> on?**

A is a prerequisite. **B is the experiment.** If A replicates and B fails, the honest finding is
*real but unreachable* — and that closes the line rather than inviting a search for a way
around latency.

## 3. Data

**Fills:** `~/genesis-evidence/hl-fills/fills.jsonl`, harvested from `userFillsByTime`, top 200
wallets by appearance, 22 days back. Each fill carries `crossed` (the venue naming the
aggressor), `px`, `sz`, `side`, `time`, `coin`, and also `closedPnl`, `startPosition`, `fee`
and `twapId`.

**Prices:** the `hl1` recording, `~/genesis-evidence/hl1/btc-hl1.jsonl` — Hyperliquid BTC
trades, hash-chained, recording since 2026-08-19.

### 3.1 Three scope limits, declared before anything is computed

**BTC only.** The harvest spans several coins; `hl1` records BTC trades alone, so markout is
computable only for BTC fills. Fills in other coins are counted and excluded.

**Markout is computed against the last TRADE price, not the mid.** `hl1` carries trades, not
the book. At the horizons in §5 on an actively traded instrument this is close, but it is an
approximation and is not called a mid anywhere in the results.

**The wallet sample is biased and the bias is known.** Wallets come from Genesis's own live
recording, so only wallets active in that window are visible; one that traded heavily earlier
and stopped is invisible. **Every result describes currently-active wallets, not the
population.** This is the whole difference between the free route and the paid archive, and it
must be restated on every reported figure.

## 4. The score

Following Zhai, per wallet, over a window:

```
alpha_w  =  sum( notional_e * markout_e ) / sum( notional_e )
```

over that wallet's **aggressive** fills only — `crossed == true`, which the venue asserts and
Genesis does not infer. `markout_e` is signed so that positive means the price moved the
wallet's way.

**Minimum 100 aggressive BTC fills in a window** for a wallet to be scored, as Zhai requires.
Wallets below it are counted and excluded, never scored on thin evidence.

## 5. The grid

**Windows:** two adjacent 10-day windows, W1 and W2, the most recent two fully covered by the
harvest. Fixed by the data, not chosen.

**Horizons:** 10 s, 60 s, 5 min, 1 h, 6 h, 24 h.

10 s is Zhai's, and is included for comparability alone. **1 h and beyond are the only horizons
Genesis could act on**, and 24 h is where its measured reachable region sits.

**Family TOX-1 = 1 persistence test + 6 horizon comparisons = 7 declared trials.** Fixed by this
section. Benjamini–Hochberg at q = 0.05 across the 6 horizon comparisons, with Bonferroni
α = 0.05/6 = 0.00833 reported alongside.

## 6. Endpoints

**A — persistence.** Spearman rank correlation of `alpha_w` at the 10 s horizon between W1 and
W2, over wallets meeting the minimum in both. Reported with a bootstrap 95% interval.

**B — reachability.** Wallets are ranked into deciles by W1 score at 10 s. **The ranking is
formed on W1 only and never re-formed.** Then, for each horizon in §5, the **W2** markout of the
top decile and of the bottom decile is reported, with a moving-block bootstrap interval.

The question at each horizon is whether the top-decile mean markout **excludes zero**.

**Secondary, non-substitutable:** the same decile split scored by `closedPnl` per unit notional
— realised profit rather than markout. Genesis has this and Zhai did not. It is reported for
description and is **not** the primary, because profit conflates information with inventory
management and exit timing, while markout isolates the information.

## 7. Predictions

- **T1.** A replicates in direction but **weaker than Zhai's 0.52** — between 0.20 and 0.45 —
  because our wallet sample is restricted to the most active traders, which compresses the
  range being correlated.
- **T2.** Top-decile W2 markout at 10 s excludes zero and is positive, in the region of Zhai's
  +2.20 bps.
- **T3. The advantage decays and is indistinguishable from zero by 1 hour.** This is the
  prediction the contract exists to test, and the one I expect to hold.
- **T4.** At 24 h neither decile is distinguishable from zero, and the two are not
  distinguishable from each other.
- **T5.** The `closedPnl` ranking correlates positively with the markout ranking but at less
  than 0.6 — they measure related but different things, and a wallet can be informed and still
  lose money on inventory.

## 8. Kill conditions

- **K1.** Fewer than 100 aggressive BTC fills in a window: the wallet is **excluded and
  counted**, never scored.
- **K2.** Fewer than 50 wallets qualifying in both windows: **decile analysis is not run**, and
  B is reported as unevaluable rather than computed on fewer than five wallets per decile.
- **K3.** If A's rank correlation is **below 0.20** or its interval includes zero, **B is not
  computed.** Zhai's finding has failed to replicate on this sample and a decile ranking built
  on an unstable score is not a ranking.
- **K4.** If no horizon at or beyond **1 hour** shows top-decile markout excluding zero, TOX-1
  reports **REAL BUT UNREACHABLE** — the signal exists and Genesis cannot act on it. That is a
  result. It does not license a search for lower latency, a different venue, or a shorter
  horizon, each of which needs its own declaration.
- **K5.** The sampling bias of §3.1 is restated on every reported figure. A result quoted
  without it is misreported.

## 9. Known limitations

**No book.** `hl1` records trades only, so markout uses trade prices (§3.1) and queue position
is unavailable.

**Latency is not simulated.** TOX-1 asks whether the information exists at a horizon, not
whether Genesis could have acted on it in time. Acting requires the 291 ms floor plus decision
time, and that is a separate question this contract does not answer even if B succeeds.

**Two windows.** Persistence over one transition is what Zhai measured and what the harvest
supports. It is not evidence of stability over months.

**One asset, one venue, 22 days.**

## 10. Out of scope

No strategy, no signal construction, no sizing, no P&L for Genesis, no live order. TOX-1 asks
whether a published property of traders exists here and whether it lasts long enough to matter.
Everything downstream needs a contract that does not yet exist.
