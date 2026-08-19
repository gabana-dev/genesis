# Salvage register — what survived each closure, and where it might apply

**Standing practice from 2026-08-19.** Genesis kills hypotheses by design, and a kill-heavy
method has a failure mode: it throws away the salvageable along with the refuted.

**The rule.** When a contract closes, separate:

- **the USE that failed** — closed, verdict stands, never reopened to chase a better number
- **the FINDING that survived** — a measurement, still true, possibly valuable elsewhere

**The distinction that keeps this honest.** Salvaging a finding for a *new question* is
legitimate. Re-running a *dead question* until it passes is goalpost-moving. If the salvage
would resurrect the original endpoint, it is not salvage.

**The asymmetry that makes most salvage possible.** A weak instrument usually fails a
**completeness** claim while remaining valid for a **presence** claim. It cannot say "there is
nothing here." It can still say "here is something," and be exactly right.

---

## LIQ-1 / LIQ-2 — the forced-flow map

**Failed use:** the map as a directional predictor, and as a commercial data feed. K2 fired at
20.24% coverage; a fifth of the exchange cannot support a completeness claim.

**Findings that survive, all still true:**

| finding | status |
|---|---|
| `liquidationPx` is public per wallet and exact | unaffected by coverage |
| The liquidation engine does not fire faster for a faster participant | the one place our 291 ms floor is irrelevant by construction |
| Half of wallets with an open position have **zero** free collateral; median of the rest is $14.81 | they cannot move their own liquidation price from inside the account |
| Our universe is **86% short** by notional, against an exchange that is exactly balanced | a hard measurement of our own sampling bias |

**Where they might apply — none of these need completeness:**

**1. Forced flow is UNINFORMED flow.** A trade executing at a known liquidation price is not
someone who knows something — it is a margin engine. Everything Genesis has measured about
adverse selection assumes the counterparty might be informed. **Being able to identify flow that
provably is not informed is the exact inverse of toxicity**, and it needs only presence, never
completeness. Every cluster the map shows is real; the ones it misses cost recall, not precision.

*Connects to:* TOX-1, which is declared and frozen. This cannot enter TOX-1 — but it is the
obvious question for a successor.

**2. A cost conditioner.** LIQ-1 §8 named this and it was never tested: *"quoting into a dense
cluster is a different proposition from quoting into an empty book, and Genesis has never been
able to tell the difference."* A presence claim again.

*Connects to:* the conditioner family. COND-1 is frozen at 29 cells and cannot take another.

**3. The 86%-short measurement characterises WHO activity-selection finds.** Systematic shorts on
a perp DEX are disproportionately market makers hedging and basis traders. That is a statement
about the population every wallet contract in this project samples from.

*Connects to:* FADE-1/FOLLOW-1's **G6** — *"more than half the top decile's fills are maker; they
are market makers."* **This must NOT be read as evidence for G6.** G6 is a frozen prediction and
importing an outside observation to support it before the run is contamination. It is recorded
here as a prior expectation, so that if G6 holds, nobody — including me — can present this as
independent confirmation.

---

## Market making (EXEC-1, NET-1, quoting policy)

**Failed use:** passive liquidity provision on BTCUSDT as a business. Spread 0.00154 bps against
5.19 bps of cost; a 0% maker fee does not rescue it.

**Findings that survive:**

- **1.83 bps maker advantage**, audit-clean, size-independent on the certain-fill branch
- **Adverse selection decays to 0.1301 bps at 1 day** — I had predicted ~1 bps and was wrong by 9×
- **Netting cuts cost 8.9×** (3.105 → 0.348 bps), dropping the 1-day break-even to ~0.5024

**Where they applied — this salvage already happened and is the proof the practice works.** The
adverse-selection decay is what made longer horizons economically survivable, and the netting
result is what made the directional break-even reachable at all. **Both came out of a business we
had just closed.** ECON-1 exists because of them.

---

## CARRY-1 — funding harvest

**Failed use:** funding as a standalone business. 2.6–4.3%/yr against a 4–5% T-bill.

**Finding that survives:** the funding series itself, measured, with its decay. A return that is
inadequate alone is not necessarily inadequate as a **component** — as a hedge leg, or as a
conditioning variable for when leverage is crowded.

**Not currently pursued**, and recorded rather than acted on.

---

## CAP-1 — the size-blind simulator

**Failed use:** capacity measurement with a size-blind instrument. Contract BLOCKED.

**Finding that survived:** *the instrument itself was the defect* — a 1,000× size range produced
identical fills. That produced `sized_fills.py`, which unblocked CAP-2.

**A closure that generated a tool.** The most common shape of useful salvage in this project.

---

## Discipline note

This register is **not** a list of things to go build. Most entries should stay unpursued.
Its job is to stop a closure from destroying a measurement, so that when evidence later names a
step, the material is still here rather than buried in a document titled "closed."
