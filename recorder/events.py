"""
Event construction, canonical serialisation and hash chaining.

The envelope is the unit of truth. Every field that distinguishes what the venue said from
what Genesis observed lives here, and nothing in this module merges them.

Canonical form matters: the hash chain is only meaningful if two processes serialise the same
event to the same bytes. `canonical_json` fixes key order, separators and unicode handling.
"""

import hashlib
import json
import math
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

GENESIS_HASH = "0" * 64

WORLD = "OBSERVATION"
DECISION = "DECISION"
INTENT = "INTENT"
EXECUTION = "EXECUTION"
RECORDER = "RECORDER"

CLASSES = (WORLD, DECISION, INTENT, EXECUTION, RECORDER)


def now() -> str:
    """Genesis clock. Always UTC, always microseconds — never a venue timestamp."""
    return datetime.now(timezone.utc).isoformat()


def canonical_json(obj) -> str:
    """
    Strict, deterministic JSON. `allow_nan=False` matters: Python will otherwise emit bare
    NaN/Infinity, which no conforming parser accepts, so the hash would not be reproducible
    by another implementation. Non-finite values are rejected at ingestion instead.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def has_non_finite(obj) -> bool:
    """True if any float in the structure is NaN or +/-Infinity."""
    if isinstance(obj, float):
        return not math.isfinite(obj)
    if isinstance(obj, dict):
        return any(has_non_finite(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return any(has_non_finite(v) for v in obj)
    return False


def canon_decimal(value, allow_negative=True):
    """
    SPEC invariant 9. One decimal string per numeric value, so "0.50", "0.5000" and numeric
    0.5 all become the same key. Trailing zeros are stripped without exponent notation, and no
    precision is discarded. Returns None for values that cannot be interpreted.

    `str(value)` before `Decimal` is deliberate: it routes a binary float through its shortest
    repr, so 0.1 becomes Decimal("0.1") rather than the exact binary expansion.

    Zero is always "0". Without this, Decimal("-0.00") normalises to "-0" and becomes a second
    book key for the same value -- the mirror image of the price-collision defect.
    """
    if value is None or isinstance(value, bool):
        return None
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not d.is_finite():
        return None
    if d == 0:
        return "0"
    if not allow_negative and d < 0:
        return None
    return format(d.normalize(), "f")


# Representation is shared; VALIDITY IS NOT. The rules differ by the role a number plays, not
# by its type, and collapsing them is how a negative resting size became book state:
#
#   price  -- what one unit costs. Never negative.
#   size   -- a resting quantity at a level. Never negative.
#   qty    -- a delta amount or a signed position change. Negative is normal and meaningful.
#   money  -- cash, fees, realised P&L. Signed by nature.
#
# Venue-specific range policy (Kalshi binary contracts trade in [0,1]) is deliberately NOT
# enforced here: it is the venue's rule, it can change, and encoding it would silently reject
# real data if it did.
def canon_price(value):
    return canon_decimal(value, allow_negative=False)


def canon_size(value):
    return canon_decimal(value, allow_negative=False)


def canon_qty(value):
    return canon_decimal(value, allow_negative=True)


def canon_money(value):
    return canon_decimal(value, allow_negative=True)


def to_decimal(value, default="0") -> Decimal:
    """Parse a canonical decimal string back to Decimal. Never returns a float."""
    if value is None or value == "":
        return Decimal(default)
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal(default)


def content_hash(obj) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def event_hash(envelope: dict, prev_hash: str) -> str:
    body = {k: v for k, v in envelope.items() if k != "hash"}
    return hashlib.sha256((canonical_json(body) + prev_hash).encode("utf-8")).hexdigest()


def make_event(event_class: str, event_type: str, body: dict,
               event_index: int, prev_hash: str, recorder_run: str) -> dict:
    if event_class not in CLASSES:
        raise ValueError(f"unknown event class: {event_class}")
    envelope = {
        "event_index": event_index,
        "event_id": str(uuid.uuid4()),
        "event_class": event_class,
        "event_type": event_type,
        "recorded_at": now(),
        "recorder_run": recorder_run,
        "body": body,
        "prev_hash": prev_hash,
    }
    envelope["hash"] = event_hash(envelope, prev_hash)
    return envelope


# ---- body constructors ---------------------------------------------------------------
# Each keeps `world` and `observation` as separate objects. Extraction from raw is for
# indexing only; `raw` is authoritative and is never rewritten.

def canonical_view(channel: str, msg: dict) -> dict:
    """
    Price-canonical projection of the venue message, computed once at ingestion so that
    replay never has to guess how a price was spelled. `raw` remains authoritative and
    untouched (invariant 3); this sits beside it.
    """
    invalid = []

    def bad(field, value, reason):
        invalid.append({"field": field, "value": str(value)[:120], "reason": reason})

    if channel == "orderbook_delta":
        price = canon_price(msg.get("price_dollars"))
        if price is None:
            bad("price_dollars", msg.get("price_dollars"), "not a non-negative decimal")
        amount = canon_qty(msg.get("delta_fp"))
        if amount is None:
            bad("delta_fp", msg.get("delta_fp"), "not a decimal")
        side = msg.get("side")
        if side not in ("yes", "no"):
            bad("side", side, "not 'yes' or 'no'")
        out = {"price_dollars": price, "side": side, "delta_fp": amount}
        if invalid:
            out["invalid"] = invalid
        return out

    if channel in ("depthUpdate", "depthSnapshot"):
        # Absolute level assignment. A quantity of "0" is a REMOVAL, not an error and not a
        # missing level -- unlike a snapshot, where a zero size is simply not a level.
        out = {"absolute": True}
        # The WS stream names the level arrays b/a; the REST snapshot names them bids/asks.
        # Reading only b/a silently canonicalised every REST anchor to an empty book.
        keys = (("b", "bids"), ("a", "asks")) if channel == "depthUpdate" \
            else (("bids", "bids"), ("asks", "asks"))
        for key, name in keys:
            levels = []
            for lv in msg.get(key) or []:
                if not isinstance(lv, (list, tuple)) or len(lv) < 2:
                    bad(name, lv, "level is not a [price, size] pair")
                    continue
                price, size = canon_price(lv[0]), canon_size(lv[1])
                if price is None:
                    bad(f"{name}.price", lv[0], "not a non-negative decimal")
                    continue
                if size is None:
                    bad(f"{name}.size", lv[1], "not a non-negative decimal")
                    continue
                levels.append([price, size])
            out[name] = levels
        if invalid:
            out["invalid"] = invalid
        return out

    if channel == "orderbook_snapshot":
        out = {}
        for side in ("yes", "no"):
            levels = []
            for lv in msg.get(f"{side}_dollars_fp") or []:
                if not isinstance(lv, (list, tuple)) or len(lv) < 2:
                    bad(f"{side}_dollars_fp", lv, "level is not a [price, size] pair")
                    continue
                price, size = canon_price(lv[0]), canon_size(lv[1])
                if price is None:
                    bad(f"{side}_dollars_fp.price", lv[0], "not a non-negative decimal")
                    continue
                if size is None:
                    bad(f"{side}_dollars_fp.size", lv[1], "not a non-negative decimal")
                    continue
                if size == "0":
                    continue          # a zero resting size is not a level
                levels.append([price, size])
            out[side] = levels
        if invalid:
            out["invalid"] = invalid
        return out

    return {}


def observation_body(raw: dict, received_at: str, connection_id: str,
                     extracted: dict, request=None) -> dict:
    """
    `extracted` comes from a dialect. `raw` is stored verbatim and never rewritten.

    `request` records what Genesis ASKED FOR -- a URL, a symbol. That is Genesis's own
    knowledge, not the venue's statement, so it belongs on the observation side and never
    inside `world`. Binance's REST depth snapshot carries no symbol; writing one into
    `world.market_ticker` would attribute to the venue something it did not say.
    """
    channel = extracted["channel"]
    return {
        "observation": {
            "received_at": received_at,
            "connection_id": connection_id,
            "subscription_id": extracted.get("subscription_id"),
            "request": request,
        },
        "world": {
            "raw": raw,
            "venue_seq": extracted.get("seq_first"),
            "venue_seq_last": extracted.get("seq_last"),
            "venue_ts_ms": extracted.get("venue_ts_ms"),
            "market_ticker": extracted.get("market"),
            "channel": channel,
            "canonical": canonical_view(channel, extracted.get("msg") or {}),
        },
    }


def decision_body(boundary_at: str, model_id: str, model_version: str,
                  input_event_ids: list, decision: dict, rationale=None) -> dict:
    joined = canonical_json(sorted(input_event_ids))
    return {
        "boundary_at": boundary_at,
        "model_id": model_id,
        "model_version": model_version,
        "inputs_hash": hashlib.sha256(joined.encode("utf-8")).hexdigest(),
        "input_event_ids": input_event_ids,
        "decision": decision,
        "rationale": rationale,
    }


def intent_body(client_order_id: str, market_ticker: str, side: str, action: str,
                count, price_dollars: str, order_type: str,
                decision_event_id=None) -> dict:
    return {
        "client_order_id": client_order_id,
        "market_ticker": market_ticker,
        "side": side,
        "action": action,
        "count": canon_qty(count),
        "price_dollars": canon_price(price_dollars),
        "order_type": order_type,
        "decision_event_id": decision_event_id,
        "submitted_at": now(),
    }


def execution_body(kind: str, market_ticker: str, raw: dict, received_at: str,
                   client_order_id=None, order_id=None, count=None,
                   price_dollars=None, fee_dollars=None, venue_ts_ms=None,
                   side=None, action=None) -> dict:
    """
    `side` and `action` are explicit and may be None. A None is never replaced by a default:
    replay treats an execution whose side or action cannot be resolved as unresolved, and
    refuses to fold it into account state. Guessing here is how a sell becomes a buy.
    """
    return {
        "kind": kind,
        "client_order_id": client_order_id,
        "order_id": order_id,
        "market_ticker": market_ticker,
        "side": side,
        "action": action,
        "count": canon_qty(count),
        "price_dollars": canon_price(price_dollars),
        "fee_dollars": canon_money(fee_dollars),
        "venue_ts_ms": venue_ts_ms,
        "received_at": received_at,
        "raw": raw,
    }


def gap_body(channel: str, market_ticker: str, last_seq: int, received_seq: int,
             received_at=None) -> dict:
    """
    `received_at` is the receipt time of the message that revealed the gap. Carrying it puts
    the anomaly on the same clock as the observation stream, so incomplete intervals line up
    with the observations they invalidate rather than with the recorder's own write time.
    """
    return {
        "channel": channel,
        "market_ticker": market_ticker,
        "last_seq": last_seq,
        "received_seq": received_seq,
        "missing_from": last_seq + 1,
        "missing_to": received_seq - 1,
        "received_at": received_at,
    }
