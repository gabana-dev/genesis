# DEFECT: the LIQ-2 universe was frozen on FOUR HOURS of recording, not 21 days

**Date:** 2026-08-19
**Severity: high.** It invalidates the central interpretation of two committed documents and one
result. Found by Gabana asking "why 21 days?" — a question I could not answer without checking,
and the check showed the premise was mine and it was wrong.

---

## 1. The error

Across [`liq-2-k2-fired-coverage-20pct.md`](liq-2-k2-fired-coverage-20pct.md),
[`on-chain-enumeration-scope.md`](on-chain-enumeration-scope.md) and
[`coverage-test-result-dormant.md`](coverage-test-result-dormant.md) I wrote repeatedly that the
missing open interest belongs to *"wallets that never traded during the 21-day recording."*

**There was no 21-day recording.**

| | actual |
|---|---|
| `hl1` recording started | **2026-08-19 08:31Z** |
| universe frozen | **2026-08-19 12:44Z** |
| **recording length at freeze** | **≈ 4 hours 13 minutes** |

**Where "21 days" came from.** `hl_harvest` pages each wallet's fill history **backwards 20 days**
through `userFillsByTime`. That is 20 days of *history fetched per wallet*, not 20 days of
*recording*. I conflated the two and then reasoned from the wrong one for a full day.

## 2. Why this matters enormously

Wallet discovery in `hl1`, measured directly:

| elapsed | distinct wallets |
|---|---|
| 0.25 h | 940 |
| 1.25 h | 2,260 |
| **4.25 h (universe frozen here)** | **5,551** |
| 6.75 h | 17,264 |
| 9.75 h | **27,276** |

**The same recording, left running to this evening, already knows 27,276 wallets — five times the
universe LIQ-2 was built on — and the curve is still climbing steeply, nowhere near saturation.**

A wallet absent from a **four-hour** window is not remotely dormant. Most ordinary traders do not
trade every four hours.

## 3. What is overturned

**"The universe is exhausted."** No. It was a four-hour sample presented as a three-week one.

**The concentration argument was over-extended.** "Top 300 of 5,395 hold 97.8%" is concentration
*within* our universe. I used it to argue that wallets *outside* the universe hold nothing. It
cannot support that: it says nothing about a wallet the recording never saw.

**"DORMANT" answered a question I had mis-specified.** The coverage test compared our universe
against *all-asset block actors* and correctly found they rarely hold BTC (3.2%). But there is a
third category I never tested, and it is the likeliest one:

> **BTC traders who simply did not trade during our four-hour window.** They hold BTC at our
> universe's rate — 43.4%, not 3.2% — because they are the same kind of wallet.

**"All-asset recording is refuted for coverage."** Only the *all-asset* lever was tested. The
**longer BTC recording** lever is entirely untested and is the obvious one.

## 4. What still stands

- **LIQ-2's K2 fired at 20.24% coverage.** A measured fact about the instrument as built.
- **Deep-history L1 enumeration is ~210 years.** Throughput, unaffected by this defect.
- **Block actors hold BTC at 3.2%.** A valid measurement; only its interpretation was wrong.
- **The commercial conclusion**, for now: a one-fifth map is not a product. If coverage rises
  materially that would need revisiting, and it has not risen yet.

## 5. How the error survived a day

It was stated confidently in a commit message, then inherited by the next document, then by the
next, and each restatement made it look better established. **No measurement was ever run against
it** — the recording's actual start time was one `head -1` away the entire time.

The specific trap: `days_back=20` sat in the harvest code and read like a recording length. The
project's own rule — *a surprising number is a suspected bug until checked* — was applied to
`withdrawable` being zero and to the 500 KB row parse, but never to a number that was not
surprising at all.

**A plausible premise gets less scrutiny than an implausible result.** That is the lesson worth
keeping.

## 6. The decision this forces, which is not mine to make

The obvious repair is to re-freeze the universe on a much longer recording and re-measure
coverage. Before that happens, the tension has to be named:

**LIQ-1 closed at 5.8%. LIQ-2 fired K2 at 20.24%. A LIQ-3 would be the third contract on the same
idea.** Three attempts at one hypothesis, each after the previous failed, is the shape of moving
your own goalposts — regardless of how good each individual reason sounds.

**The argument that it is legitimate:** LIQ-1 closed on a design error found before analysis.
LIQ-2's universe rests on a defect in how the instrument was *built and described* — four hours
presented as twenty-one days — and repairing a mis-built instrument is not the same as retrying
until the number is agreeable.

**The argument that it is not:** K2 fired on a measured result. Every closed contract can be
reopened if you are willing to find something wrong with the instrument, and the person deciding
whether the reason is good enough is the person who wants the answer.

**Recorded here undecided, for Gabana.** What is *not* in question: LIQ-2's verdict stands as
issued, its secondary is never computed, and nothing collected under it may be read as a result.
