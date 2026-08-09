"""
Deterministic projections. Pure functions of the event log and nothing else.

Every projection carries its own completeness flag. A book reconstructed across a recorded
gap is returned as incomplete with the reason attached, rather than as a plausible-looking
book. Silence about incompleteness is the failure mode this module exists to prevent.
"""

from collections import defaultdict
from decimal import Decimal

import events as E
from log import read

SNAPSHOT = "orderbook_snapshot"
DELTA = "orderbook_delta"


def _ts(ev):
    """Ordering key: Genesis receipt time. Venue time is preserved but never reorders the log."""
    b = ev.get("body", {})
    if ev["event_class"] == E.WORLD:
        return b.get("observation", {}).get("received_at") or ev["recorded_at"]
    return b.get("received_at") or b.get("submitted_at") or ev["recorded_at"]


def order_book_at(path, market_ticker, at=None):
    """
    Rebuild the book for one market as of `at` (Genesis receipt time, ISO string).

    Returns {"book": {"yes": {price: size}, "no": {...}}, "complete": bool,
             "reason": str|None, "last_seq": int|None, "events_applied": int}

    Completeness is lost at a SEQUENCE_GAP or CONNECTION_OPENED and regained only at the next
    authoritative snapshot for that market.
    """
    # Sizes are Decimal, never int and never float. Kalshi's public order book carries
    # fractional decimal-string quantities ("0.01", "191.00") under a tapered_deci_cent price
    # structure, so integer coercion both crashes and would lose sub-unit size.
    book = {"yes": defaultdict(lambda: Decimal("0")), "no": defaultdict(lambda: Decimal("0"))}
    complete, reason, last_seq, applied = False, "no snapshot seen", None, 0
    current_run = None

    for ev in read(path):
        # Iterate in log order and FILTER, never break. Receipt clocks can step backwards
        # (NTP), so the first event past the boundary does not imply the rest are.
        t = _ts(ev)
        if at is not None and t > at:
            continue

        cls, typ, body = ev["event_class"], ev["event_type"], ev.get("body", {})

        # A change of recorder_run means the recorder was not running for some interval.
        # Whether or not the venue's sequence numbers reveal it, that is a real hole, and
        # completeness is not restored until the next authoritative snapshot.
        if current_run is not None and ev.get("recorder_run") != current_run:
            complete = False
            reason = "recorder run changed: observation was interrupted"
        current_run = ev.get("recorder_run")

        if cls == E.RECORDER:
            if typ == "SEQUENCE_GAP" and body.get("market_ticker") in (market_ticker, None):
                complete = False
                reason = (f"sequence gap {body.get('missing_from')}-{body.get('missing_to')}"
                          f" before a new snapshot")
            elif (typ == "UNINTERPRETABLE_FIELD"
                  and body.get("market_ticker") in (market_ticker, None)):
                complete = False
                reason = ("uninterpretable field(s): "
                          + ", ".join(f.get("field", "?") for f in body.get("fields") or []))
            elif (typ == "DUPLICATE_MESSAGE" and body.get("conflict")
                  and body.get("market_ticker") in (market_ticker, None)):
                # Two different payloads claimed the same sequence number. Which one the
                # venue meant is unknowable from the record, so the book is not trustworthy.
                complete = False
                reason = (f"conflicting duplicate at seq {body.get('seq')}: "
                          f"two different payloads share one sequence number")
            elif typ in ("CONNECTION_OPENED", "RECORDER_STARTED"):
                complete = False
                reason = f"{typ}: sequence continuity not established"
            continue

        if cls != E.WORLD:
            continue

        world = body.get("world", {})
        if world.get("market_ticker") != market_ticker:
            continue

        msg = (world.get("raw") or {}).get("msg") or {}
        # Prices are read from the canonical view computed at ingestion. Older events without
        # one are canonicalised here so a mixed-vintage log still resolves to single keys.
        canon = world.get("canonical") or E.canonical_view(typ, msg)

        bad_fields = canon.get("invalid")

        if typ == SNAPSHOT:
            book = {"yes": defaultdict(lambda: Decimal("0")),
                    "no": defaultdict(lambda: Decimal("0"))}
            for side in ("yes", "no"):
                for price, size in canon.get(side) or []:
                    book[side][price] = E.to_decimal(size)
            if bad_fields:
                # Some levels could not be interpreted, so this snapshot does not
                # re-establish a known-complete book.
                complete = False
                reason = (f"uninterpretable field(s) in snapshot: "
                          f"{', '.join(f['field'] for f in bad_fields)}")
            else:
                complete, reason = True, None
            last_seq = world.get("venue_seq")
            applied += 1

        elif typ == DELTA:
            side = canon.get("side")
            price = canon.get("price_dollars")
            delta = E.to_decimal(canon.get("delta_fp"))
            if bad_fields:
                # The delta cannot be applied and must not be silently skipped: the book
                # from here on is missing a change the venue actually made.
                complete = False
                reason = (f"uninterpretable field(s) in delta: "
                          f"{', '.join(f['field'] for f in bad_fields)}")
                last_seq = world.get("venue_seq")
            elif side in book and price is not None:
                book[side][price] = book[side].get(price, Decimal("0")) + delta
                # Exactly zero (or negative) removes the level. Decimal makes "exactly" mean
                # exactly: a 0.001 residue survives where float arithmetic might not.
                if book[side][price] <= 0:
                    book[side].pop(price, None)
                last_seq = world.get("venue_seq")
                applied += 1

    return {"book": {s: {p: E.canon_size(q) for p, q in v.items()} for s, v in book.items()},
            "complete": complete, "reason": reason,
            "last_seq": last_seq, "events_applied": applied}


