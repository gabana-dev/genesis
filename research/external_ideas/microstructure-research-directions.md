# Microstructure research directions (LLM-suggested)

**Source:** ChatGPT and Claude, in separate conversations with the researcher, 2026-08-13.
Both were asked what research directions Genesis could pursue given the EXEC-1 recording.
**Status:** unadopted

---

## The ideas

Both models proposed reframing Genesis from "can we predict price?" to **studying markets as
information-processing systems** — how information enters, propagates through participants,
alters liquidity, and eventually appears in price. Neither claimed novelty; both correctly
identified their suggestions as imports from established market microstructure.

**Proposed directions, condensed:**

| # | Direction | Cited prior art |
|---|---|---|
| 1 | Order-flow / queue imbalance → short-horizon price change | Cont, Kukanov & Stoikov (2014); Gould & Bonart |
| 2 | Liquidity resilience — how fast depth rebuilds after displacement | Bouchaud, Farmer & Lillo (2009) |
| 3 | Market state persistence — autocorrelation decay of book state ("market memory") | — |
| 4 | Information content — mutual information `I(X_t; Y_t+h)`, "information half-life" | — |
| 5 | Self-excitation of order flow | Hawkes processes; Bacry, Mastromatteo & Muzy |
| 6 | Price discovery across venues — where information appears first | Hasbrouck (1995) information share |
| 7 | Market state → future **volatility** rather than direction | Corsi (2009) HAR-RV, and HAR-RV-X for exogenous regressors |
| 8 | Panel / pooled testing across correlated assets to escape the single-series power limit | Driscoll-Kraay or clustered standard errors |
| 9 | Conditional / event-based tests instead of unconditional ones | event-study methodology |
| 10 | "Liquidity stress index", "fidelity index" — composite state variables | — |
| 11 | Flow independence / crowding — are many participants acting independently or as one? | — |
| 12 | News → market state → price, with an LLM as a *semantic sensor* producing structured event features, never a trading signal | — |
| 13 | Theoretical grounding for what EXEC-1 measures empirically | Glosten & Milgrom (1985); Kyle (1985); Easley & O'Hara PIN |
| 14 | Publish the Binance kline archive defects as a standalone finding | — |

Both explicitly warned against searching many conditions until something works, and both said
finish EXEC-1 first.

## Feasibility against Genesis's actual data — checked 2026-08-13

The recording is `btcusdt@depth` from `stream.binance.com`: **Binance spot, 1-second diff
updates reporting NET change per price level.** Individual events are not observable — if 40
orders were added and 35 cancelled within a second, the record shows +5.

**Not answerable with this recording, for reasons of data rather than difficulty:**

- **(5) Hawkes / self-excitation** — requires event-level arrivals with precise timestamps.
  One-second netting destroys the event structure the model is about.
- **Cancellation rate vs replenishment rate as separate quantities** (a component of 1, 2 and
  10) — netted before observation. Only the difference survives.
- **(11) Flow independence / crowding** — not merely hard: unidentifiable. Counting independent
  participants from netted book changes cannot be done, and no venue publishes account-level
  flow.
- **(6) Cross-venue price discovery** — one venue was recorded. Needs new simultaneous
  recordings, which is a project rather than an analysis.
- **(12) News** — no external data is collected, and none is planned at this phase.

**Answerable with this recording:** (2) liquidity resilience, (3) state persistence,
(4) information content, and (1) order-book imbalance — all at 1-second resolution.

## Why it might matter to Genesis — and where it does not

**The recurring omission in both proposals is horizon.** Order-flow imbalance, resilience,
information decay and self-excitation all live at seconds to minutes. MEASURE-1 established
that affordability begins at **4 hours**. So most of the list measures a region Genesis's own
evidence has already excluded from action. They remain interesting as science; they are not
routes to an edge, and neither model connected them back to the affordability floor.

**Two exceptions survive that test:**

- **(7) Volatility forecasting.** Volatility has far more effective observations than
  direction, the research journal already named it as the lever, and HAR-RV is an established
  baseline that reuses the verified kline pipeline. It respects the affordability floor.
  Open question neither model addressed: **what instrument expresses a volatility view** at
  accessible cost? Without one, a good forecast is a risk input, not revenue.
- **(8) Cross-sectional / panel testing.** Measured on 2026-08-13 — see
  [`../crypto-cross-section-breadth-study.md`](../crypto-cross-section-breadth-study.md).
  33 perps carry ~2 independent bets directionally, ~24 once the market factor is removed. The
  route has room in it, in relative-value shape only.

**Held against, specifically:**

- **(10) Composite indices** — `Fidelity = f(depth, spread, resilience, volatility, flow, ...)`
  with unspecified `f`, or a stress index with four free weights, is a parameter farm. It is
  unfalsifiable until specified, and specifying it is the searching the trial ledger exists to
  count. ChatGPT names this danger and then proposes it anyway.
- Framing markets as collective mind is motivation, not measurement. Every testable version
  reduces to something microstructure already names. Useful as a reason to look; not evidence,
  and not a basis for choosing direction.
- The final priority table rates five of eight areas "High", which is not a prioritisation, and
  omits cost and feasibility — where multi-venue, news and sentiment die.

**(14) is underrated by both.** The three defects MEASURE-1 found in Binance's public kline
archives — halt-truncated bars, unreliable `close_time`, the ms→µs unit switch — sit in data
many people use and likely get wrong. It is a short, verifiable artifact from work already
done, and unlike everything else here it costs days rather than months.

## Status

Nothing here is adopted. No experiment follows from this file. Recorded so the ideas exist in
one place with their feasibility already checked, and so that a later decision to pursue one is
made deliberately rather than by remembering a conversation.
