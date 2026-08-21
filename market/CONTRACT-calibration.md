# CAL-1 — does the vulnerability we publish anticipate what happens to a cluster?

**Status: DRAFT, awaiting declaration by Gabana. K1 has already fired for the primary
predictor — see §3.** Nothing below may be changed once frozen. It
is written now, deliberately, while the record holds 522 calls and no outcome has been examined —
because a contract written after the data looks suggestive is not a contract, it is a
rationalisation.

**Classification: MEASUREMENT.** No novelty is claimed for the idea of checking whether a
published figure predicts anything. What is unusual is only that nobody in this market does it.

---

## 1. Why this contract exists

Everything Isobath ships can be copied in a fortnight — the map, the wallet check, the copy, the
design. **The one thing that cannot be copied is a public record of our own calls against what
subsequently happened**, because it accrues only with time.

`product/calibration.py` has been recording since 2026-08-21: every cluster published, and what
the same price bucket looked like 6, 24 and 72 hours later. It records and deliberately concludes
nothing. This contract is what turns that record into a finding, or kills the attempt.

## 2. The question

> **Among clusters we publish, does a higher `cannot_defend_pct` at time T predict a larger
> reduction in that cluster's notional by T+H, conditional on price having reached it?**

If yes, "vulnerable" means something predictive and the product's central claim is earned.

If no, the product still stands — it describes *current* defensibility, which is observed and
true regardless — but we will have measured that it says nothing about what happens next, and
that must be published as prominently as any positive result.

## 3. THE PROBLEM THAT MAY KILL THIS BEFORE IT RUNS

**`cannot_defend_pct` has almost no variance.** Measured on day one of recording, across 433
calls: **71% of clusters sit at exactly 100%**, median 100.0, only 56 of 433 below 90%.

A predictor with no spread cannot discriminate. If nearly every cluster is 100%, saying so
separates nothing, and the question above is unanswerable **not because the effect is absent but
because there is no contrast to measure it against.**

This is the exact shape of the failure that killed GEN-1 — a test that could resolve nothing
below 54.67% and measured 52.10%. It is recorded here, before running, so that it cannot later be
discovered mid-analysis and worked around.

**Therefore §4 requires a contrast check that runs FIRST and can stop the experiment.**

### P1 was run before this contract was frozen. Both vulnerability measures FAIL it.

Against the 433 calls held on 2026-08-21, splitting at the median:

| candidate predictor | median | p10–p90 | below / above median | P1 |
|---|---|---|---|---|
| `cannot_defend_pct` | 100.0 | 76.0 – 100.0 | 29% / **0%** | **fail** |
| `thinly_defended_pct` | 100.0 | 87.7 – 100.0 | 27% / **0%** | **fail** |
| `notional_usd` | 1,001,183 | 328,395 – 11,397,295 | — | pass |
| `wallets` | 3.0 | 1.0 – 14.0 | — | pass |
| `distance_pct` | 5.0 | 1.0 – 8.5 | — | pass |

Zero percent of clusters sit *above* the median vulnerability, because the median **is** the
ceiling. There is no high-vulnerability group to compare against a low-vulnerability one.

**This is the finding, and it is larger than the one CAL-1 set out to make.** The product's
central published figure cannot be calibrated as framed — not because we lack data, but because
the quantity does not vary. If 96% cannot-defend is what BTC looks like on an ordinary Thursday,
that number describes **leverage in general, not today**, and the product should say so rather
than presenting it as a reading that changes.

**Substituting a predictor does not rescue the original question.** `notional_usd`, `wallets` and
`distance_pct` all pass P1, but "does cluster size predict reduction" is a different question
from "does vulnerability predict reduction", and only the second is what Isobath sells. Any
substituted run is therefore **secondary and must be labelled as answering a different question**,
never reported as though the primary question had been answered.

## 4. Pre-conditions — checked before any outcome is computed

**P1 — CONTRAST.** The predictor must have usable spread. Split calls at the median; both halves
must contain at least 30% of calls. **Already run — see §3. Both vulnerability measures fail, so
K1 has fired for the primary question.** CAL-1 therefore proceeds only as a secondary experiment
on a predictor that passes, explicitly labelled as a different question, or waits for a market
condition in which vulnerability actually varies.

**P2 — POWER.** State, before running, the smallest difference in reduction ratio the sample can
detect at 80% power, and the independent observations that requires. Clusters from consecutive
hourly snapshots are **not independent** — the same wallets persist across scans — so the unit of
observation is a *cluster episode*: one price bucket, one contiguous run of snapshots. If the
episode count cannot detect a difference worth acting on, the experiment waits rather than runs.

**P3 — CONFOUND SEPARATION.** Every outcome must be conditioned on the four confounds already
recorded (`product/calibration.py`): scan tier, coverage at both ends, and whether the match was
found at all. A notional reduction that coincides with a tier change is uninformative and is
excluded, not adjusted.

## 5. The measurement

For each cluster episode with a resolvable outcome at horizon H ∈ {6, 24, 72} hours:

- **predictor**: the published vulnerability figure at T
- **outcome**: `notional_after / notional_before` for the same *price* bucket, matched within half
  a bucket width
- **condition**: whether the hourly spot series reached the cluster price between T and T+H — a
  **lower bound**, since hourly sampling cannot see an intra-hour touch

**Primary comparison**: mean reduction ratio for high-vulnerability episodes against
low-vulnerability episodes, split at the median, restricted to episodes where price reached the
cluster.

**Benchmark**: a matched control drawn from the same asset and the same hour, exactly as
CASCADE-1 required. A result that beats a permutation null but loses to a matched control is a
failure — that is precisely how CASCADE-1 died, and this contract inherits the rule.

## 6. Kill conditions

Any one of these ends CAL-1 and is published as a refutation.

| | |
|---|---|
| **K1** | P1 fails for every candidate predictor — no contrast exists to measure |
| **K2** | P2 shows the detectable difference is larger than any difference worth acting on |
| **K3** | The high- and low-vulnerability groups differ by less than the matched control's spread |
| **K4** | Fewer than half of episodes resolve, making the surviving sample a survivorship artefact |
| **K5** | The result reverses when conditioned on scan tier — meaning it measured our sampling, not the market |

## 7. What may be published either way

**Permitted:** the measured relationship, its confidence interval, its sample, its confounds, and
the statement that vulnerability does or does not anticipate cluster reduction.

**Forbidden regardless of outcome:** any per-cluster probability, any forecast of price, and any
suggestion that a high-vulnerability cluster will be reached. CASCADE-1 (F-0010) already found
that reaching a cluster does not move price more than a volatility-matched minute. CAL-1 asks a
different question — whether the cluster itself dissolves — and a positive result must not be
allowed to leak back into the price claim we already refuted.

## 8. First read

Not before **2026-11-01**, or when P2's episode count is met, whichever is later. The record is
three days old. Any reading before then is noise, and the temptation to take one early is the
reason this section exists.
