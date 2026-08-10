"""
Venue dialects: how to read a raw message without changing it.

A dialect answers four questions about a payload the recorder did not design -- which
channel is this, which market, what is its sequence, and what is the venue's timestamp --
and nothing else. It never rewrites `raw`, never normalises one venue into another's shape,
and never infers a value the venue did not send.

That last rule is why Binance is a dialect and not a translation. Kalshi sends `delta_fp`,
a CHANGE to a level. Binance sends `b`/`a` entries that are the new ABSOLUTE size at a
price, with "0" meaning remove. Converting Binance into Kalshi's form would require knowing
the prior book, which is inference dressed as ingestion. The two semantics are recorded as
what they are, and `replay` applies each accordingly.

Sequence is generalised to a RANGE. Binance carries `U` (first update id) and `u` (final),
with contiguity `next.U == prev.u + 1`. Kalshi's single `seq` is the degenerate case where
first == last, so one rule covers both.
"""


def kalshi_extract(raw: dict) -> dict:
    msg = raw.get("msg") if isinstance(raw.get("msg"), dict) else {}
    seq = raw.get("seq")
    return {
        "channel": raw.get("type") or "unknown",
        "market": msg.get("market_ticker"),
        "seq_first": seq,
        "seq_last": seq,
        "venue_ts_ms": msg.get("ts_ms"),
        "subscription_id": raw.get("sid"),
        "msg": msg,
    }


def binance_extract(raw: dict) -> dict:
    # Binance is flat: the message IS the payload, there is no nested `msg`.
    # The REST depth snapshot has a different shape again -- {lastUpdateId, bids, asks} --
    # with no event type, no symbol and no timestamp. It is given the synthetic channel
    # name "depthSnapshot" so replay can tell an anchor from an update; the payload itself
    # is still stored verbatim.
    if "lastUpdateId" in raw and "e" not in raw:
        # D-A (BAV-1 run 1). `lastUpdateId` is a point-in-time marker, NOT a position in a
        # sequenced stream: consecutive REST fetches are not consecutive stream members, and
        # the id jumps by thousands between them. Treating it as a sequence made every fetch
        # after the first emit a SEQUENCE_GAP, and because REST payloads carry no symbol those
        # gaps had market_ticker=None and so invalidated EVERY market. In run 1 that marked
        # all 60 probes incomplete and left no baseline to compare against.
        # The value is preserved verbatim in world.raw and used as the reconciliation anchor;
        # it is simply not a stream sequence.
        return {"channel": "depthSnapshot", "market": raw.get("symbol"),
                "seq_first": None, "seq_last": None,
                "venue_ts_ms": None, "subscription_id": None, "msg": raw}
    return {
        "channel": raw.get("e") or "unknown",
        "market": raw.get("s"),
        "seq_first": raw.get("U"),
        "seq_last": raw.get("u"),
        "venue_ts_ms": raw.get("E"),
        "subscription_id": None,
        "msg": raw,
    }


KALSHI = {"name": "kalshi", "extract": kalshi_extract}
BINANCE = {"name": "binance", "extract": binance_extract}

BY_NAME = {"kalshi": KALSHI, "binance": BINANCE}
