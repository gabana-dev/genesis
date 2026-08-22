# The hypothesis queue

**Written 2026-08-22, after six eliminations.**

This file exists because of a specific risk. The current instruction is *collect, do not design* —
and "we are collecting data" is a comfortable way to avoid the hard question for a year. A queue
makes the avoidance visible: every row names what is being waited for and what will be run the
moment it arrives.

**Rules.**
1. A hypothesis enters this queue **before** anyone knows whether the data supports it.
2. No hypothesis is promoted to a product surface until it survives a **control**, in a frozen
   contract with kill conditions. Six have now failed at exactly that step.
3. A killed hypothesis is never deleted. It becomes an `F-` finding and stays.
4. Anything that can be tested today **is tested today**. Waiting is only legitimate when the
   blocker is real and named in the table.

---

## Killed — six, and each one is a finding

| # | hypothesis | how it died |
|---|---|---|
| F-0010 | reaching a liquidation cluster moves price | beat a permutation null, **lost to a volatility-matched control** (44.52 vs 40.07 bps) |
| F-0012 | defensibility ranks clusters | ~100% for 71% of clusters — **no contrast to measure** |
| F-0013 | survivors differ from casualties | "absent" conflates liquidation with voluntary exit — **unmeasurable in this archive** |
| F-0014 | clusters are big enough to matter | median cluster is **0.44% of the book** standing in front of it |
| F-0015 | margin response can be computed | formula reproduces the venue for 56.4%, internally inconsistent for 71.8% of accounts |
| F-0016 | public market state predicts conditions | nine variables, six years, **every lift within noise of 1.00**; long/short and funding reverse sign by year |

## Answered, not killed — a measurement that changed what we publish

| # | question | answer |
|---|---|---|
| F-0017 | what does an unbiased sample of this market look like | ten wallets hold **56.6%**; median position **$1,308** against a mean of $99,108 |
| F-0018 | how much does the hourly tier's selection bias the published map | coverage and dollar totals survive; **position counts do not** — 28% vs 47% within 10% of liquidation |
| F-0019 | does the impact relationship survive a thin book | **yes** — CONTRACT-impact K4 tested and not fired. The ratio does almost all the work; below 0.75× daily normal adds ~20% |

**The pattern, stated so it is not rediscovered a seventh time:** every one of these was either
volatility wearing a costume, a constant, or arithmetic that did not hold. Any new hypothesis must
say, before it runs, which of those three it could be — and how the test would tell.

---

## Queued

| # | hypothesis | data needed | blocked on | status |
|---|---|---|---|---|
| **Q1** | a dollar of margin moves a liquidation price by a measurable amount | deposits + hourly `liquidationPx` | **collecting now** — `market/deposits.py` records the fast set hourly; needs enough deposits landing between two scans | **waiting on time** |
| **Q2** | exposure concentration varies, and varies with something | wide-tier per-wallet state | **collecting now** — `market/wide.py`, 8,000 wallets, frozen sample | **waiting on time** |
| **Q3** | forced exposure as a share of the standing book is a market-level variable that varies | LIQ-2 + `standing_book()` | none — `market/bookwatch.py` archives it every 15 minutes since 2026-08-22 | **collecting; testable once the series is weeks long** |
| **Q4** | wallet cohorts behave differently before failure | longitudinal per-wallet state | wide tier plus months | **waiting on time** |
| **Q8** | the stress premium under F-0002's regime — depth after a large move over depth before it — rather than against a daily median | bookDepth + aggTrades | none | **runnable** |
| **Q5** | IMPACT-1 at burst level in a **thin** book (HL altcoins) | HL l2Book + trades for non-BTC | needs a thin-book recorder; BTC's book is $225M and the cost is ~1 bp (F-0014) | **buildable** |
| ~~Q6~~ | ~~IMPACT-1 under stressed depth~~ | | | **ANSWERED 2026-08-22 → F-0019.** K4 tested and did NOT fire. The ratio absorbs most of the regime; a book below 0.75× its daily normal adds ~20% |
| ~~Q7~~ | ~~does the fast tier bias the published map~~ | | | **ANSWERED 2026-08-22 → F-0018.** Coverage and dollar totals survive (within 1.6 points, within a tenth); position counts do not (28% vs 47% within 10% of liquidation) |

**Q6 and Q7 are answered; Q3 is collecting.** Nothing runnable is left unrun — every remaining
row is genuinely blocked on archive time, which is the only state in which "we are waiting for
data" is an honest thing to say.

**The next runnable question is a new one, and it comes from F-0019:** the stress premium was
measured against a *daily median*, which includes quiet overnight thinness. F-0002's stress —
depth after a large move divided by depth before it, 0.657 in the worst quarter — is sharper and
rarer, and this design cannot see it. Isolating that regime is **Q8**, and it needs no new data.

---

## Not queued, and why

| | |
|---|---|
| anything predicting **price direction** | F-0005: 4,900 independent observations, 13.4 years. Unpowered before it starts |
| a **risk score** or LOW/MODERATE/HIGH | a colour, not a finding. `product/IA.md §7` |
| an **accuracy percentage** | no forecasts are made, so there is nothing to score |
| a **dashboard of adjectives** | F-0016 measured that the percentiles behind them know nothing the tape did not |

---

## The honest prior

Six hypotheses have died and none has survived. The business plan has said since v1 that the most
probable outcome is *"machinery works, no edge found, value is in the observation infrastructure."*
Six eliminations later that sentence has more evidence behind it, not less.

That is not a reason to stop. It is a reason to keep the queue short, the tests cheap, and the
claims off the website until something survives a control.
