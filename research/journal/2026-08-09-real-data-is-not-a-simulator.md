# 2026-08-09 — A simulator was rejected. Real market data was never tested.

> Drafted by Claude from the researcher's ruling of 2026-08-09, pending his review.
> Content of the ruling is his; the data facts in §2 are computed from the RDB-1
> snapshot; the open items in §4 are handed to
> [`../decisions/0002-close-the-genesis-research-program.md`](../decisions/0002-close-the-genesis-research-program.md),
> not resolved here.

## 1. The distinction

The environment-first gate, drafted in DR0002 and applied to Genesis's own market goal,
returned **no justified environment**. The stated reason was specific:

> "Reflexivity needs unreachable scale; a hand-built market simulator would rediscover the
> price-impact function that was typed into it."

Both halves of that objection are about an environment Genesis would have **authored**. A
simulator's price dynamics are a thing someone types in, so recovering them demonstrates
nothing — this is the same manufactured-necessity failure mode DR0001 and DR0002 each caught,
one level further out.

**That objection does not transfer to real market data.** A recorded market price was not
authored by Genesis, cannot be tuned by Genesis, and does not become easier if Genesis wants it
to. It supplies the one thing M2 identified as missing — a cost the experimenter did not write
— without supplying the thing that made a simulator worthless.

The gate rejected *simulators*. It never ruled on *real data*. That was an unexamined gap, not
a decision.

**Ruling (researcher, 2026-08-09): RRP is the real environment.**

## 2. The environment is already in the repository

No acquisition step is required. `RRP` — the NSW1 half-hourly regional reference price — sits
in the same 96 AEMO CSVs already downloaded for RDB-1, on the same timestamps, under the same
licence, covered by the same sha256 manifest. The harness was built target-agnostic; the README
records that pointing it at RRP "requires changing a column name, not the harness."

It is a materially harder series than demand. Computed from the last 24 development months
(n = 144,720 native intervals):

| | `TOTALDEMAND` | `RRP` |
|---|---|---|
| coefficient of variation | 0.169 | **1.884** |
| excess kurtosis | — | **1599** |
| skew | — | 34.4 |
| observed range | — | −$1,000 → $15,500 |
| intervals with negative price | — | 3.12% |
| intervals above $1,000 | — | 0.231% |

Demand is smooth and doubly seasonal, which is why the imported linear-Gaussian machinery suits
it — RDB-1 is a fair *validation* of that machinery and a weak *test* of it. Price is spiky,
fat-tailed, regime-switching and admits negative values. A Gaussian predictive distribution is
expected to be poorly calibrated on it.

**That expected failure is the point.** The harness already instruments `cov50/80/95` and CRPS,
so a calibration failure would be measured precisely rather than inferred. Under the standing
criteria — more capable, more adaptive, more measurable, more grounded — a well-measured
negative result on RRP is worth more than a further MAE improvement on demand.

## 3. What this does not earn

Recorded now so it cannot be quietly assumed later:

- **Forecasting a price is not trading it.** No fills, no position, no market impact, no
  reflexivity. Nothing here bears on execution or on performative prediction (opportunity map
  **D**), and no claim in that direction is licensed by it.
- **Electricity price forecasting is an established field** with its own review literature. Any
  work on RRP is classified **import + engineering validation**. No novelty is claimed, and the
  prior-art gate applies before any laboratory is proposed.
- **The cost is available, not yet installed.** M2's finding was that usefulness requires a cost.
  A real price makes a real cost *possible*; it does not by itself put one in the loop. Nothing
  consumes the forecast yet.

## 4. Left open, deliberately

- Whether the simulator/real-data distinction amends DR0002 — which currently selects Option D
  (completed learning vehicle) and withdraws Option A — or leaves it standing. Reviewed as a
  scheduled step **after** the RDB-1 evidence is frozen, not before.
- Whether the next step is a **target change** (RRP through the existing protocol) or a
  **consumer change** (a decision layer over the demand forecasts that already exist). One step,
  chosen from evidence. Not both, and not a sequence.

## Source

[`../decisions/0002-close-the-genesis-research-program.md`](../decisions/0002-close-the-genesis-research-program.md)
(the environment-first gate, preserved there and deliberately not canon);
[`../prior-art-and-opportunity-map.md`](../prior-art-and-opportunity-map.md);
[`../experiments/0005-sparse-observation-decision-relevance.md`](../experiments/0005-sparse-observation-decision-relevance.md)
§E (costless waiting); `rdb/README.md` (frozen RDB-1 contract and licence).
