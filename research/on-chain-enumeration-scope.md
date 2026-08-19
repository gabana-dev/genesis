# Scoping on-chain account enumeration: what it would take to fix coverage

**Date:** 2026-08-19
**Question:** LIQ-2 reached 20.24% coverage from a trade-derived wallet universe and
[the tail is empty](liq-2-k2-fired-coverage-20pct.md). Can enumerating accounts from the
Hyperliquid L1 reach materially higher — and at what cost?

**This is infrastructure scoping, not a contract.** No hypothesis is tested here and nothing
below licenses re-reading LIQ-2's killed secondary.

---

## 1. The endpoint exists, and it is not the documented info API

Found by probe, not documentation:

```
POST https://rpc.hyperliquid.xyz/explorer   {"type": "blockDetails", "height": N}
  -> {"blockDetails": {"height", "blockTime", "hash", "proposer", "numTxs",
                       "txs": [{"time", "user", ...}]}}
```

`api.hyperliquid.xyz/info` returns **422** for this type and `api.hyperliquid.xyz/explorer`
returns **404** — the host matters. A second endpoint, `{"type": "userDetails", "user": ...}`,
also works and returns a wallet's transactions, but it is per-user and so cannot enumerate.

**Every transaction carries a `user` address**, so the L1 is in principle a complete account
index — every account that ever acted appears.

## 2. Measured, not assumed

| quantity | measured |
|---|---|
| chain tip | **~530,000,000** blocks |
| chain block rate | 4.84 blocks/s |
| **sustained fetch rate** | **0.08 blocks/s** (~12.5 s/block, after 429 backoff) |
| transactions per block | 369 mean |
| **distinct users per block** | **16 mean** |
| distinct users from 25 sampled blocks | 399 |

The fetch rate is the whole story. The explorer endpoint is aggressively rate-limited — an
unthrottled binary search for the chain tip triggered 429s within seconds, and the sustained
figure above is what survives backoff.

## 3. The full-history scan is dead on arrival

```
530,000,000 blocks / 0.08 blocks per second  =  ~210 years
```

Even a 12× improvement in throughput leaves **17 years**. Complete enumeration is not merely
expensive, it is impossible at any effort we can apply. **That option is closed and should not be
revisited.**

## 4. What a bounded recent-window scan buys, and its central weakness

Sampling recent blocks is affordable: 25 blocks yielded 399 distinct addresses in 5 minutes.
Naive extrapolation suggests ~1,250 blocks over ~4.3 hours might yield on the order of 20,000
addresses — **but that is an upper bound and probably a bad one.** New-address yield per block in
the sample decayed hard (92, 1, 29, 13, 25, 0, 87, 2, 9, 6, …), which is the signature of a small
set of repeat actors dominating the tape. **The saturation curve has not been measured and the
extrapolation should not be trusted until it is.**

**The deeper problem is that this does not escape the bias that killed LIQ-2.** Scanning *recent*
blocks finds *recently active* addresses — the same population our trade tape already gave us.
A wallet that opened a position eight months ago and has not touched it since only appears in old
blocks, and old blocks are precisely the part §3 rules out.

So on-chain enumeration is **not** the "fundamentally different wallet source" it looked like. It
is a wider net over the same water.

## 5. A second ceiling: discovery is not the binding constraint anyway

Suppose enumeration handed us 20,000 addresses tomorrow. Each still needs a
`clearinghouseState` call at the measured **1.585 s/wallet**:

| universe | one full scan |
|---|---|
| 5,395 (today) | 2h22m |
| 13,600 | **6h00m — the cadence ceiling** |
| 20,000 | 8h48m |
| 50,000 | 22h |

**A 6-hour deep-scan cadence cannot cover more than ~13,600 wallets**, whatever enumeration
finds. Beyond that, discovery and tracking have to separate: an occasional wide discovery pass
that only ranks, and a frequent scan of the top N.

That is already the LIQ-2 architecture, and the concentration numbers say it costs almost
nothing — **the top 300 wallets hold 97.8% of scan-set notional.** So the design survives; only
the discovery pool would change.

## 6. The free win nobody noticed

`recorder/hyperliquid.py` records with `coin="BTC"`. **The universe is BTC traders only.**

A wallet that trades ETH, SOL or HYPE and holds a BTC position is invisible to us — and the
harvest shows these wallets are heavily multi-asset (722k BTC fills, but also 132k ETH, 71k HYPE,
46k SOL). Recording trades across all assets is close to a one-line change and widens the wallet
net at no marginal cost.

**It is forward-only** — it widens future recordings, not the existing universe — so it helps the
archive, not today's coverage.

## 7. The decisive test, and it is cheap

Everything above turns on one unknown: **is the missing 80% of open interest held by dormant
wallets, or by active wallets we simply never recorded because they trade other assets?**

- If **dormant**: nothing rescues coverage. §3 closes the only path to them, and the forced-flow
  archive is permanently a partial one.
- If **active elsewhere**: enumeration and all-asset recording both help, and coverage could rise
  a long way.

**The test:** take the 399 addresses already discovered from block sampling, drop those already in
the 5,395 universe, and run `clearinghouseState` on the remainder. Measure what fraction hold BTC
positions and how much notional they add relative to their count.

Roughly 400 requests, about 10 minutes, and it settles a question that otherwise costs days of
engineering to answer wrong. **Not run yet — the fills harvest is currently using the same token
bucket, and contending with it would corrupt both.**

## 8. Recommendation

1. **Do not attempt full-history enumeration.** 210 years.
2. **Run the §7 test** once the harvest finishes tonight. It is the gate for everything else.
3. **Make the all-asset recording change** regardless — near-zero cost, compounding benefit to the
   archive, and it is the only item here that is unambiguously worth doing.
4. **Do not build any product** on this until the §7 test says coverage has a path above 25%.

And the standing condition: **LIQ-2's secondary stays dead.** If better coverage ever makes the
directional question worth asking again, it is asked in a new contract, declared before the data
is looked at.
