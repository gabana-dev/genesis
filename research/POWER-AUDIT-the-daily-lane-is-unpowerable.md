# Power audit: every daily-horizon test in this project is underpowered by one to two orders of magnitude

**Date:** 2026-08-20
**Cost:** one hour, zero new data, entirely from numbers already recorded.
**Prompted by** Gabana asking whether anything can be learned now rather than after more weeks of
waiting that produce nothing.

**Answer: yes, and this is it.** The tests we have been running could never have found the effects
we were looking for. That is checkable today, and it should have been checked before any of them
were frozen.

---

## 1. What a hit-rate test can actually see

For a directional test, the smallest true hit rate detectable at 80% power, α = 0.05 two-sided:

| independent observations | smallest detectable hit rate |
|---|---|
| 270 | **0.5852** |
| 900 | **0.5467** |
| 2,695 | 0.5270 |
| 5,000 | 0.5198 |
| 20,000 | 0.5099 |

And in the other direction — what a realistic edge costs to establish:

| true hit rate | independent obs needed | years at 1 per day |
|---|---|---|
| 0.510 | 19,600 | **53.7** |
| 0.520 | 4,900 | **13.4** |
| 0.530 | 2,178 | 6.0 |
| 0.550 | 784 | 2.1 |

## 2. GEN-1 could not have found what it was looking for

| | |
|---|---|
| rows per cell | 2,695 |
| **independent** observations (8-hourly decisions, 1-day horizon) | **~898 days** |
| smallest hit rate the test could resolve | **0.5467** |
| best cell measured | **0.5210** |

**The best result in the experiment sits below the threshold the experiment could detect.**

GEN-1 reported that five of ten cells cleared their economic bar, every confidence interval
contained 0.50, and the best cell sat inside the null. All true. But the conclusion drawn —
that nothing is there — was **not established by the test**. A true edge of 52% would have
produced exactly the data we saw, and the test would have missed it every time.

## 3. ECON-1 is already known to be uninformative, three months early

Its declared read is 270 completed 1-day trades at 3 decisions/day — **90 independent days.**

| | |
|---|---|
| smallest detectable hit rate at that n | **0.5852** |
| t-statistic if the in-sample Sharpe (0.070) is entirely real | **0.66** |
| t treating all 270 as independent (generous, wrong) | 1.15 |
| independent days needed at that effect size | **1,600 — 4.4 years** |
| at half the effect (in-sample inflates) | 6,400 — 17.5 years |

**ECON-1 returns a null in November whether or not the effect is real.**

And **K2 closes the directional programme on that null.** A test that cannot detect the effect
would be used to kill the question. That is the defect, and it is visible now, before any
observation exists — the strongest position from which to record it.

## 4. This is MEASURE-1's 68-year wall, generalised

MEASURE-1 found that establishing linear structure at ≥4 h needs **68 years** of a seven-year-old
instrument, and called it a hard boundary of the same kind as the latency floor.

That was read as a fact about variance ratios. **It is a fact about the daily lane itself.** Any
statistic, at a 1-day horizon, on one instrument, needs decades — because one instrument produces
one independent observation per day, and small effects need thousands.

**The 291 ms latency floor closes the fast lane. The independent-observation rate closes the slow
lane.** Genesis has been working in the only region where neither constraint had been computed.

## 5. What our "no" answers actually established

This is the honest restatement, and it is weaker than what was reported:

> **We established that no LARGE directional edge exists — nothing above roughly 54–55%. We never
> had the power to say anything about the 51–53% region, which is where every realistic edge in
> this literature lives.**

Reported as "no edge." Truthfully: "no edge bigger than five percentage points."

**Not every conclusion is affected.** Those resting on measured magnitudes rather than
significance stand unchanged — market making died because the spread is 0.00154 bps against
5.19 bps of cost, which is a ratio, not a p-value. Carry returned 2.6–4.3% against a 4–5% T-bill,
also a magnitude. **The economic closures survive. The statistical ones do not.**

## 6. The two escapes, and they are already named in canon

MEASURE-1 §8 lists the only ways out: **conditional, cross-sectional, or event-based.** The power
arithmetic says why each works.

**Cross-sectional multiplies the observation rate.** N instruments give N independent observations
per day instead of one. At 20 assets, detecting a 52% edge falls from 13.4 years to about
**8 months** — and further with more assets. This is the single largest available change to the
project's information rate, and Genesis has the multi-asset metrics archive already on disk.

*GEN-1 does not contradict this.* GEN-1 asked whether the same time-series signal **replicates**
on each asset separately — five separate underpowered tests. A cross-sectional design ranks
assets against each other at each date and is a different estimator with different statistics.

**Event-based trades frequency for effect size.** Liquidations, funding resets, listings: rarer,
but the per-event effect is large, and n needed falls as the square of effect size. A 50 bps event
effect needs a hundredth of the observations of a 5 bps one.

## 7. Standing practice, adopted now

**No contract may be frozen without a power section stating: the effect size it is designed to
detect, the number of INDEPENDENT observations that requires, and the time to collect them.**

If that time exceeds the project's horizon, the contract is not declared. This is arithmetic. It
takes minutes. It would have prevented DIR-1, DIR-2, GEN-1 and ECON-1 from being run in their
current form.

**The independence count is the part that gets missed.** ECON-1 looks like 270 observations and is
90; GEN-1 looks like 2,695 and is 898. Overlapping windows inflate the apparent sample threefold
and the apparent t-statistic by √3.

## 8. What this does not excuse

The tests were not wasted — they rule out large effects, and the measurement machinery they built
is sound. But **the project has been answering "is there an effect?" with instruments that could
only answer "is there a huge effect?"**, and reporting the first.

That is a more serious methodological failure than any of the individual defects found this week,
and unlike those, it was computable before a single observation was collected.
