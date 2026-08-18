# Binance futures streams: an endpoint migration, not a location restriction

**Date:** 2026-08-18
**Status: CLOSED — resolved, T0.1 unblocked (§8).** A factual measurement of data
availability, not a direction decision.
**Classification: BUILD — engineering. Not research. No novelty claimed.**

Found while implementing T0.1 (record the liquidation stream).

> ## CORRECTION, same day
>
> **The first version of this document concluded these streams were "not served to this
> location" and framed it as regional. That was wrong.** The same streams are silent from a
> Paris server on a different continent and a different network. It is not geographic, and a
> VPS or VPN does not fix it.
>
> The actual cause is a **venue endpoint migration**: Binance split the futures websocket into
> `/public` (high-frequency), `/market` (regular) and `/private` (user data), and
> **decommissioned the legacy URLs on 2026-04-23** — four months before this test. The
> announcement states that unmigrated connections "will ONLY be able to receive data from
> `/public`", and that channels under `/market` "will stop pushing data."
>
> **That is exactly the partition measured below.** `depth` and `trade` are high-frequency and
> still arrive on the legacy path; `aggTrade`, `markPrice`, `kline` and `forceOrder` are
> regular-market channels and are silent.
>
> **RESOLVED, same day — see §8.** The new form is `/<category>/ws/<stream>`. The earlier
> probes were missing the `/ws/` segment, which is why they returned `HTTP 404`. T0.1 is
> unblocked and `!forceOrder@arr` is recording.
>
> The original text is preserved below because the measurements in it are correct and only the
> conclusion drawn from them was not.

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

---

## 7. Latency, measured from both locations

Asked while diagnosing the above: **would a VPS help?** Two separate answers.

**For the missing streams: no.** They are silent from Paris too. Nothing about location fixes
an endpoint migration.

**For latency: it depends which path, and the answer is not uniform.** TCP round trip, 12
attempts each, 2026-08-18:

| Host | Nairobi (min / median / max) | Paris (min / median / max) |
|---|---|---|
| `api.binance.com` | 36.0 / 53.2 / 87.3 ms | **2.8 / 3.0 / 4.9 ms** |
| `fapi.binance.com` | 32.5 / 56.5 / **20,057** ms | **2.6 / 3.3 / 34.7 ms** |
| `stream.binance.com` | 33.8 / 61.4 / **30,051** ms | 226.0 / 234.7 / 238.8 ms |
| `fstream.binance.com` | 47.4 / 186.1 / **60,536** ms | 227.2 / 232.3 / 245.4 ms |

Two things stand out, and they point opposite ways.

**Nairobi is unstable, badly.** The medians are respectable; the maxima are 20, 30 and 60
seconds. Data-bearing REST calls took **30–90 seconds** during this session against Paris's
234–294 ms. That is a 100–300× difference and it is variance, not distance — the minima from
Nairobi are 32–47 ms.

**But Paris is *worse* on the stream hosts** — 232 ms median against Nairobi's 186 ms. The
REST/API hosts sit behind an edge that terminates near Paris (hence 3 ms); the stream hosts
resolve to an origin that is far from both. A move buys **stability**, not a lower floor.

**Consequence for the 291 ms floor.** Paris's data-bearing REST round trip of 234–294 ms sits
right on top of the measured floor. Relocating does not produce a step change in reachable
horizons and does not reopen anything the prior-art survey closed on latency grounds. What it
would buy is the elimination of 60-second stalls, which matter for *recording reliability*
rather than for *strategy*.

**Recorded as measurement, not as a recommendation.** Whether to move the recorder is an
operational decision, and no direction is selected. §9 sharpens what such a move would and
would not fix.

---

## 8. Resolution: the correct endpoints, measured

The path form is `wss://fstream.binance.com/<category>/ws/<stream>`. Both earlier attempts
omitted the `/ws/` segment and so hit `HTTP 404` on paths that do not exist — the failure was
in the probe, not in the venue.

Probed from **Nairobi and from a Paris host** (same script, same day). Every result below
agrees across both locations, which is what establishes it as a catalogue split rather than a
local artefact:

