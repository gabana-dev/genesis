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
FUTURES_WS_URL = "wss://fstream.binance.com/ws/{symbol}@depth"
FUTURES_REST_SNAPSHOT = "https://fapi.binance.com/fapi/v1/depth?symbol={symbol}&limit=1000"

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
                 extra_streams=("aggTrade",), ws_url=None, rest_url=None):
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

    def anchor():
        """
        Re-fetch the REST snapshot. Binance's procedure requires this after EVERY (re)connect,
        not once at startup: a reconnect loses the update chain, and without a fresh
        lastUpdateId there is nothing to reconcile the resumed stream against. Recorded as an
        observation like any other -- it anchors the book, it does not repair it.
        """
        try:
            snap = rest_snapshot(symbol, rest=rest_base)
            ingestor.observe(snap, request={"url": rest_base.format(symbol=symbol.upper()),
                                            "symbol": symbol.upper()})
        except Exception as e:
            ingestor.error("rest_snapshot_failed", e)

    while True:
        connection_id = str(uuid.uuid4())
        try:
            async with websockets.connect(url, max_size=MAX_FRAME) as ws:
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
                ingestor.subscription_changed(["depth", *extra_streams], [symbol.upper()])
                anchor()

                while True:
                    now = time.time()
                    if deadline is not None and now >= deadline:
                        ingestor.connection_closed("stop_after reached")
                        return
                    if forced_at is not None and not forced_done and now >= forced_at:
                        forced_done = True
                        ingestor.log.append(
                            E.RECORDER, "RECONNECT_FORCED",
                            {"reason": "deliberate reconnect to exercise recovery",
                             "deliberate": True, "connection_id": connection_id})
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
                    ingestor.observe(raw, received_at=received_at)

        except Exception as e:
            ingestor.error(type(e).__name__, e)
            ingestor.connection_closed(f"exception: {type(e).__name__}")

        if deadline is not None and time.time() >= deadline:
            return
        if not reconnect:
            return
        await asyncio.sleep(1.0)
