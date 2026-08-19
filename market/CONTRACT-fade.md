# FADE-1 — does taking the other side of persistently unprofitable wallets pay?

**Status: FROZEN 2026-08-19, before any wallet has been scored.** No score, window, threshold,
benchmark, prediction or kill condition below may be changed after this point. If a defect is
found it is reported and recorded, not silently repaired.

**Classification: IMPORT + BUILD. No novelty claimed.** The behavioural premise is Barber &
Odean's, decades old. What is new here is only that realised profit is *directly observable*
on an on-chain order book, so the cohort can be identified from ground truth rather than proxied.

> ## AMENDMENT 2 — 2026-08-19, before any wallet has been scored
>
> **Split into a refutation channel and a confirmation channel.** Both changes tighten; nothing
> is loosened.
>
> **The defect this repairs.** K1 required 60 days of harvest before any read. That threshold was
> set by counting *decision points* when it should have counted *independent* ones. At a one-day
> horizon, N days of evaluation give **N independent observations** however finely they are
> sampled — 60 days is 30, which was never going to establish anything. The number was wrong in
> a way that would have produced a long wait for an underpowered answer.
>
> **And more history makes the central bias worse, not better.** Wallets come from Genesis's own
> live recording, so they are wallets active *today*. Scoring them over a longer past conditions
> harder on survival: every trader who blew up and stopped is invisible. Extending the harvest
> buys observations at the cost of the very bias §4 already declares.
>
> ### The two channels
>
> **REFUTATION — historical, available now, and it can only kill.** Cohort membership persistence
> (F4 / G4) is testable on the 22 days already harvested: two 10-day windows, which is Zhai's own
> design. If membership does not persist, **K4 fires and both contracts close**, in hours rather
> than months.
>
> **This channel may NOT report B1–B4 as evidence.** It may refute the premise; it may not
> support it. A positive economic figure computed here is survivorship-contaminated by
> construction and is reported, if at all, as a pilot that confirms nothing.
>
> **CONFIRMATION — forward, and the only channel that can support a result.** Evaluation runs on
> decision points at or after **2026-08-21**, using the `hl1` recording, which is unbiased: it
> sees every wallet that trades, not only the ones the harvest reached. Cohort selection still
> uses harvested history — survivorship affects *who is picked*, which is acceptable because the
> cohort being traded against is by definition currently active.
>
> **K1 is replaced:** no *confirmatory* read before **270 forward decision points**, matching
> ECON-1. The 60-day harvest requirement is withdrawn as the wrong instrument for the question.
>
> **A fast no, a slow yes.** That is the correct shape for a hypothesis with these odds, and it
> was not the shape originally declared.


---

## 1. The change of question

Every previous Genesis experiment asked **"can we predict the price?"** — the hardest question
in finance, contested by the best-resourced participants alive. Five contracts and the answer
has been consistently *"not by enough to matter."*

FADE-1 asks a different question:

> **Can we identify wallets that persistently lose money, and does taking the other side of
> their aggregate positioning pay?**

This is identification rather than prediction. It does not require beating anyone. It requires
recognising a stable pattern of behaviour, which is a much weaker claim.

## 2. Why fade the losers rather than follow the winners

FOLLOW-1 ([`CONTRACT-follow.md`](CONTRACT-follow.md)) tests the mirror. Both are declared
because both are plausible. But three things favour this side:

**Losers are more persistent than winners.** Skill is hard to separate from luck; bad
behaviour — buying tops, selling bottoms, over-leveraging, holding losers and cutting winners —
is stable and identifiable. This is the oldest finding in the retail-trading literature.

**There are far more of them**, so the cohort is larger and its aggregate is less noisy.

**Their anti-edge is behavioural, and behaviour does not get faster.** A profitable wallet's
edge may be latency Genesis can never match; that objection does not apply to a losing one.

## 3. What this is NOT

**Not copy trading.** Copying replicates a trade and arrives late by construction — 291 ms of
latency plus decision time means a systematically worse entry than the wallet being copied.
FADE-1 reads a **state**, not a fill: the cohort's aggregate net position at a decision
boundary. Nothing is raced.

**Not a claim that these wallets are stupid.** A wallet with negative realised P&L may be
hedging a position invisible to this data, or market-making unsuccessfully, or trading for
reasons that are not directional. The contract claims only that the aggregate is *informative*,
never that it is *irrational*.

## 4. Data — and a shortfall declared in advance

**Source:** `~/genesis-evidence/hl-fills/fills.jsonl`, harvested from Hyperliquid's public
`userFillsByTime`. Each fill carries `closedPnl`, `startPosition`, `sz`, `px`, `side`,
`crossed`, `dir`, `fee`, `coin`, `time`.

**Prices:** Hyperliquid BTC, from the `hl1` recording and 1-hour klines.

> ### ~~The harvest as it stands is INSUFFICIENT~~ — SUPERSEDED BY AMENDMENT 2
>
> *Retained because a frozen contract is not edited. The 60-day threshold below counted
> decision points rather than independent observations and is withdrawn; see Amendment 2.*
>
> ### The harvest as it stands is INSUFFICIENT, and this is stated before any result
>
> The current harvest reaches 22 days back. FADE-1 requires a **30-day scoring window (W1)**
> and a **30-day evaluation window (W2)**, so **60 days of history.**
>
> At 22 days there are roughly 30 eight-hourly decision points in a test window. **Thirty
> observations cannot establish anything**, and running on them would produce a number whose
> only honest description is noise.
>
> **K1 forbids reading FADE-1 until the harvest reaches 60 days.** Extending it is the same
> method with a wider `days_back` — no new technique, only more requests. Declaring the
> requirement now means the extension is a data decision rather than a rescue after a
> disappointing result.

