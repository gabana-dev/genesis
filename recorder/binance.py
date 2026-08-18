"""
Binance spot depth adapter. Public market data only.

No account, no API key, no credentials, no orders. This is an unauthenticated read of a
public stream, used to test the recorder against traffic Genesis did not author. It is not a
trading integration and there is no order-submission path anywhere in this package.

Why this venue: Binance PUBLISHES its reconciliation rules, so the recorder's claims can be
checked against an external written standard rather than against an assumption --

    1. take a REST depth snapshot; note `lastUpdateId`
    2. drop any stream event where `u <= lastUpdateId`
    3. the first kept event must satisfy `U <= lastUpdateId + 1 <= u`
    4. every subsequent event must satisfy `U == previous u + 1`

Rule 4 is what the recorder's gap detection is tested against. Kalshi's `seq` scope was never
documented, so it could only ever be assumed.

Both the REST snapshot and the stream messages are recorded verbatim as observations. The
snapshot is an observation like any other -- it is not treated as ground truth that repairs
anything.
"""

import asyncio
import json
import time
import urllib.request
import uuid

import events as E

WS_URL = "wss://stream.binance.com:9443/ws/{symbol}@depth"
REST_SNAPSHOT = "https://api.binance.com/api/v3/depth?symbol={symbol}&limit=1000"

# USD-M futures is a DIFFERENT HOST and a different continuity rule (see dialects
# `binance_futures_extract`). Liquidations exist only here -- there is no spot equivalent --
# so recording forced flow requires this connection, not an extra subscription on the spot one.
#
# TWO BASE PATHS, AND THEY CANNOT SHARE A CONNECTION.
# Binance split the futures websocket by data category and decommissioned the legacy
# `/ws/<stream>` path on 2026-04-23. `/public` carries high-frequency channels (depth,
# trade); `/market` carries regular market data (forceOrder, aggTrade, markPrice, kline).
# Measured 2026-08-18 from two continents -- see
# research/binance-futures-stream-availability.md.
#
# A SUBSCRIBE for a `/market` channel sent over a `/public` connection is ACKNOWLEDGED with
# {"result": null} -- the venue's SUCCESS response -- and then delivers nothing, forever.
# That is why `record()` now reports channels that were subscribed and stayed silent: an
# acknowledged subscription is not evidence that data arrived.
FUTURES_PUBLIC_WS_URL = "wss://fstream.binance.com/public/ws/{symbol}@depth"
FUTURES_LIQUIDATION_WS_URL = "wss://fstream.binance.com/market/ws/!forceOrder@arr"
FUTURES_REST_SNAPSHOT = "https://fapi.binance.com/fapi/v1/depth?symbol={symbol}&limit=1000"

# Nairobi's link stalls: TCP maxima of 20-60 s against medians of 50-190 ms. The library
# default open timeout aborts a handshake that would have completed, and three such aborts
# read as "this stream is unavailable" rather than "the link stalled" -- which is exactly the
# wrong conclusion, and one already drawn once. Generous here; slow is not absent.
OPEN_TIMEOUT = 45

# Depth payloads are large; the default 1MB frame limit is not enough for busy books.
MAX_FRAME = 16 * 1024 * 1024

# Fixed id on our SUBSCRIBE, so the acknowledgement can be told apart from market data.
SUBSCRIBE_ID = 1


def rest_snapshot(symbol: str, timeout=20, rest=None) -> dict:
    """One unauthenticated GET. Returns the raw payload, unmodified."""
    url = (rest or REST_SNAPSHOT).format(symbol=symbol.upper())
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


