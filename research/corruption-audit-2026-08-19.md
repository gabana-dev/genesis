# Did the bugs corrupt anything already concluded?

**Date:** 2026-08-19. Asked by the researcher, and the right question to ask.

Eight defects were found in eight days. Each is traced to every conclusion that could depend
on it.

---

## The one that mattered most, and it is clean

**Could the size-blind fill simulator have inflated EXEC-1's 1.83 bps?**

That number is load-bearing — the cost model, every directional bar, ECON-1 and NET-1 all
descend from it. If it were inflated, most of the project would be wrong.

`fills.py` has two fill branches:

```python
if here == 0.0 and traded_through:          # CERTAIN
    _fill(o, t, mid, "certain")
...
if o.consumed >= o.queue_ahead > 0:         # OPTIMISTIC -- the size-blind one
    _fill(o, t, mid, "optimistic_only")
```

The **certain** branch fires when the level went to zero *and* the book moved past it. Every
order resting there filled, whatever its size. **Size cannot enter that condition.** Only the
optimistic branch is size-blind.

EXEC-1's outcome mix at the touch: **13,217 certain, 1 optimistic-only.**

**99.99% of EXEC-1's fills came from the branch where size is irrelevant, and its headline was
computed on the certain pool alone. The 1.83 bps is not corrupted.**

## The rest, traced

| defect | what it touched | conclusion affected? |
|---|---|---|
| **D-4** one Ingestor per connection | multi-connection recordings | **No.** q3 was single-connection; q5 was recorded after the fix. |
| **D-5** blocking urllib in the event loop | multi-connection recordings | **No.** Same reason. It did corrupt my *attribution* of q5's timestamp anomalies, which was corrected in the record. |
| **Adverse selection extrapolated** (1.19 assumed at 1d, 0.13 measured) | the cost stack | **No, and worth checking.** Market making is a short-horizon activity, so 1.19 at 60 s is the right figure there — and at either value the round trip is −5.19 or −4.13 bps against a 0.00154 bps spread. Catastrophically negative either way. The closure stands. |
| **CAP-1 size-blindness** | CAP-1 itself | **No.** CAP-1 was never run to completion; it was blocked before producing a number. |
| **D-CAP2-1** units | CAP-2's first run | **No.** Run discarded before it was read as a result. |
| **D-6** book.stream instrument | reconstructions from multi-instrument logs | **No.** Only q5 is multi-instrument and nothing has been published from it. |
| **DIR-1 K3** (mean vs p95 of the null) | DIR-1's best-cell verdict | **Partially, and it did not change the answer.** DIR-1 reported its best cell as exceeding the zero-skill expectation; under the corrected test it would not. But K2 and K4 fired independently and DIR-1's verdict was negative regardless. Recorded as D-D1. |
| **GEN-1 unit boundary** | nothing | Crashed before producing output. |

## Why so many were harmless

Not luck. Three habits did it:

**Kill conditions fired before results were read.** CAP-1 and CAP-2's first run both died on
their own checks or on a smoke test, before a number reached a document.

**Anchors.** CAP-2's K2 required reproducing EXEC-1's reach rate and hit 0.65286 against
0.65290. That single check validated an entirely new instrument against an old one.

**The certain/optimistic bracket.** EXEC-1 reported a *lower bound* that requires no queue
assumption at all. The ambiguity that made it look conservative is exactly what made it immune
to a defect discovered two weeks later.

## What is worth revisiting, and what is not

**Worth revisiting — one thing.** DIR-1 and DIR-2 were judged against bars of 0.5281 and
0.5218. Netting later dropped the bar to **0.5024**. Neither contract was wrong at the cost it
declared, but both were answering *"does accuracy beat the break-even?"* at a time when that
was the binding question. At a 0.5024 bar it is not. **Their verdicts stand; their framing is
obsolete.** GEN-1 made this explicit and it is the most important methodological shift in the
project.

**Not worth revisiting.** EXEC-1, MEASURE-1, CARRY-1, the cost model and CAP-2 all rest on
quantities the defects could not reach.

## The honest residual

**These are the bugs that were found.** The base rate for a codebase of 18,500 lines written in
eight days is not zero, and the machinery that caught eight has no way to prove it caught the
last one. What can be said is narrower and true: **every number currently load-bearing has
either been anchored against an independent measurement, or is a bound that holds under any
assumption about the thing that might be wrong.**
