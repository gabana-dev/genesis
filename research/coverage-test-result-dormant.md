# Coverage test: DORMANT. The forced-flow map is permanently stuck near 20%.

**Date:** 2026-08-19
**Declared:** [`on-chain-enumeration-scope.md`](on-chain-enumeration-scope.md) §7, with thresholds
fixed in `market/coverage_test.py` and committed **before** the run.
**Verdict: DORMANT.** The wallets LIQ-2 cannot see are not trading assets we failed to record.
They are not trading.

---

## 1. The result

| | baseline (LIQ-2 deep) | novel wallets from L1 blocks |
|---|---|---|
| scanned | 5,395 | 400 |
| holding a BTC position | 2,342 (**43.4%**) | 13 (**3.2%**) |
| **rate vs baseline** | — | **0.07×** |
| mean notional per holder | $224,458 | $656,857 (**2.93×**) |
| total notional | ~$526M | **$8.54M** |

40 blocks sampled every 1,000 back from the tip yielded 438 distinct addresses, of which
**407 (93%) were absent from our 5,395-wallet universe.** The block population really is
different from ours. It simply does not hold BTC.

**The declared rule fires DORMANT** on the rate test: 0.07× is below the 0.25× floor.

## 2. The one result that cuts the other way, and why it does not rescue anything

Novel wallets that *do* hold BTC hold **2.93× more** than ours on average. That is a real finding
and it deserves stating rather than burying: the wallets outside our net are fewer but heavier.

It changes nothing, and the arithmetic is independent of the declared rule:

```
400 novel wallets            ->  $8.54M added
to move 20.24% -> 25% (K2)   ->  $124M needed
                             ->  ~5,800 additional wallets per snapshot
```

That would roughly double the deep-scan universe, push the scan from 2h22m to **~5 hours**, and
still only just reach the threshold. **The declared verdict and the practical arithmetic agree,
which is the outcome worth having when a single test decides a branch.**

## 3. What this closes

**The forced-flow map is permanently a ~20% map.** LIQ-2's K2 already fired; this establishes
that no reachable instrument fixes it:

- more wallets of the same kind — refuted by concentration (top 300 hold 97.8%)
- deep-history L1 enumeration — refuted by throughput (~210 years)
- all-asset recording — **refuted here**: the all-asset active population is 93% novel and only
  3.2% of it holds BTC

**Three independent paths, all closed.** The remaining open interest belongs to wallets that do
not transact on a timescale any sampling we can afford will see.

## 4. A recommendation of mine that this reverses

[`next-phase-review-2026-08-19.md`](next-phase-review-2026-08-19.md) §13 item 5 recommended the
all-asset recording change as *"near-zero cost, compounds."* **For coverage, that was wrong**, and
this test is the reason: widening the recording to every asset would add many wallets and almost
no BTC open interest.

The change may still be worth making for **other** purposes — FADE-1/FOLLOW-1 cohorts and TOX-1
are about wallet behaviour, not BTC position coverage — but it should no longer be justified by
coverage. Demoted from "do it regardless" to "only if a wallet-behaviour contract asks for it."

## 5. What this closes commercially

The "exact liquidation map as a data feed" idea rested on one claim: our map is exact where
commercial products estimate. **A map covering a fifth of the exchange is not a better map, it is
a partial one**, and the archive whose only moat was that it cannot be backfilled would be an
archive of a fifth of the phenomenon.

**That idea is closed on evidence, not on opinion.** It took one afternoon and about 400 requests
rather than a product build, which is the entire argument for testing the cheap decisive thing
first.

## 6. Limitation, stated plainly

The sample covers 40 blocks across ~40,000 — roughly **2.3 hours of chain time**. It therefore
speaks directly about *recently active* wallets and only by elimination about dormant ones.

That elimination is the intended inference and it is sound in one direction: if the all-asset
**active** population barely holds BTC, then the missing open interest sits with wallets that are
neither in our BTC universe nor recently active anywhere. Whether they are dormant, or merely
active more rarely than a 2.3-hour window can see, is not distinguished here — and does not
matter, because both are equally out of reach.

## 7. Disposition

- **LIQ-2 collection continues.** `clearinghouseState` has no history and an uncollected hour is
  lost permanently. It is not a wait for coverage to improve; coverage cannot improve.
- **No LIQ-3.** All three candidate instruments are now closed with measurement. Declaring another
  contract on this idea would be us moving our own goalposts.
- **No product.** §5.
