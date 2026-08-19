# FADE-1 refutation channel: K2 fires. Unevaluable, and F4 was not computed.

**Date:** 2026-08-19
**Contract:** [`../market/CONTRACT-fade.md`](../market/CONTRACT-fade.md), Amendment 2 —
the refutation channel, which tests cohort persistence (F4 / G4) on two 10-day windows and
**can only kill**.
**Result: K2 fires. Reported unevaluable, not computed.**

---

## 1. The measurement

K2: *"Fewer than 50 wallets in the cohort, or fewer than 500 decision points in W2: reported
**unevaluable**, not computed."*

§5 requires **200 BTC fills in W1** for a wallet to be scored — *in W1*, not across the harvest.

| window anchoring | W1-eligible wallets | bottom decile | K2 floor |
|---|---|---|---|
| W1 starting at the earliest fill | 255 | **25** | 50 |
| W1 ending 10 days before the last fill | 270 | **27** | 50 |

**Both fail, by roughly half.** The anchoring choice does not rescue it, which is worth knowing:
had one cleared and the other not, picking between them after the fact would have been a forking
path.

## 2. What went wrong in my earlier count

Last night I reported the cohort at 61 wallets and said K2 cleared with margin. **That count was
over the whole 22-day harvest.** The contract requires 200 fills **within W1**, a 10-day window,
and roughly a third as many wallets clear that bar.

The extension from 729 to 911 wallets was still worth doing — it moved a genuinely marginal
number — but it was measured against the wrong requirement, and the gap is much larger than I
said.

## 3. What was NOT done, stated so it can be checked

**F4 was never computed.** No `skill_w` score, no cohort ranking, no persistence figure exists
for this data. Only wallet **counts** were measured — the feasibility inputs K2 gates on.

This matters for what happens next. Extending the harvest to satisfy a **feasibility** gate,
*before* any score is computed, is not goalpost-moving. Extending after seeing a disappointing
F4 would be. The sequence is the whole difference, and it is recorded here so the claim is
falsifiable rather than merely asserted.

## 4. What it would take

| | |
|---|---|
| harvested wallets now | 911 |
| W1-eligible rate | ~28% of harvested |
| needed for a 50-wallet decile | ~500 W1-eligible → **~1,800 harvested** |
| additional wallets | **~900** |
| time | ~3.5–4 hours at the measured ~4 wallets/min |
| disk | **~+2 GB** to `fills.jsonl` |

**The disk cost is not free, and it lands on another experiment.** q5 grows 6.1 GB/day against
28.9 GB free, so 2 GB spent on the harvest is roughly **8 hours less q5 recording** — and q5 is
already short of its declared seven days. This is a direct trade between COND-1's recording
length and FADE-1's ability to run at all.

## 5. Disposition

**FADE-1 and FOLLOW-1 remain declared, frozen and unread.** K2 firing is not a result about the
hypothesis; it is a statement that the instrument cannot see. Nothing about the premise is
established either way.

The confirmatory channel is unaffected and still gated on forward decision points from
2026-08-21 (Amendment 2), which no amount of harvesting accelerates.

**The third harvest extension is a decision for Gabana**, precisely because it costs another
experiment rather than only time.