async def record(ingestor, symbol, stop_after=None, reconnect_after=None, reconnect=True,
                 extra_streams=("aggTrade",), ws_url=None, rest_url=None, snapshot=True,
                 subscribed_as=("depth",), markets=None):
    """
    Observe the depth stream, recording everything. Additional channels are SUBSCRIBEd on the
    same connection.

    WHY SUBSCRIBE RATHER THAN A COMBINED-STREAM URL
        Binance offers `/stream?streams=a/b`, which wraps every payload as
        {"stream": ..., "data": {...}}. Storing the unwrapped inner object would break
        invariant 3 -- `raw` is what the venue sent -- and storing the wrapper would make the
        dialect read a shape no single-stream recording has. Subscribing over the existing
        `/ws/<stream>` connection leaves payloads in their documented form, so one dialect
        covers both and every prior recording stays comparable.

    WHY aggTrade, AND WHY IT MUST BE RECORDED LIVE
        EXEC-1 carried no trade stream, so every fill was inferred from book evolution and
        reported as a bracket. Binance publishes historical aggTrades, but publishes no book
        at this resolution -- so book AND trades on one clock, under this recorder's own
        completeness labels, cannot be backfilled. It exists only if recorded.

    `reconnect_after` forces one deliberate reconnect that many seconds in, so the recorder's
    reconnect handling is exercised even when the venue behaves perfectly for the whole run.
    It is recorded as DELIBERATE in the event body -- a forced reconnect that looked like a
    natural one would be fabricated evidence.

    `snapshot=False` suppresses the REST anchor. The liquidation stream is a feed of discrete
    events, not a book: there is no depth endpoint to anchor it against, and fetching the
    unrelated depth snapshot alongside it would file an observation of one market as context
    for another.
    """
    import websockets

    ws_base = ws_url or WS_URL
    rest_base = rest_url or REST_SNAPSHOT
    url = ws_base.format(symbol=symbol.lower())
    # D-1 (research/exec-1-recording-defects.md). These were computed from `loop.time()`, a
    # MONOTONIC clock, which on macOS does not advance while the host is asleep -- so
    # `--seconds N` bounded N seconds of WAKEFULNESS, not N seconds of elapsed time. The
    # EXEC-1 host slept 6.28h across 18 episodes and the run was still going 3h54m past its
    # nominal end, silently and without bound.
    #
    # Wall clock is what a caller passing 604800 means, and what a pre-registered "7 days"
    # window means. NTP can step this clock, but by seconds over a week -- negligible beside
    # the hours a monotonic clock loses to sleep.
    deadline = None if stop_after is None else time.time() + stop_after
    forced_at = None if reconnect_after is None else time.time() + reconnect_after
    forced_done = False

    async def anchor():
        """
        Re-fetch the REST snapshot. Binance's procedure requires this after EVERY (re)connect,
        not once at startup: a reconnect loses the update chain, and without a fresh
        lastUpdateId there is nothing to reconcile the resumed stream against. Recorded as an
        observation like any other -- it anchors the book, it does not repair it.

        D-5, found in the first three-connection recording and the reason this is a coroutine.
        `rest_snapshot` is BLOCKING urllib inside an async coroutine. With one connection that
        merely delayed that connection. With several sharing an event loop it froze ALL of
        them for the duration of the fetch -- and from Nairobi these fetches take 30-90
        seconds. The measured damage in a 180 s run: one connection's ack arrived 81 s late,
        another took 80 s to open, 768 timestamp anomalies, and pong timeouts that killed
        connections the venue had no complaint about.

        That is not merely slow. T0.2's entire premise is that the ORDER of events in this log
        is the real arrival order on one clock. A stall that freezes two feeds while a third
        fetches destroys exactly that, and would have done so silently -- the log would show a
        confident interleaving that was an artefact of which coroutine held the loop.

        Only the network call is moved off the loop. `observe()` still runs on the loop
        thread, so appends stay strictly ordered and the no-await-inside-observe invariant
        holds.
        """
        try:
            snap = await asyncio.to_thread(rest_snapshot, symbol, 20, rest_base)
            ingestor.observe(snap, request={"url": rest_base.format(symbol=symbol.upper()),
                                            "symbol": symbol.upper()})
        except Exception as e:
            ingestor.error("rest_snapshot_failed", e)

    def report_silent(channels_seen, connection_id):
        """
        Name any channel that was subscribed, acknowledged, and never delivered.

        This is not defensive padding. Binance ACKNOWLEDGES a SUBSCRIBE for a channel that
        lives on a different base path -- {"result": null}, its success response -- and then
        sends nothing. Measured directly: a `/public` connection accepted an `aggTrade` and
        `!forceOrder@arr` subscription and delivered 119 depthUpdates and zero of either.
        Without this, the log would contain a SUBSCRIPTION_ACK, no errors, and a healthy
        integrity check, and the missing channel would read as "the market was quiet."
        """
        missing = [s for s in extra_streams if s not in channels_seen]
        if missing:
            ingestor.log.append(
                E.RECORDER, "SUBSCRIPTION_SILENT",
                {"channels": missing, "connection_id": connection_id, "url": url,
                 "note": "subscribed and acknowledged, but zero messages on this connection"})

    while True:
        connection_id = str(uuid.uuid4())
        # Per-connection, because a subscription is re-established per connection: a channel
        # that delivered on the last connection proves nothing about this one.
        channels_seen = set()
        try:
            async with websockets.connect(url, max_size=MAX_FRAME,
                                          open_timeout=OPEN_TIMEOUT) as ws:
                ingestor.connection_opened(connection_id, url)
                if extra_streams:
                    # Re-sent on EVERY reconnect. A subscription established once and assumed
                    # to persist across a drop is the same class of error as a stale
                    # checkpoint: the recording would look healthy while silently missing a
                    # channel from the first disconnection onward.
                    await ws.send(json.dumps({
                        "method": "SUBSCRIBE",
                        "params": [f"{symbol.lower()}@{s}" for s in extra_streams],
                        "id": SUBSCRIBE_ID}))
                # The channel carried by the URL itself, plus whatever was SUBSCRIBEd.
                # `subscribed_as` and `markets` are parameters because the liquidation
                # connection is neither depth nor one symbol: it is `!forceOrder@arr` across
                # the WHOLE VENUE. Hardcoding ["depth"], [symbol] recorded a subscription
                # claim that was simply false, and a false claim in the provenance chain is
                # worse than a missing one -- it would have made 81 venue-wide liquidations
                # look like this symbol's forced flow.
                ingestor.subscription_changed([*subscribed_as, *extra_streams],
                                              markets if markets is not None
                                              else [symbol.upper()])
                if snapshot:
                    await anchor()

                while True:
                    now = time.time()
                    if deadline is not None and now >= deadline:
                        report_silent(channels_seen, connection_id)
                        ingestor.connection_closed("stop_after reached")
                        return
                    if forced_at is not None and not forced_done and now >= forced_at:
                        forced_done = True
                        ingestor.log.append(
                            E.RECORDER, "RECONNECT_FORCED",
                            {"reason": "deliberate reconnect to exercise recovery",
                             "deliberate": True, "connection_id": connection_id})
                        report_silent(channels_seen, connection_id)
                        ingestor.connection_closed("deliberate reconnect")
                        break

                    timeout = 5.0 if deadline is None else max(0.1, min(5.0, deadline - now))
                    try:
                        payload = await asyncio.wait_for(ws.recv(), timeout=timeout)
                    except asyncio.TimeoutError:
                        continue
                    received_at = E.now()
                    try:
                        raw = json.loads(payload)
                    except json.JSONDecodeError as e:
                        ingestor.malformed(payload, e)
                        continue
                    if isinstance(raw, dict) and raw.get("id") == SUBSCRIBE_ID \
                            and "result" in raw:
                        # The SUBSCRIBE acknowledgement. Not an observation of the market --
                        # passing it to observe() would record it as a WORLD event with an
                        # unknown channel and no market. Recorded as a recorder event so the
                        # subscription is evidenced rather than assumed, and so a rejected
                        # subscription is visible instead of silent.
                        ingestor.log.append(E.RECORDER, "SUBSCRIPTION_ACK",
                                            {"result": raw.get("result"), "id": raw.get("id"),
                                             "streams": list(extra_streams),
                                             "connection_id": connection_id,
                                             "received_at": received_at})
                        continue
                    if isinstance(raw, dict) and raw.get("e"):
                        channels_seen.add(raw["e"])
                    ingestor.observe(raw, received_at=received_at)

        except Exception as e:
            ingestor.error(type(e).__name__, e)
            report_silent(channels_seen, connection_id)
            ingestor.connection_closed(f"exception: {type(e).__name__}")

        if deadline is not None and time.time() >= deadline:
            return
        if not reconnect:
            return
        await asyncio.sleep(1.0)
