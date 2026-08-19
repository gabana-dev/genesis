# Outside assessment, 2026-08-19

Written as an audit rather than a report. Where it finds fault it names the file and the number.

---

## 1. Overclaims and inconsistencies found

**1.1 The COND-1 "runner" is not a runner.** I told the researcher the COND-1 runner was written
before q5 closes. `market/cond1.py` contains the declared grid, four conditioner primitives, the
kill conditions and a cell reporter — **and no end-to-end driver.** There is no function that
reads q5, reconstructs the two books, simulates fills, applies the conditioners and produces the
29 cells. q5 closes on 25 August. **This is the single largest outstanding gap and it was
misreported as complete.**

**1.2 Five declared cells have no implementation.** `cond1.cells()` enumerates `pooled_A`
through `pooled_D` plus `unconditioned` — the five reference cells the family count depends on —
but no pooling logic exists. The family arithmetic (29) is asserted by a test that counts
labels, not computations.

**1.3 The same quantity is represented in two units across modules.** `dir2.py` reads metrics
timestamps as **seconds** and multiplies by 1000; `econ1.py` builds them as **milliseconds** and
uses them directly. Both are internally correct. Neither can safely consume the other's data,
and nothing marks the boundary. A latent trap, not yet a bug.

**1.4 A declared metric is uninformative.** `median_ambiguity_fraction` reads 0.0000 in every
CAP-2 cell because the distribution is zero-inflated. Already recorded in the CAP-2 result; noted
here because it was declared in a frozen contract before its shape was known, and that pattern
will recur.

## 2. Dead weight

`lab/` (25 files) and `rdb/` (16 files) are **orphaned** — nothing outside them imports them.
`lab/README.md` states they are history kept runnable, which was a deliberate decision, so the
code stays. But **their test suites run on every commit**: `test_laboratory3.py` 4.96 s,
`test_sparse_loop.py` 5.03 s, `test_rdb_series.py` 2.71 s, plus three smaller — roughly **14
seconds of a 108-second suite spent testing retired subsystems.**

`holons/` is **not** dead and must not be removed: NET-1's A2 and A3 arms depend on it.

## 3. The rigidity, and it is one thing

**Every contract Genesis has ever frozen is BTCUSDT, and no contract has ever examined that
choice.**

MEASURE-1 selected BTC for data quality. Eleven contracts inherited it silently. That is the
textbook shape of an unexamined constraint: not defended, not revisited, simply carried.

Measured today, 1,000 daily bars per symbol, same cost stack:

| symbol | median 1d move | netted break-even | distance above a coin flip |
|---|---|---|---|
| **BTCUSDT** | 122.8 bps | 0.5028 | **0.283 pp** |
| BNBUSDT | 137.9 | 0.5025 | 0.252 pp |
| XRPUSDT | 167.6 | 0.5021 | 0.208 pp |
| ETHUSDT | 174.3 | 0.5020 | 0.200 pp |
| DOGEUSDT | 240.3 | 0.5014 | **0.145 pp** |
| SOLUSDT | 243.5 | 0.5014 | **0.143 pp** |

**The bar on SOL and DOGE is half the distance above a coin flip that BTC's is**, because the
cost is fixed per trade while the prize scales with the move.

Genesis optimised for the cleanest data and thereby selected the hardest market it could have
picked — the most watched, most arbitraged, tightest-spread instrument in crypto. The 0.00154 bps
spread was never a disappointment; it was the evidence.

## 4. The waits can be shortened, and one is already redundant

**4.1 ECON-1's 90 days can be sidestepped today.** Binance publishes the same futures metrics
archive for **ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT and DOGEUSDT** — all verified available, all
back to roughly 2020. The frozen DIR-2 specification can be run on five assets it has never
seen, immediately.

This is **not** the same hypothesis as ECON-1 and must not be reported as it. ECON-1 asks
whether the signal works forward on BTC. A multi-asset run asks whether the *method* generalises
at all. But it is free, immediate, and far more informative than it looks: if the spec fails on
all five, BTC's forward result is very likely noise. If it holds on three, that is stronger
evidence than a single asset can ever produce.

Pindza (2026) found no cross-asset *model* transfer, which is precisely why running the same
frozen spec across assets is a test rather than an assumption.

**4.2 The hl1 recording is now largely redundant.** It was started to accumulate two 10-day
windows by 9 September. The `userFillsByTime` harvest retrieves 22 days of the same history in
hours. hl1's remaining value is as an **unbiased** sample — it sees every wallet that trades,
where the harvest only sees wallets already active — so it should be kept and re-scoped, not
treated as the path to the answer.

**4.3 The test suite spends 14 of 108 seconds on retired subsystems.**

## 5. Where the unexploited ground actually is

The harvest returned richer fills than the method needed. Each carries `closedPnl`,
`startPosition`, `fee`, `oid` and `twapId` alongside `crossed`.

**5.1 Realised profit per wallet is directly observable.** Zhai's markout score is a *proxy* for
skill. Genesis has the thing itself. No centralised venue exposes it and the literature does not
use it, because it does not exist off-chain.

**5.2 That suggests a different mechanism entirely.** Every experiment so far has asked *"can we
predict the price?"* — the hardest question in the field, against the best-resourced competitors
alive. The data now in hand supports a different question:

> **Which wallets are persistently profitable, and can their behaviour be followed?**

This replaces prediction with identification. It does not require beating anyone; it requires
recognising skill and acting after it. The latency requirement collapses — a wallet holding for
hours does not care about 291 ms — and the bar stops being "52.8% directional accuracy" and
becomes "is the followed wallet's edge larger than twice our cost".

**The honest objections, before anyone gets excited.** Their edge may be latency-based and
therefore uncopyable. Many high-`closedPnl` wallets will be market makers, whose profit comes
from spread rather than direction and cannot be followed. Position sizes and entry reasons are
invisible. And selecting winners after the fact is survivorship unless the selection window and
the test window are strictly separated — which is exactly what TOX-1's W1/W2 split already does.

**It is testable with data already on disk, and it is the first idea in this project that does
not require out-predicting the market.**

**5.3 `twapId` labels announced institutional flow.** Barone & Lillo (2026) measured that trading
alongside a visible TWAP costs more. That is a cost-conditioning variable available for free, and
it needs no inference.

**5.4 The book-shape finding is unexploited.** CAP-2 incidentally measured that a \$1,000 order is
**14.8×** the displayed depth one tick behind the touch — that level holds about \$67. BTCUSDT's
book is a spike at the touch with near-empty ticks behind it. Nothing in Genesis uses this yet,
and it bears directly on any quoting decision.

## 6. What I would do, in order

1. **Write the COND-1 driver.** q5 closes in six days and the analysis does not exist.
2. **Run the frozen DIR-2 spec on five other assets.** Hours of work, collapses a 90-day
   information wait, and tests generalisation rather than assuming it.
3. **Declare a follow-the-profitable-wallet contract** once the harvest completes. It is the
   only line here that does not require beating the market at prediction.
4. **Re-scope hl1** as the unbiased control it now is.
5. **Drop the retired suites** from the default test run.

## 7. What I would not change

The contract discipline is the reason this assessment could be written at all. Six of my own
errors were caught this week by kill conditions, anchors and hand-computed tests — including a
units bug that would have justified million-dollar sizing on sixteen-dollar evidence. **That
machinery is the asset.** The rigidity is not in the method; it is in the single unexamined choice
of instrument.