| Stream | `/public/ws/` | `/market/ws/` |
|---|---|---|
| `btcusdt@depth` | **delivers** | silent |
| `btcusdt@trade` | **delivers** | silent |
| `btcusdt@aggTrade` | silent | **delivers** |
| `btcusdt@markPrice` | silent | **delivers** |
| `btcusdt@kline_1m` | silent | **delivers** |
| `btcusdt@forceOrder` | silent | **delivers** |
| `!forceOrder@arr` | silent | **delivers** |

This matches the venue's stated split exactly: `/public` carries high-frequency channels,
`/market` carries regular market data.

### 8.1 The failure mode this creates, which is worse than a 404

A `SUBSCRIBE` for a `/market` channel, sent over an open `/public` connection, is
**acknowledged with `{"result": null}` — the venue's success response — and then delivers
nothing.** Measured directly: a `/public` connection that accepted a subscription for
`btcusdt@aggTrade` and `!forceOrder@arr` returned 119 `depthUpdate` messages and zero of
either, with no error at any layer.

A recorder built on the reasonable assumption that an acknowledged subscription is a working
subscription would produce a log containing a `SUBSCRIPTION_ACK`, no errors, a passing
integrity check, and no liquidations — and the natural reading of that log is *"forced flow is
rare"*. That is the same class of error §6 describes, arrived at by a different route.

`recorder/binance.py` therefore now emits a `SUBSCRIPTION_SILENT` recorder event naming any
channel that was subscribed, acknowledged, and never delivered on that connection. An
acknowledgement is a claim by the venue; delivery is the evidence.

### 8.2 Consequence for the recorder: two connections, not one

The two categories cannot share a connection, so futures now runs **two websockets into one
log on one clock** — `depth`+`trade` on `/public/ws/`, `!forceOrder@arr` on `/market/ws/`.

Verified over 120 s: **472 depth updates, 10,803 individual trades, 81 liquidations across 36
symbols, zero sequence gaps, integrity verified.**

Note the scope difference, which is now carried in the manifest: `!forceOrder@arr` is
**venue-wide**. It is not the recorded symbol's forced flow, and the first implementation
recorded it as though it were — `subscription_changed` hardcoded `["depth"], [symbol]`, which
filed 81 venue-wide liquidations under a single-symbol subscription claim. Corrected before any
real recording.

### 8.3 What T0.1 recovers

The blocked liquidation stream was treated as a pure loss of rigour: forced flow would have had
to be *inferred* from the trade stream. It is now available, which means the inference does not
have to be trusted — **it can be validated against it.** An inferred-cascade detector can be
scored against real liquidation labels on the same clock, which is the same independent-channel
pattern BAV-1 used to validate completeness labels. That is a stronger position than either
having the stream or inferring from it alone.

---

## 9. A second measurement, found while smoke-testing: receipt timestamps from Nairobi

The 120 s smoke test recorded **212 timestamp anomalies inside a 4.6 s wall-clock window**, all
carrying drift of 60.0–63.3 s. The venue clock was not the problem: an independent check
against `api.binance.com/api/v3/time` put local offset at −0.4 to −0.6 s, and `sntp` reported
+0.36 s.

The signature is a **throttled link draining a backlog**. Drift *rises* through the burst
(60.2 → 63.3 s), meaning delivery was slower than the venue was producing, so message age grew
while the backlog drained. A live REST call during the same session took **30.7 s**. This is
§7's instability, caught in the act.

**What this does and does not invalidate.**

`received_at` is unreliable from this location during stall episodes, so any analysis keyed to
receipt time — and any live quoting — is not safely done from here.

`venue_ts_ms` is unaffected. **Spot-versus-perp lead-lag is a venue-clock question**, so T0.2's
central measurement does not depend on the link being good, and the plan proceeds from Nairobi.

That relies on one assumption which Genesis has **not** verified and does not currently have a
way to verify: that Binance's spot and USD-M futures matching engines timestamp against
synchronised clocks. Recorded as an assumption, not a finding. If it is wrong, every lead-lag
number at sub-second resolution is wrong by the offset.
