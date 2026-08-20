# Real coverage is 53.3%, not 20.24%. The tail was not empty.

**Date:** 2026-08-20
**Purpose:** business sizing — is an archive of Hyperliquid position data worth building?
**Method:** stratified estimate, seed 20260820, `market/coverage_now.py`.

**LIQ-2 remains dead.** K2 fired on the instrument as built, its verdict stands, its secondary
is never computed. This measures a *different* instrument.

---

## 1. The number

| | |
|---|---|
| universe when LIQ-2 froze it (4 h of recording) | 5,395 |
| universe now (~19 h of recording) | **31,349** |
| exchange BTC open interest | $2,396,600,220 |
| estimated visible | **$1,276,200,032** |
| **coverage** | **53.3%** — 95% CI **[40.9%, 70.8%]** |
| LIQ-2 reported | 20.24% |

The interval is wide because position notional is heavily skewed, and the bootstrap says so
rather than hiding it behind a normal approximation. **Even the lower bound, 40.9%, is double
what LIQ-2 measured and well clear of K2's 25% floor.**

## 2. The claim this destroys

LIQ-2's closure argued the universe was **exhausted**: the top 300 of 5,395 wallets held 97.8%
of scan-set notional, so more wallets of the same kind would add nothing.

The stratified sample says otherwise, decisively:

| | wallets | holding BTC | notional |
|---|---|---|---|
| original universe (stratum A) | 5,395 | 1,690 (31%) | **$596M** |
| discovered since (stratum B, sampled) | 25,954 | **35.6%** of sample | **$681M est.** |

**The wallets discovered after the freeze hold MORE than the entire original universe.** The new
wallets also hold BTC at a *higher* rate — 35.6% against 31%.

The concentration statistic was true and I over-extended it. It measured concentration *within*
a four-hour activity sample, and I used it to claim something about wallets that sample never
saw. It could never support that.

## 3. Why the old number was so wrong

Not one error but two, compounding:

1. **The universe was four hours old**, not the 21 days I recorded across three documents.
2. **Activity ranking is anti-correlated with position size** — the wallets appearing most in a
   trade feed are market makers with flat books. A short window selects hardest for exactly the
   wallets that hold least.

A four-hour activity sample is close to the worst possible instrument for measuring who holds
open interest, and it produced 20.24%. Nineteen hours produces 53.3%.

## 4. This is still a lower bound

The universe remains **activity-derived**: a wallet that has not traded during hl1's ~19 hours
is still invisible, however large its position. hl1 is still recording and still discovering
wallets, so **coverage should keep rising** without any further work.

What the earlier "DORMANT" verdict established survives and is now correctly scoped: wallets
active in *other assets* rarely hold BTC (3.2%). That was never the binding question. The
binding question was wallets that trade BTC *less often than our window was long*, and this
measurement answers it — there are a great many, and they hold most of the money.

## 5. What it means commercially

A 20% map is not a product. **A 53% map, still climbing, is a different object.**

It does not settle whether anyone will pay. It settles the one input the whole question rested
on, which was ours to control and which I had wrong by a factor of 2.6.

## 6. Caveats, stated

- **Time mismatch.** Stratum A's notional is from the 18:03Z deep scan; open interest is current.
  Price moved from ~66,000 to ~69,000 between them, so both sides shifted.
- **Wide interval.** [40.9%, 70.8%] is honest, not precise. Narrowing it needs a larger sample or
  a full scan (13.8 hours).
- **One asset, one venue, one moment.**

## 7. What this does and does not license

**Does not:** revive LIQ-2, or read anything collected under it as a result.

**Does:** establish that a forced-flow map built on a properly-aged universe would cover roughly
half the exchange rather than a fifth — and that the instrument's failure was never the idea, it
was a four-hour recording mistaken for a three-week one.

**Whether that becomes a LIQ-3 remains undecided and is Gabana's call.** The tension recorded in
[`DEFECT-universe-was-four-hours-not-21-days.md`](DEFECT-universe-was-four-hours-not-21-days.md)
§6 stands: three contracts on one idea has a shape worth being suspicious of, however good each
individual reason sounds.
