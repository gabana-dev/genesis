"""
The alert engine: the scanner pointed at one wallet instead of the top 300.

WHY THIS EXISTS (product/ALERTS.md): the wallet check answers a question the trader already knew
to ask. The alert answers one they did not, at the moment it matters, without them at a screen.
It is the only surface anyone will pay for.

EVERY ALERT IS A TRANSITION, NEVER A LEVEL. The engine holds one small record per
chat/address/coin and emits only when it changes. That is the whole anti-spam design: price
oscillating around a threshold sends one message, not one per cycle. If the state file is lost
the worst case is a duplicate, never a miss.

Nothing here is on the predicted tier. Rule C -- the forced selling sitting between a wallet and
its own liquidation -- is deliberately NOT shipped: CASCADE-1 (F-0010) found reaching a cluster
does not move price more than a volatility-matched minute, so sending it would be selling back a
claim we refuted.

The watchlist pairs an address with a chat id. That is personal data and it never enters this
repo -- it lives in ~/genesis-private/alerts/.
"""
import html
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "market"))
from liqmap import _post          # noqa: E402  -- reuse the 429 backoff, do not reimplement it

PRIVATE = os.path.expanduser("~/genesis-private/alerts")
WATCHLIST = f"{PRIVATE}/watchlist.json"
STATE = f"{PRIVATE}/state.json"
LOG = f"{PRIVATE}/alerts.log"

# The one copy of the site URL outside the web build. web/src/lib/data.ts derives its own from
# astro.config.mjs; these two are the ONLY places a domain move has to touch.
SITE = "https://gabana-dev.github.io/genesis"

# Free tier. Not a trial -- the whole product for a trader with one account. The limit exists as
# one constant so the boundary is real from the first subscriber rather than retrofitted onto
# people who got used to unlimited.
MAX_WATCHED = 3

# Rule A. A threshold crossed is an event; a distance is a number.
BANDS = [25, 15, 10, 5, 2]
REARM = 1.25          # a band cannot fire again until distance recovers a quarter past it
STAND_DOWN = 25       # a position that was inside 10% and is now outside this gets one all-clear

# Rule B. Free collateral against margin in use.
CUSHION_TRIP = 0.05
CUSHION_REARM = 0.10
DEFEND_WATCH = 25     # only meaningful while something is actually close


