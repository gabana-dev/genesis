# Binance futures streams: what is actually served to this location

**Date:** 2026-08-18
**Status: CLOSED.** A factual measurement of data availability, not a direction decision.
**Classification: BUILD — engineering. Not research. No novelty claimed.**

Found while implementing T0.1 (record the liquidation stream). **T0.1 cannot be done from this
location.** The finding is recorded rather than worked around, because the failure mode is
silent: a recording would simply contain no liquidations, and that is indistinguishable from a
week in which none occurred.

---

## 1. What was tested

Direct websocket probes to `wss://fstream.binance.com/ws/<stream>`, from Nairobi, 2026-08-18,
each held open for the stated duration with no subscription message — the stream is named in
the connection path, which is the venue's documented single-stream form.

| Stream | Held | Received |
|---|---|---|
| `btcusdt@depth` | 12 s | **49 depthUpdate** |
| `btcusdt@trade` | 12 s | **19 trade** |
| `btcusdt@aggTrade` | 15 s | **silent** |
| `btcusdt@markPrice` | 30 s | **silent** |
| `btcusdt@kline_1m` | 12 s | **silent** |
| `btcusdt@forceOrder` | 15 s | **silent** |
| `!forceOrder@arr` | 60 s | **silent** |

## 2. Why "silent" is a finding rather than an absence of events

Two of those streams fire on a schedule, so silence cannot be explained by a quiet market.

**`btcusdt@markPrice` publishes every 3 seconds by design.** Thirty seconds of silence is ten
missed publications of a heartbeat.

**`!forceOrder@arr` carries every liquidation on the entire venue**, across all symbols, not
just BTCUSDT. Sixty seconds without a single liquidation anywhere on Binance USD-M futures is
not a plausible market state.

Meanwhile `@depth` and `@trade` delivered normally on the same host, in the same window, over
the same connection pattern. **This is a partition of the stream catalogue, not an outage of
the venue and not a network problem.**

## 3. Alternative hosts

| Host | `!forceOrder@arr` |
|---|---|
| `fstream.binance.com` | silent |
| `fstream-mm.binance.com` | connection rejected (`InvalidStatus`) |
| `fstream.binancefuture.com` | silent |

Subscription over an open connection was also tried, in both the documented forms — `SUBSCRIBE`
on a bare `/ws` endpoint, and the combined `/stream?streams=…` URL. **Both acknowledged the
subscription with `{"result": null}` — the venue's success response — and then delivered
nothing.** An acknowledged subscription that yields no data is the worst version of this: it
looks like it worked.

## 4. What this rules out, and what it does not

**Ruled out from this location, for now:** liquidations (`forceOrder`), aggregate trades
(`aggTrade`), mark price, and klines over websocket.

**Not established:** *why*. Candidates include a regional restriction on part of the futures
catalogue, an edge-node configuration serving Nairobi, or a persistent partial outage. Nothing
here distinguishes them, and the venue publishes no statement that was found. **This should be
re-tested rather than assumed permanent** — a single day from a single location is thin
evidence about a policy.

**Not affected:** the futures REST depth snapshot works (`fapi.binance.com`), and spot
websocket streams are unaffected — the spot recording running since 2026-08-18 carries both
depth and aggTrade normally.

## 5. Consequence for the plan

**T0.1 — record forced flow — is blocked, not deferred.** The liquidation stream was to be
*supervised ground truth* for separating forced from informed flow. It is unavailable, so that
distinction must either be inferred from the trade stream (a liquidation cascade has a
signature: rapid one-sided trades of accelerating size) or left unmade. Inference was
explicitly what the liquidation stream was meant to avoid, so this is a real loss of rigour and
is recorded as one.

**T0.2 — perp book and trades — proceeds, and is better than specified.** `@trade` delivers
*individual* trades where `@aggTrade` would have delivered merged ones. Aggregation combines
same-price fills from a single taker order, which is exactly the granularity flow attribution
needs to keep. The unavailable stream was the inferior record.

Verified over 60 seconds: **224 depth updates and 1,020 individual trades, zero sequence gaps
on either channel** — confirming both continuity rules, `pu == previous u` for depth and
`t == previous t + 1` for trades.

## 6. A note on how this was found

The implementation was written first and smoke-tested against the live venue before anything
was committed or recorded for real. The smoke test showed depth arriving and trades absent,
which prompted the probe.

Had the futures recorder been started for a multi-day run on the strength of a passing unit
test, it would have produced a log with no liquidations in it, and the natural reading of that
log would have been *"forced flow is rarer than expected."* That conclusion would have been
about Binance's edge configuration rather than about markets.