def account_state_at(path, at=None):
    """
    Fold INTENT and EXECUTION into cash, position, fees, realised P&L and open orders.

    Derived ONLY from what the venue reported happening. Intents create open orders; they
    never create positions. Nothing here infers a fill.
    """
    cash = Decimal("0")
    fees = Decimal("0")
    realised = Decimal("0")
    positions = defaultdict(lambda: Decimal("0"))
    cost_basis = defaultdict(lambda: Decimal("0"))
    open_orders = {}
    fills = []
    settlements = []
    unresolved = []
    reasons = []

    for ev in read(path):
        if at is not None and _ts(ev) > at:
            continue
        cls, body = ev["event_class"], ev.get("body", {})

        if cls == E.INTENT:
            open_orders[body["client_order_id"]] = {
                "market_ticker": body["market_ticker"], "side": body["side"],
                "action": body["action"], "count": body["count"],
                "price_dollars": body["price_dollars"], "filled": "0",
                "intent_event_id": ev["event_id"],
            }

        elif cls == E.EXECUTION:
            kind = body.get("kind")
            coid = body.get("client_order_id")
            order = open_orders.get(coid)

            # Side and action come from the execution, else from a matching intent. They are
            # never defaulted: a fill whose direction cannot be established is recorded as
            # unresolved rather than guessed into a buy.
            side = body.get("side") or (order or {}).get("side")
            action = body.get("action") or (order or {}).get("action")
            key = (body.get("market_ticker") or (order or {}).get("market_ticker"), side)

            if kind in ("fill", "partial_fill") and (side is None or action is None):
                unresolved.append({"event_id": ev["event_id"], "kind": kind,
                                   "client_order_id": coid,
                                   "missing": [f for f, v in (("side", side),
                                                              ("action", action)) if v is None]})
                reasons.append(f"unresolved {kind}: no side/action for "
                               f"client_order_id={coid!r}; not applied")
                continue

            if kind == "settlement" and side is None:
                unresolved.append({"event_id": ev["event_id"], "kind": kind,
                                   "missing": ["side"]})
                reasons.append("unresolved settlement: no side recorded; not applied")
                continue

            if kind in ("fill", "partial_fill"):
                count = E.to_decimal(body.get("count"))
                price = E.to_decimal(body.get("price_dollars"))
                fee = E.to_decimal(body.get("fee_dollars"))
                if action == "buy":
                    cash -= price * count
                    positions[key] += count
                    cost_basis[key] += price * count
                else:
                    cash += price * count
                    held = positions[key]
                    if held > 0:
                        avg = cost_basis[key] / held
                        realised += (price - avg) * min(count, held)
                        cost_basis[key] -= avg * min(count, held)
                    positions[key] -= count
                cash -= fee
                fees += fee
                fills.append({"event_id": ev["event_id"], "client_order_id": coid,
                              "count": E.canon_qty(count),
                              "price_dollars": E.canon_price(price),
                              "fee_dollars": E.canon_money(fee), "market_ticker": key[0]})
                if order:
                    filled = E.to_decimal(order["filled"]) + count
                    order["filled"] = E.canon_qty(filled)
                    if filled >= E.to_decimal(order["count"]) or kind == "fill":
                        open_orders.pop(coid, None)

            elif kind in ("cancel", "reject"):
                open_orders.pop(coid, None)

            elif kind == "settlement":
                payout = E.to_decimal(body.get("price_dollars"))
                count = E.to_decimal(body.get("count"))
                fee = E.to_decimal(body.get("fee_dollars"))
                cash += payout * count
                cash -= fee
                fees += fee
                held = positions.get(key, Decimal("0"))
                realised += payout * count - cost_basis.get(key, Decimal("0"))
                cost_basis[key] = Decimal("0")
                positions[key] = held - count if held >= count else Decimal("0")
                settlements.append({"event_id": ev["event_id"], "market_ticker": key[0],
                                    "payout_dollars": E.canon_price(payout),
                                    "count": E.canon_qty(count),
                                    "observed": True, "independently_verified": False})

    return {
        "cash_dollars": E.canon_money(cash),
        "fees_dollars": E.canon_money(fees),
        "realised_pnl_dollars": E.canon_money(realised),
        "positions": {f"{m}|{s}": E.canon_qty(c) for (m, s), c in positions.items() if c},
        "reserved_collateral_dollars": E.canon_money(_reserved(open_orders)),
        "open_orders": open_orders,
        "fills": fills,
        "settlements": settlements,
        "unresolved": unresolved,
        "reasons": reasons,
        "complete": not unresolved,
    }


def _reserved(open_orders):
    """Binary contracts are fully collateralised: a resting buy reserves price x count."""
    total = Decimal("0")
    for o in open_orders.values():
        if o["action"] == "buy":
            remaining = E.to_decimal(o["count"]) - E.to_decimal(o["filled"])
            total += E.to_decimal(o["price_dollars"]) * remaining
    return total
