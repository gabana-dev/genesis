# GEN-1 result: six cells clear their bar and none of it means anything

**Date:** 2026-08-19
**Contract:** [`../market/CONTRACT-generalisation.md`](../market/CONTRACT-generalisation.md),
frozen at `ee3f7e08535c02eb…` before any non-BTC metrics file was read.
**Report:** [`../market/evidence/gen1-report.json`](../market/evidence/gen1-report.json)
**Data:** 1,721 daily metrics files per asset, ~495,000 rows each, 2020-08 → 2026-08. 99 s.

---

## 1. The result

| cell | n | accuracy | own bar | clears | 95% CI | long | K4 |
|---|---|---|---|---|---|---|---|
| **ETHUSDT 1d** | 2,695 | **0.5210** | 0.5018 | yes | [0.4983, 0.5440] | 0.604 | Y |
| SOLUSDT 1d | 2,694 | 0.5122 | 0.5012 | yes | [0.4896, 0.5360] | 0.729 | Y |
| BNBUSDT 1d | 2,697 | 0.5091 | 0.5022 | yes | [0.4854, 0.5313] | 0.732 | Y |
| BNBUSDT 3d | 2,697 | 0.5076 | 0.5012 | yes | [0.4720, 0.5432] | 0.755 | Y |
| SOLUSDT 3d | 2,694 | 0.5067 | 0.5007 | yes | [0.4722, 0.5453] | 0.850 | Y |
| ETHUSDT 3d | 2,695 | 0.4998 | 0.5010 | no | [0.4638, 0.5343] | 0.645 | Y |
| XRPUSDT 1d | 2,697 | 0.4943 | 0.5018 | no | [0.4716, 0.5161] | 0.632 | Y |
| DOGEUSDT 1d | 2,697 | 0.4943 | 0.5015 | no | [0.4727, 0.5165] | 0.648 | Y |
| DOGEUSDT 3d | 2,697 | 0.4920 | 0.5009 | no | [0.4568, 0.5254] | 0.685 | Y |
| XRPUSDT 3d | 2,697 | 0.4894 | 0.5010 | no | [0.4553, 0.5202] | 0.654 | Y |

**Five of ten clear their own bar on the point estimate. Not one of them means anything.**

- **Every single 95% interval contains 0.50.** Not one excludes a coin flip, let alone a bar.
- **K3 fires.** The best cell, ETH at 1 day, scores **0.5210** against a zero-skill best-of-10
  distribution with **mean 0.5148 and p95 0.5247.** It is inside the noise.
- **K4 fires in all ten cells.** Per-window standard deviation exceeds the distance from 0.50
  everywhere.

**GEN-1 returns negative. The DIR-2 specification does not generalise.**

## 2. The thing this result actually taught me

**Once netting drops the cost to 0.348 bps, the bar stops being the test.**

The bars here run **0.5007 to 0.5022** — between seven and twenty-two hundredths of a point
above a coin flip. A specification can clear a bar that low by accident, and five of them did.

Every earlier experiment was framed as *"can accuracy beat the break-even hit rate?"* — a
sensible question when the bar was 0.5281. At 0.5010 the question is empty. **The binding
constraint has silently changed from economic to statistical**: what matters is no longer
whether the signal clears costs, but whether there is a signal at all.

Nothing in any frozen contract noticed that transition. It is worth more than the result.

## 3. Predictions, scored — four of five

- **H1 — CONFIRMED.** No asset clears its own bar with an interval excluding it. Five clear on
  the point estimate; none survives its confidence interval.
- **H2 — MIXED.** Three assets land above 0.50 (ETH, SOL, BNB) and two below (XRP, DOGE). BTC
  was 0.5242. That is not the coherent cross-asset signal H2 described, nor is it clean
  independence. It is what ten weak draws look like.
- **H3 — CONFIRMED, emphatically.** Long fraction exceeds 0.60 in **all ten cells**, ranging to
  **0.850** on SOL at 3 days. The features are positioning measures on assets that all rose
  over the sample, and the specification is structurally long everywhere.
- **H4 — WRONG.** I predicted SOL and DOGE would come closest to their bars because their bars
  are lowest. SOL clears both of its cells; **DOGE fails both and is among the two worst
  assets.** The lowest bar did not help the asset that had it.
- **H5 — CONFIRMED.** XRP and DOGE both land below 0.50, on both horizons. Five assets and a
  weak signal produced assets pointing the wrong way, exactly as a null would.

## 4. What it means for ECON-1

GEN-1 was run because the asymmetry pays: failure everywhere would make ECON-1's November read
close to decided in advance.

**It did not fail everywhere. It failed inconclusively**, which is the least useful of the three
possible outcomes.

Three assets weakly positive, two weakly negative, nothing significant, the best inside the
null. That is **consistent with there being no signal anywhere**, and equally consistent with a
signal too small for 2,700 observations to resolve. It lowers confidence in ECON-1 modestly and
settles nothing.

The honest summary: **BTC's 0.5242 does not look special against its peers, and it does not look
replicated either.**

## 5. What is NOT concluded

**Not that alt-coins are worse instruments.** The bar comparison in the contract stands: SOL's
break-even is half BTC's distance above a coin flip. GEN-1 says the *specification* does not
travel, not that the *market* is worse. A different signal might do better on SOL precisely
because its bar is lower.

**Not that the assets are independent.** Five points cannot establish a correlation structure.

**Not a licence to refit.** K2 is explicit: no per-asset tuning, no added features, no extended
asset list without a new declaration.

## 6. A defect, and it was the one named that morning

The 2026-08-19 assessment flagged as a latent trap that `dir2` represents metrics timestamps in
**seconds** while `econ1` uses **milliseconds**, with nothing marking the seam.

The first GEN-1 run crashed on it within the hour — `load_metrics` returned seconds and handed
them to a millisecond consumer. The seam is now marked in the docstring where the conversion
happens, rather than in a document nobody reads at the point of use.
