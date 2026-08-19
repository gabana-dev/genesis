# Selective prediction: the idea is sound, these two papers are a cautionary tale

**Date:** 2026-08-19
**Classification: IMPORT (the framing) + WARNING (the execution). Nothing adopted.**

Two papers, same lead author, two months apart, different journals:

- Kuznetsov, Prokopovych-Tkachenko, Bilan, Khruskov & Cherkaskyi (2025), *Algorithms* 18(12):758
- Kuznetsov, Kostenko, Klymenko, Hbur & Kovalskyi (2025), *Appl. Sci.* 15(20):11145

Both apply the same **confidence-threshold framework**: predict direction, then execute only
when model confidence exceeds a threshold. Headline: *"peak profits of 167.64 basis points per
trade with directional accuracies of 82–95% on executed trades."*

**Being one framework from one group, they are close to a single piece of evidence, not two.**

---

## 1. What is genuinely worth importing

**Selective classification is the formal name for "do nothing", and it has real foundations.**
The papers correctly cite Chow (1970), Herbei & Wegkamp (2006), Cortes, DeSalvo & Mohri (2016)
on abstention learning, and López de Prado (2018) on uncertainty-based sizing.

That matters to Genesis because **DIR-1 and DIR-2 both take a side at every decision point.**
They never abstain. FLAT is not in the action space, and the literature says it should be.

**The coverage–accuracy trade-off is the right object.** Accuracy on executed trades is
meaningless without the fraction executed. Any selective result Genesis ever produces must
report coverage in the same breath, and these papers do at least do that.

## 2. Why the numbers should not be believed

**A. The headline is the peak of a very large sweep.** 11 pairs × horizons from 10 to 600
minutes × 4 deadbands × 2 confidence levels × **46 threshold values** — thousands of
configurations — and the abstract reports the **peak**. No multiple-comparison correction
appears anywhere.

Genesis has measured what that does. Best-of-12 coin flips at n=5,940 averages **0.5106** and
reaches **0.5170** one time in twenty. Best-of-thousands, on the small samples that high
confidence produces, will manufacture spectacular numbers from noise. **This is exactly what
DIR-2's K3 exists to reject**, and it is why K3 was corrected from the mean to the p95.

**B. The profits are too large for the horizons, in a way that suggests magnitude selection.**
They report ~59–83 bps average profit per trade at horizons of minutes to hours. MEASURE-1
measured BTC's median absolute move as **12.5 bps at 15 minutes and 23.7 bps at one hour**.

Earning 82 bps per trade when the typical move is 25 bps is not possible from direction alone.
It requires the evaluated trades to be systematically the large-move ones — which is what a
**deadband** does if samples inside the band are dropped from evaluation rather than only from
labelling. Whether a move will exceed the deadband is **not knowable at decision time**.

The paper does not state clearly which it does. **On the evidence available the numbers are
consistent with conditioning on the realised move**, and that is the single most common fatal
flaw in this genre.

**C. Coverage collapses where the results are best.** Their own text: *"large regions of the
parameter space achieve essentially zero coverage"*, and *"<0.1% coverage for τ > 0.95"*. The
reported regimes run 7–12% coverage. On a 15% test split across 11 symbols, the best cells rest
on very few trades.

**D. Weekends were excluded from the main results**, with the paper acknowledging 12–18%
accuracy degradation there. A second selection, disclosed but not carried into the headline.

**E. Threshold selected by profit maximisation on validation.** Legitimate only if the reported
figure is from an untouched test set. The split is 70/15/15, but the abstract's "peak" language
does not make clear which set produced 167.64.

## 3. What a sound version would require — the specification Genesis would have to meet

Recorded now, before any selective experiment is declared, so it cannot be written to fit a
result:

1. **Never exclude a sample from evaluation based on its realised move.** The deadband may
   define the training label. It may not filter the test set.
2. **Report coverage with every accuracy figure**, and treat a cell below a declared minimum
   trade count as insufficient rather than impressive.
3. **Declare the confidence threshold in advance**, or select it on validation and report on a
   test set that selection never touched. Both, stated which.
4. **Correct for the sweep.** The null is best-of-N at the coverage-reduced sample size, and
   the comparison is the **p95** of that null, not its mean.
5. **Benchmark against the non-selective version of the same model.** If abstaining does not
   beat always-trading, the confidence score is decoration.
6. **Include costs at the actual fee tier**, and state the number.

## 4. What this changes for Genesis

**Nothing is adopted.** No feature, threshold, or method from these papers enters any contract.

**One thing is added to the map**: a selective variant of the DIR-2 specification — with FLAT
as a third action — is a legitimate future declaration with real literature behind it, and it
is the only structural idea from this reading worth pursuing. It must meet §3 in full.

It cannot enter ECON-1, which is frozen and forward-running with a two-sided specification.
It would be a separate contract, and it should not be written until ECON-1 reads, because
building a selective variant while the non-selective one is still unmeasured means never
learning which of the two did the work.