**Sampling bias, restated per K6.** Wallets come from Genesis's own live recording, so only
wallets active in that window are visible. **Every figure describes currently-active wallets,
not the population.**

## 5. The score

Per wallet, over a window, using **BTC fills only** (the only coin with a price series):

```
skill_w  =  sum(closedPnl_e)  /  sum(|notional_e|)
```

Realised profit per unit traded. Normalising by notional is not cosmetic: without it the
cohort would be selected on **size** rather than on **skill**, and the largest traders would
define both tails.

**Minimum 200 BTC fills in W1** for a wallet to be scored. Below it the wallet is counted and
excluded, never scored on thin evidence.

**The loser cohort is the bottom decile of `skill_w` in W1.** The ranking is formed on W1 alone
and **never re-formed**. That separation is the whole defence against survivorship.

## 6. The signal

At each decision boundary in W2, from `startPosition` and each fill's direction, reconstruct
every cohort wallet's BTC position, then:

```
cohort_position(t)  =  sum over cohort of position_w(t),  z-scored on a trailing 30 days
```

**The FADE position is the opposite sign.** When the losing cohort is unusually long, FADE-1 is
short.

**Decision frequency: hourly. Horizon: 1 day.** Hourly because positioning changes continuously
and 8-hourly would waste most of the sample; 1 day because that is Genesis's measured reachable
region. Overlap is handled by a moving-block bootstrap with block = 24, never by discarding
observations.

## 7. Endpoint and benchmarks

**Primary: mean net return per decision, in bps**, after the full cost stack — **not accuracy.**

GEN-1 established why: once netting drops cost to 0.348 bps the break-even bar falls to ~0.5024,
and a specification can clear a bar that low by accident. **The binding constraint is now
statistical, not economic.** Accuracy is no longer the right object anywhere in this project.

Cost stack: Hyperliquid tier 0 netted, 0.348 bps per decision, per
[`feemap.py`](feemap.py) and the adverse-selection horizon study.

**Four benchmarks, all must clear:**

- **B1** — mean net return per decision > 0.
- **B2** — beats buy-and-hold over the same decisions under the same cost stack.
- **B3** — beats the **95th percentile** of 10,000 sign-permuted nulls. Permutation preserves
  the long/short counts and destroys only the timing.
- **B4 — beats a constant position at FADE-1's own realised net exposure.** This is the
  primary passive benchmark and §8 explains why it is the one that will probably kill this.

## 8. The objection that will most likely sink it, stated first

**Retail is structurally long.** If the losing cohort is persistently long — which is the
default expectation — then fading them is persistently **short**, and a persistent short in a
rising market loses money without containing any information at all.

That is the mirror of the defect found in DIR-2, where a 71% long signal earned drift rather
than skill. **B4 exists precisely to catch it**, and F3 predicts it will fire.

If FADE-1 clears B1 but fails B4, the honest reading is **"we found a way to be short in a bull
market"**, and K3 says so.

## 9. Predictions

- **F1.** The loser cohort's aggregate position is **persistently long** — mean net exposure
  above +0.5 z across W2.
- **F2.** B1 clears: fading produces a positive mean net return per decision.
- **F3. B4 FAILS.** The return is exposure, not timing. *This is my expectation and the one I
  most want to be wrong about.*
- **F4.** Cohort membership is persistent: at least 40% of the W1 bottom decile remains in the
  bottom quintile when W2 is scored independently. Below that, "persistently unprofitable" is
  not a stable attribute and the premise is wrong.
- **F5.** FADE-1 outperforms FOLLOW-1 on the primary endpoint — losers are the more stable
  cohort.
- **F6.** The cohort's fills are predominantly **taker** (`crossed == true`). If they are mostly
  makers, they are failing market makers rather than bad directional traders, and the
  behavioural premise does not apply.

## 10. Kill conditions

- **K1.** **No read until the harvest covers 60 days.** Not a soft target: a result computed on
  22 days is void, whatever it says.
- **K2.** Fewer than 50 wallets in the cohort, or fewer than 500 decision points in W2:
  reported **unevaluable**, not computed.
- **K3.** If B1 clears but **B4** fails, the result is reported as **exposure, not information**,
  and FADE-1 closes. A cheaper way to be short is not a finding.
- **K4.** If F4 fails — cohort membership does not persist — **the premise is refuted** and B1–B4
  are not computed. There is no point testing a signal built on an unstable cohort.
- **K5.** If F6 fails — the cohort is predominantly maker — FADE-1 reports that it has
  identified **unsuccessful market makers rather than bad directional traders**, and the
  behavioural premise is withdrawn.
- **K6.** The §4 sampling bias is restated on every reported figure.
- **K7.** Any change to the score, the cohort definition, the windows or the cost stack voids
  the run.

## 11. Known limitations

**One venue, one asset, one cohort definition.** Hyperliquid BTC.

**Position reconstruction depends on `startPosition` being complete.** Gaps in a wallet's fill
history produce a position series with unknown offsets; wallets with detectable gaps are
excluded and counted.

**No hedges are visible.** A wallet losing on Hyperliquid may be profitable overall across
venues. This measures Hyperliquid P&L, not trader P&L, and the distinction is stated on every
figure.

**Latency is not simulated.** FADE-1 asks whether the state is informative at a daily horizon,
not whether it could be acted on inside a specific execution path.

## 12. Out of scope

No sizing, no leverage, no live order, no per-wallet trading, no agent.
