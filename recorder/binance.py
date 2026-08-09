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
import urllib.request
import uuid

import events as E

WS_URL = "wss://stream.binance.com:9443/ws/{symbol}@depth"
REST_SNAPSHOT = "https://api.binance.com/api/v3/depth?symbol={symbol}&limit=1000"

# Depth payloads are large; the default 1MB frame limit is not enough for busy books.
MAX_FRAME = 16 * 1024 * 1024


def rest_snapshot(symbol: str, timeout=20) -> dict:
    """One unauthenticated GET. Returns the raw payload, unmodified."""
    url = REST_SNAPSHOT.format(symbol=symbol.upper())
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


async def record(ingestor, symbol, stop_after=None, reconnect_after=None, reconnect=True):
    """
    Observe the depth stream, recording everything.

    `reconnect_after` forces one deliberate reconnect that many seconds in, so the recorder's
    reconnect handling is exercised even when the venue behaves perfectly for the whole run.
    It is recorded as DELIBERATE in the event body -- a forced reconnect that looked like a
    natural one would be fabricated evidence.
    """
    import websockets

    loop = asyncio.get_running_loop()
    url = WS_URL.format(symbol=symbol.lower())
    deadline = None if stop_after is None else loop.time() + stop_after
    forced_at = None if reconnect_after is None else loop.time() + reconnect_after
    forced_done = False

    def anchor():
        """
        Re-fetch the REST snapshot. Binance's procedure requires this after EVERY (re)connect,
        not once at startup: a reconnect loses the update chain, and without a fresh
        lastUpdateId there is nothing to reconcile the resumed stream against. Recorded as an
        observation like any other -- it anchors the book, it does not repair it.
        """
        try:
            snap = rest_snapshot(symbol)
            ingestor.observe(snap, request={"url": REST_SNAPSHOT.format(symbol=symbol.upper()),
                                            "symbol": symbol.upper()})
        except Exception as e:
            ingestor.error("rest_snapshot_failed", e)

    while True:
        connection_id = str(uuid.uuid4())
        try:
            async with websockets.connect(url, max_size=MAX_FRAME) as ws:
                ingestor.connection_opened(connection_id, url)
                ingestor.subscription_changed(["depth"], [symbol.upper()])
                anchor()

                while True:
                    now = loop.time()
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
                    ingestor.observe(raw, received_at=received_at)

        except Exception as e:
            ingestor.error(type(e).__name__, e)
            ingestor.connection_closed(f"exception: {type(e).__name__}")

        if deadline is not None and loop.time() >= deadline:
            return
        if not reconnect:
            return
        await asyncio.sleep(1.0)
