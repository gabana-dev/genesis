"""
Kalshi WebSocket adapter. The only module that touches the network.

UNTESTED AGAINST THE LIVE VENUE. No API credentials were available when this was written, so
every line below is written from the published documentation and has never opened a real
connection. Nothing in the repository claims otherwise, and the health report will show an
empty observation period until this has actually run.

Kept deliberately thin: it opens a connection, subscribes, and hands raw messages to
`stream.Ingestor`. All sequence tracking, gap detection and persistence live in the
transport-agnostic core, so the untested surface is as small as possible.
"""

import asyncio
import base64
import json
import os
import time
import uuid

import events as E

WS_URL = "wss://api.elections.kalshi.com/trade-api/ws/v2"
DEMO_WS_URL = "wss://demo-api.kalshi.co/trade-api/ws/v2"

PUBLIC_CHANNELS = ("ticker", "trade", "market_lifecycle_v2")
BOOK_CHANNELS = ("orderbook_delta",)
PRIVATE_CHANNELS = ("fill",)


def _sign(private_key_pem: bytes, message: str) -> str:
    """
    RSA-PSS signature over `timestamp + method + path`, per Kalshi's documented auth scheme.
    `cryptography` is imported lazily so the rest of the package has no dependency on it.
    """
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError as e:
        raise RuntimeError(
            "Kalshi authentication needs the `cryptography` package: uv pip install cryptography"
        ) from e
    key = serialization.load_pem_private_key(private_key_pem, password=None)
    sig = key.sign(
        message.encode("utf-8"),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256(),
    )
    return base64.b64encode(sig).decode("utf-8")


def auth_headers(key_id=None, private_key_path=None, path="/trade-api/ws/v2"):
    key_id = key_id or os.environ.get("KALSHI_KEY_ID")
    private_key_path = private_key_path or os.environ.get("KALSHI_PRIVATE_KEY_PATH")
    if not key_id or not private_key_path:
        raise RuntimeError(
            "Set KALSHI_KEY_ID and KALSHI_PRIVATE_KEY_PATH to record from the live venue.")
    ts = str(int(time.time() * 1000))
    with open(private_key_path, "rb") as fh:
        pem = fh.read()
    return {
        "KALSHI-ACCESS-KEY": key_id,
        "KALSHI-ACCESS-SIGNATURE": _sign(pem, ts + "GET" + path),
        "KALSHI-ACCESS-TIMESTAMP": ts,
    }


async def record(ingestor, market_tickers, channels=None, url=WS_URL,
                 stop_after=None, reconnect=True):
    """
    Connect, subscribe, and stream messages into the ingestor until stopped.

    Every connection attempt, close and failure becomes an event. A reconnect clears sequence
    continuity in the ingestor, which is what makes the resulting gap visible in replay rather
    than silently healed.
    """
    import websockets

    channels = list(channels or (BOOK_CHANNELS + PUBLIC_CHANNELS))
    deadline = None if stop_after is None else time.time() + stop_after

    while True:
        connection_id = str(uuid.uuid4())
        try:
            headers = auth_headers()
            async with websockets.connect(url, additional_headers=headers) as ws:
                ingestor.connection_opened(connection_id, url)
                sub = {"id": 1, "cmd": "subscribe",
                       "params": {"channels": channels, "market_tickers": list(market_tickers)}}
                await ws.send(json.dumps(sub))
                ingestor.subscription_changed(channels, market_tickers)

                while True:
                    if deadline is not None and time.time() > deadline:
                        ingestor.connection_closed("stop_after reached")
                        return
                    timeout = None if deadline is None else max(0.1, deadline - time.time())
                    try:
                        payload = await asyncio.wait_for(ws.recv(), timeout=timeout)
                    except asyncio.TimeoutError:
                        ingestor.connection_closed("stop_after reached")
                        return
                    received_at = E.now()
                    try:
                        raw = json.loads(payload)
                    except json.JSONDecodeError as e:
                        ingestor.malformed(payload, e)
                        continue
                    ingestor.observe(raw, received_at=received_at)

        except Exception as e:  # network, auth, protocol -- all are recorded, none are hidden
            ingestor.error(type(e).__name__, e)
            ingestor.connection_closed(f"exception: {type(e).__name__}")
            if not reconnect or (deadline is not None and time.time() > deadline):
                return
            await asyncio.sleep(2.0)
