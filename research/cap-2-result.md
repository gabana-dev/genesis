# CAP-2 result: capacity degrades gently, and I predicted it badly

**Date:** 2026-08-19
**Contract:** [`../market/CONTRACT-capacity-2.md`](../market/CONTRACT-capacity-2.md), frozen at
`9b06777e0071e750…` before the instrument touched real data.
**Report:** [`../market/evidence/cap2-report.json`](../market/evidence/cap2-report.json)
**Data:** q3, 241,920 orders, 231 s.

**This run is the SECOND.** The first passed both kill conditions and was wrong — see
[`cap-2-units-defect.md`](cap-2-units-defect.md). Its output is discarded.

---

## 1. The instrument is validated

**K2 — the anchor — passes almost exactly.** Observed reach 0.65286 against EXEC-1's published
0.65290. The new replay loop agrees with the old one where the two should agree, to four
decimal places.

**K3 — size-blindness — clears by two orders of magnitude.** Spread across sizes is **0.115**
against a 0.001 threshold. The instrument now sees size. On the discarded run this spread was
0.005, and that was floating-point noise.

## 2. The result

Fill rate (upper bound, base units), pooled across offsets:

| size | fill rate | vs \$1,000 |
|---|---|---|
| \$1,000 | **0.7893** | — |
| \$10,000 | 0.7554 | −3.4 pts |
| \$100,000 | 0.7173 | −7.2 pts |
| \$1,000,000 | **0.6743** | **−11.5 pts** |

**A thousand-fold increase in size costs about eleven and a half points of fill rate.** That is
a real constraint and a gentle one.

At the touch specifically (offset 0), the decline is steeper: 0.8674 → 0.7159.

## 3. Predictions, scored — two of five

- **G1 — CONFIRMED.** Fill rate falls monotonically with size, across all four sizes.
- **G2 — WRONG, and malformed.** I predicted the \$1,000 *upper* bound would land within 5
  points of EXEC-1's 65.27%. It is 78.93%. But EXEC-1's 65.27% is a **certain-fill** rate — a
  *lower* bound — so I compared two different quantities. The comparable figure, our lower
  bound at \$1,000, is **0.6556**, which matches EXEC-1 to within 0.3 points. The prediction was
  badly written; the instrument agrees.
- **G3 — WRONG, badly.** I predicted the \$1,000,000 upper bound would fall **below 20%**. It is
  **67.4%**. I was wrong by a factor of three and in the direction of pessimism.
- **G4 — WRONG.** I predicted absolute ambiguity would rise with size. It **falls**: the gap
  between bounds is 13.7 points at \$1,000 and 2.2 points at \$1,000,000. A larger order is
  *less* likely to complete an optimistic fill, so the two bounds converge rather than diverge.
  CAP-1's C5 said the same thing and was also wrong.
- **G5 — CONFIRMED.** At \$1,000,000 the median depth ratio exceeds 1.0 and the size classifies
  as `dominant` in the majority of cells (0.96, 0.96, 0.34 across the three offsets).

## 4. An unplanned observation: the book is a spike, not a slope

The depth ratios are the most surprising numbers in the run:

| cell | median depth ratio | dominant |
|---|---|---|
| \$1,000 at the touch | 0.004 | 2% |
| **\$1,000 one tick behind** | **14.78** | **77%** |
| \$1,000 five ticks behind | 1.49 | 20% |

**A \$1,000 order is fifteen times the displayed depth one tick behind the touch.** The level
holds about \$67.

BTCUSDT's book is not a gentle slope away from the touch — it is a **spike at the touch with
near-empty ticks immediately behind it**, and depth partially returns further out (five ticks
behind holds more than one tick behind). Genesis has never measured this and it was not what
CAP-2 set out to look at.

It also explains the offset-0 versus offset-1 gap in fill rate, and it matters for any future
quoting work: **posting one tick behind the touch is not a small concession, it is a move into
a near-empty part of the book.**

## 5. A declared metric that turned out uninformative

`median_ambiguity_fraction` reads **0.0000 in every cell**. That does not mean there is no
ambiguity — the aggregate bounds differ by up to 13.7 points.

The distribution is heavily zero-inflated: most orders either trade through the level
(ambiguity exactly 0) or never fill at all (also 0). Only a minority sit in the partial-fill
region where the bracket is open. **The median is the wrong summary for that shape**, and it
was declared in the contract before anyone knew the shape.

Reported as declared and flagged as uninformative. A future contract should use the mean or the
fraction of orders in the ambiguous region.

## 6. What this does and does not establish

**Establishes:** with this instrument, on this recording, fill rate declines smoothly and
modestly with size, and the decline is real rather than an artefact — K2 anchors it and K3
clears by 115×.

**Does not establish anything about profitability.** CAP-2 is descriptive by declaration (§6 of
the contract), which is the only reason it was permitted to read q3 a third time. **The moment
any of these numbers is used to justify a trade size, it inherits the full data-reuse problem
and must be re-established on unseen data.**

**The ceiling binds hardest exactly where the question matters.** Market impact is unmodelled.
At \$1,000,000 the order is 4.2× displayed depth at the touch and `dominant` in 96% of cases —
so the true fill quality there is worse than 67.4% by an amount this recording cannot measure.
**Read 67.4% as an upper bound that is probably generous.**

**Not Hyperliquid.** q3 is Binance. Hyperliquid's depth feed runs at 0.2 updates/second and its
fast feed carries no depth, so capacity is not measurable there with what Genesis can observe.

## 7. The honest summary

Three of five predictions wrong, one of them by a factor of three, and the one I got most wrong
was in the pessimistic direction — I expected size to bite far harder than it does.

The finding is mildly good news for a strategy that does not yet exist: **capacity is not the
binding constraint at any size Genesis would plausibly trade.** Fees are, at 96.6% of the cost
stack, and netting is the lever against them.
