"""
Hyperliquid adapter. Public market data only.

No account, no key, no credentials, no orders. This is an unauthenticated read of a public
websocket, recorded for one reason: **Hyperliquid names the wallets on both sides of every
trade**, and no centralised venue does.

WHY THIS RECORDING EXISTS
    T2.1 -- separating forced from informed flow -- has been blocked because Binance's trade
    stream carries no account information, so participant attribution could only ever be
    inferred. Zhai (2026, arXiv:2608.04373) shows informativeness is a PERSISTENT wallet
    attribute, with rank correlation 0.52 across adjacent ten-day windows. That method needs
    identity, and identity exists here.

    Hyperliquid publishes a historical archive, but it is a Requester Pays S3 bucket and
    downloading it costs money. Recording forward is free, and two ten-day windows is about
    twenty days -- far less than the ninety ECON-1 needs.

WHAT THIS RECORDING CANNOT CLAIM
    No gap detection. `tid` is not a stream position (see dialects.hyperliquid_extract), so an
    absence of SEQUENCE_GAP events here means the check was impossible, not that it passed.
"""

import asyncio
import json
import time
import uuid

import events as E

WS_URL = "wss://api.hyperliquid.xyz/ws"
MAX_FRAME = 16 * 1024 * 1024
OPEN_TIMEOUT = 45


async def record(ingestor, coin="BTC", stop_after=None, subscriptions=("trades",),
                 reconnect=True):
    """Subscribe and record verbatim. Re-subscribes on every reconnect."""
    import websockets

    deadline = None if stop_after is None else time.time() + stop_after
    while True:
        connection_id = str(uuid.uuid4())
        seen = set()
        try:
            async with websockets.connect(WS_URL, max_size=MAX_FRAME,
                                          open_timeout=OPEN_TIMEOUT,
                                          ping_interval=20) as ws:
                ingestor.connection_opened(connection_id, WS_URL)
                for s in subscriptions:
                    await ws.send(json.dumps({"method": "subscribe",
                                              "subscription": {"type": s, "coin": coin}}))
                ingestor.subscription_changed(list(subscriptions), [coin])

                while True:
                    now = time.time()
                    if deadline is not None and now >= deadline:
                        _report_silent(ingestor, subscriptions, seen, connection_id)
                        ingestor.connection_closed("stop_after reached")
                        return
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
                    ch = raw.get("channel")
                    if ch == "subscriptionResponse":
                        # The venue's acknowledgement, not an observation of the market.
                        ingestor.log.append(E.RECORDER, "SUBSCRIPTION_ACK",
                                            {"result": raw.get("data"),
                                             "connection_id": connection_id,
                                             "received_at": received_at})
                        continue
                    if ch:
                        seen.add(ch)
                    ingestor.observe(raw, received_at=received_at)

        except Exception as e:
            ingestor.error(type(e).__name__, e)
            _report_silent(ingestor, subscriptions, seen, connection_id)
            ingestor.connection_closed(f"exception: {type(e).__name__}")

        if deadline is not None and time.time() >= deadline:
            return
        if not reconnect:
            return
        await asyncio.sleep(1.0)


def _report_silent(ingestor, subscriptions, seen, connection_id):
    """An acknowledged subscription is a claim; delivery is the evidence. See binance.py."""
    missing = [s for s in subscriptions if s not in seen]
    if missing:
        ingestor.log.append(E.RECORDER, "SUBSCRIPTION_SILENT",
                            {"channels": missing, "connection_id": connection_id,
                             "url": WS_URL,
                             "note": "subscribed and acknowledged, zero messages"})
