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

Sequence is generalised to a RANGE. Binance SPOT carries `U` (first update id) and `u`
(final), with contiguity `next.U == prev.u + 1`. Kalshi's single `seq` is the degenerate case
where first == last, so one rule covers both.

Binance FUTURES chains differently -- `pu == prev.u` -- and is a separate dialect for that
reason. It is expressed in the same range abstraction rather than by special-casing the
checker; see `binance_futures_extract`. Assuming the spot rule there would emit a gap on
nearly every message.
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
    if raw.get("e") == "aggTrade":
        # An aggregate trade carries `f`/`l` -- the first and last individual trade id it
        # aggregates -- which is a contiguous range on the same footing as depth's U/u. It
        # does NOT carry U/u, so reading those would give (None, None) and silently disable
        # gap detection on the busiest channel.
        #
        # Trade ids and depth update ids are different number spaces on the same symbol.
        # `stream` keys sequence state by (subscription, channel, market), so they cannot
        # collide -- but only because `channel` is in that key. If it were ever removed,
        # interleaving these two streams would emit a SEQUENCE_GAP on nearly every message.
        return {
            "channel": "aggTrade",
            "market": raw.get("s"),
            "seq_first": raw.get("f"),
            "seq_last": raw.get("l"),
            "venue_ts_ms": raw.get("E"),
            "subscription_id": None,
            "msg": raw,
        }
    return {
        "channel": raw.get("e") or "unknown",
        "market": raw.get("s"),
        "seq_first": raw.get("U"),
        "seq_last": raw.get("u"),
        "venue_ts_ms": raw.get("E"),
        "subscription_id": None,
        "msg": raw,
    }


def binance_futures_extract(raw: dict) -> dict:
    """
    Binance USD-M futures. A DIFFERENT dialect from spot, not a variant of it.

    TWO RULES DIFFER, AND BOTH WOULD CORRUPT SILENTLY IF ASSUMED IDENTICAL.

    1. CONTINUITY. Spot chains on `U == previous u + 1`. Futures chains on `pu == previous u`
       -- `pu` being the previous stream event's final update id, a field spot does not send.
       Futures `U` is allowed to jump, so applying the spot rule here would emit a
       SEQUENCE_GAP on nearly every message and a healthy recording would look destroyed.

       Rather than special-case `stream.py`, the futures rule is expressed in the existing
       range abstraction: seq_first = pu + 1, seq_last = u. The generic check
       `seq_first == last + 1` then reduces to `pu + 1 == previous u + 1`, i.e. exactly
       `pu == previous u`. One continuity rule in one place still covers both venues.

       `U` is not carried in the extract and is not needed: it serves only the initial
       snapshot reconciliation, which the recorder performs by re-anchoring. The raw payload
       retains it verbatim (invariant 3), so nothing is lost.

    2. LIQUIDATIONS ARE NESTED, AND SAMPLED. `forceOrder` carries its order under `o` rather
       than flat, and -- documented by the venue -- **only the largest liquidation per symbol
       in each 1000 ms window is published.** It is therefore an INDICATOR of forced flow,
       never a count of it and never a sum of its size. Anything that totals liquidation
       volume from this stream is measuring the venue's sampling rule, not the market.
       It carries no sequence, so gap detection is impossible on it and none is claimed.
    """
    e = raw.get("e")

    if e == "forceOrder":
        return {"channel": "forceOrder",
                "market": (raw.get("o") or {}).get("s"),
                "seq_first": None, "seq_last": None,
                "venue_ts_ms": raw.get("E"), "subscription_id": None, "msg": raw}

    if e == "trade":
        # Individual trades. `t` is a single trade id -- the degenerate range where
        # first == last, which the abstraction already covers.
        #
        # Futures serves `@trade` but NOT `@aggTrade` to this location (see
        # research/binance-futures-stream-availability.md), and individual trades are the
        # better record anyway: aggTrade merges same-price fills from one taker order, which
        # is precisely the granularity flow attribution needs to keep.
        return {"channel": "trade", "market": raw.get("s"),
                "seq_first": raw.get("t"), "seq_last": raw.get("t"),
                "venue_ts_ms": raw.get("E"), "subscription_id": None, "msg": raw}

    if e == "aggTrade":
        return {"channel": "aggTrade", "market": raw.get("s"),
                "seq_first": raw.get("f"), "seq_last": raw.get("l"),
                "venue_ts_ms": raw.get("E"), "subscription_id": None, "msg": raw}

    if e == "depthUpdate":
        pu = raw.get("pu")
        return {"channel": "depthUpdate", "market": raw.get("s"),
                "seq_first": (pu + 1) if isinstance(pu, int) else raw.get("U"),
                "seq_last": raw.get("u"),
                "venue_ts_ms": raw.get("E"), "subscription_id": None, "msg": raw}

    if "lastUpdateId" in raw and e is None:
        return {"channel": "depthSnapshot", "market": raw.get("symbol"),
                "seq_first": None, "seq_last": None,
                "venue_ts_ms": None, "subscription_id": None, "msg": raw}

    return {"channel": e or "unknown", "market": raw.get("s"),
            "seq_first": None, "seq_last": None,
            "venue_ts_ms": raw.get("E"), "subscription_id": None, "msg": raw}


KALSHI = {"name": "kalshi", "extract": kalshi_extract}
BINANCE = {"name": "binance", "extract": binance_extract}
BINANCE_FUTURES = {"name": "binance_futures", "extract": binance_futures_extract}

BY_NAME = {"kalshi": KALSHI, "binance": BINANCE, "binance_futures": BINANCE_FUTURES}