# --------------------------------------------------------------------------------------
# Store. The bot writes the watchlist; the engine writes the state. No shared writer.
# --------------------------------------------------------------------------------------
def _read(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def watchlist():
    return _read(WATCHLIST, {})


def save_watchlist(w):
    _write(WATCHLIST, w)


def log(line):
    os.makedirs(PRIVATE, exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {line}\n")


# --------------------------------------------------------------------------------------
# Reading the exchange
# --------------------------------------------------------------------------------------
def positions(addr, mids, budget):
    """Open positions with a liquidation price, closest first.

    Anything past 100% is dropped. Not because it is dust -- a large short can sit thousands of
    percent away -- but because price doubling is outside every band we alert on, so carrying it
    only adds noise to "the closest position".
    """
    st = _post({"type": "clearinghouseState", "user": addr}, budget)
    if not st:
        return None, []

    out = []
    for ap in st.get("assetPositions") or []:
        p = ap.get("position") or {}
        try:
            szi = float(p.get("szi") or 0.0)
            liq = float(p.get("liquidationPx") or 0.0)
            mid = float(mids.get(p.get("coin")) or 0.0)
        except (TypeError, ValueError):
            continue
        if not (szi and liq and mid):
            continue
        dist = abs(mid - liq) / mid * 100.0
        if dist > 100.0:
            continue
        out.append({"coin": p["coin"], "side": "long" if szi > 0 else "short",
                    "liq": liq, "mid": mid, "dist": dist,
                    "notional": abs(szi) * mid})
    return st, sorted(out, key=lambda x: x["dist"])


def cushion(st):
    """Free collateral as a fraction of margin in use.

    `withdrawable` is read from the venue, never derived. F-0001 measured that the obvious
    arithmetic matches it 19% of the time and misclassifies one wallet in five as able to defend
    when it is not -- always in the direction of looking safer.
    """
    used = float((st.get("marginSummary") or {}).get("totalMarginUsed") or 0.0)
    free = float(st.get("withdrawable") or 0.0)
    return (free / used if used > 0 else None), free, used


# --------------------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------------------
def band(dist):
    """The tightest band this distance sits inside, or None if it is outside all of them."""
    inside = [b for b in BANDS if dist <= b]
    return min(inside) if inside else None


def evaluate(prev, pos, cush):
    """Return (alerts, next_state) for one address. Alerts are transitions only."""
    alerts = []
    state = dict(prev)

    if not pos:
        return alerts, {}

    closest = pos[0]
    now, was = band(closest["dist"]), prev.get("band")

    # A. Tightening. Fires only on entering a band tighter than the one already reported.
    if now is not None and (was is None or now < was):
        alerts.append(("proximity", closest))
        state["band"] = now
    # Re-arm: distance must recover a quarter past the reported band before it can fire again.
    elif was is not None and closest["dist"] > was * REARM:
        if was <= 10 and now is None and closest["dist"] > STAND_DOWN:
            alerts.append(("stand_down", closest))
        state["band"] = now

    # B. Trapped. Only meaningful while something is actually close.
    ratio = cush[0]
    trapped = prev.get("cushion") == "trapped"
    if closest["dist"] <= DEFEND_WATCH and ratio is not None:
        if not trapped and ratio < CUSHION_TRIP:
            state["cushion"] = "trapped"
            # A proximity alert in the same pass already carries the free-collateral line, so
            # sending both would be two messages about one event -- which is how an alarm loses
            # a customer.
            if not alerts:
                alerts.append(("cannot_defend", closest))
        elif trapped and ratio > CUSHION_REARM:
            state["cushion"] = "ok"
    return alerts, state


# --------------------------------------------------------------------------------------
# Copy. This is the product -- the message is the whole thing the customer ever sees.
# --------------------------------------------------------------------------------------
def money(n):
    if n >= 1e9: return f"${n/1e9:.2f}B"
    if n >= 1e6: return f"${n/1e6:.2f}M"
    if n >= 1e3: return f"${n/1e3:.1f}k"
    return f"${n:,.2f}"


def px(n):
    return f"{n:,.2f}" if n >= 1 else f"{n:,.6f}".rstrip("0")


def short(addr):
    return f"{addr[:6]}…{addr[-4:]}"


def compose(kind, p, addr, free, used):
    coin = html.escape(p["coin"])
    tail = (f'\n\n<a href="{SITE}/check.html?a={addr}">{short(addr)}</a>'
            " · read live from Hyperliquid")

    if kind == "proximity":
        defend = ("Free collateral is <b>zero</b> — there is nothing to defend with."
                  if free <= 0 else f"Free collateral: {money(free)}.")
        return (f"⚠️ <b>{coin} {p['side']} — {p['dist']:.1f}% from liquidation</b>\n\n"
                f"{coin} is at {px(p['mid'])}. This position closes itself at "
                f"<b>{px(p['liq'])}</b>.\n\n{defend}" + tail)

    if kind == "cannot_defend":
        return ("🔻 <b>Nothing left to defend with</b>\n\n"
                f"Free collateral has fallen to {money(free)} against {money(used)} of margin in "
                "use. The liquidation price can no longer be moved from inside the account.\n\n"
                f"Closest: {coin} {p['side']}, {p['dist']:.1f}% away at {px(p['liq'])}." + tail)

    if kind == "stand_down":
        return ("✅ <b>Clear</b>\n\n"
                f"{coin} {p['side']} is back to {p['dist']:.1f}% from liquidation. "
                "Nothing is close any more." + tail)

    raise ValueError(kind)


# --------------------------------------------------------------------------------------
# Engine
# --------------------------------------------------------------------------------------
def run(send=None, verbose=False):
    """One pass. `send` is injected so a dry run can print instead of messaging real people."""
    if send is None:
        import telegram
        send = telegram.send

    wl = watchlist()
    if not wl:
        return 0

    budget = {"sleep": 0.35, "throttled": 0}
    mids = _post({"type": "allMids"}, budget) or {}
    if not mids:
        log("ABORT no mids from exchange")
        return 0

    # One fetch per address, however many chats watch it.
    addrs = sorted({a for c in wl.values() for a in c.get("addresses", [])})
    reads = {a: positions(a, mids, budget) for a in addrs}

    state = _read(STATE, {})
    live, sent = set(), 0

    for chat, rec in wl.items():
        for addr in rec.get("addresses", []):
            st, pos = reads.get(addr, (None, []))
            if st is None:
                # An address we could not read is an address nobody is watching. Never silent:
                # a watch that cannot check is a failed watch.
                log(f"UNREAD {short(addr)} chat={chat}")
                continue
            key = f"{chat}:{addr}"
            live.add(key)
            cush = cushion(st)
            alerts, nxt = evaluate(state.get(key, {}), pos, cush)
            state[key] = nxt
            for kind, p in alerts:
                msg = compose(kind, p, addr, free=cush[1], used=cush[2])
                if verbose:
                    print(f"--- {chat} {addr} {kind}\n{msg}\n")
                if send(chat, msg):
                    sent += 1
                    log(f"SENT {kind} {short(addr)} chat={chat} dist={p['dist']:.2f}")
                else:
                    log(f"FAILED {kind} {short(addr)} chat={chat}")

    # Prune state for anything no longer watched, so an unsubscribe really forgets.
    _write(STATE, {k: v for k, v in state.items() if k in live})
    return sent


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    n = run(send=(lambda c, m: True) if dry else None, verbose=dry)
    print(f"{n} alert(s) {'composed (dry run)' if dry else 'sent'}")
