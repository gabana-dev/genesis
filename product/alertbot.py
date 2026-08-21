"""
The subscription bot. Long-polls Telegram, owns the watchlist file.

The engine (alerts.py) owns the state file. Neither writes the other's -- that is why there is no
lock anywhere in this system.

Subscribing is the customer's deliberate act: they type /watch. The public wallet check stores
nothing at all, so this is the single point where an address becomes data we hold, and it never
enters the public repo.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import alerts
import telegram

ADDR = re.compile(r"^0x[0-9a-f]{40}$")
OFFSET = f"{alerts.PRIVATE}/offset.json"

HELP = (
    "I watch Hyperliquid positions and message you when one gets close to liquidation — "
    "and, the part most tools get wrong, when there is nothing left to defend it with.\n\n"
    "<b>/watch 0x…</b> — start watching an address\n"
    "<b>/unwatch 0x…</b> — stop\n"
    "<b>/list</b> — what I am watching for you\n"
    "<b>/stop</b> — forget me entirely\n\n"
    f"Up to {alerts.MAX_WATCHED} addresses. I check every few minutes and only message you when "
    "something changes — never a running commentary."
)


def status_line(addr, mids, budget):
    """What the address looks like right now. Sent on /watch so the first message proves the
    alarm can actually see the position, rather than promising it silently."""
    st, pos = alerts.positions(addr, mids, budget)
    if st is None:
        return "I could not reach the exchange for that address just now. I will keep watching."
    if not pos:
        return "No open positions with a liquidation price right now. I will tell you when there are."
    p = pos[0]
    _, free, used = alerts.cushion(st)
    defend = ("<b>nothing to defend with</b>" if free <= 0
              else f"{alerts.money(free)} free collateral")
    return (f"Closest: {p['coin']} {p['side']}, <b>{p['dist']:.1f}%</b> from liquidation "
            f"at {alerts.px(p['liq'])} — {defend}.")


def handle(text, chat, wl, mids, budget):
    """Returns (reply, changed)."""
    cmd, _, arg = text.strip().partition(" ")
    cmd, arg = cmd.lower().lstrip("/").split("@")[0], arg.strip().lower()
    rec = wl.setdefault(str(chat), {"addresses": []})

    if cmd in ("start", "help"):
        return HELP, False

    if cmd == "watch":
        if not ADDR.match(arg):
            return ("That does not look like a Hyperliquid address. It should be <code>0x</code> "
                    "followed by 40 hex characters.", False)
        if arg in rec["addresses"]:
            return "Already watching that one.", False
        if len(rec["addresses"]) >= alerts.MAX_WATCHED:
            return (f"That is {alerts.MAX_WATCHED} addresses, which is the limit for now. "
                    "Use /unwatch to make room.", False)
        rec["addresses"].append(arg)
        return f"Watching <code>{arg}</code>.\n\n{status_line(arg, mids, budget)}", True

    if cmd == "unwatch":
        if arg in rec["addresses"]:
            rec["addresses"].remove(arg)
            return "Stopped watching that address.", True
        return "I was not watching that one.", False

    if cmd == "list":
        if not rec["addresses"]:
            return "Nothing yet. Send <b>/watch 0x…</b> to start.", False
        return "\n".join(f"<code>{a}</code>" for a in rec["addresses"]), False

    if cmd == "stop":
        wl.pop(str(chat), None)
        return "Forgotten — every address and everything I knew about them.", True

    return HELP, False


def main():
    off = alerts._read(OFFSET, {}).get("offset", 0)
    budget = {"sleep": 0.35, "throttled": 0}
    print("alertbot: polling")
    while True:
        msgs, off = telegram.updates(off)
        alerts._write(OFFSET, {"offset": off})
        if not msgs:
            continue
        mids = alerts._post({"type": "allMids"}, budget) or {}
        wl = alerts.watchlist()
        changed = False
        for m in msgs:
            text, chat = m.get("text"), m["chat"]["id"]
            if not text:
                continue
            reply, ch = handle(text, chat, wl, mids, budget)
            changed |= ch
            telegram.send(chat, reply)
            alerts.log(f"BOT chat={chat} {text.split()[0][:16]}")
        if changed:
            alerts.save_watchlist(wl)


if __name__ == "__main__":
    try:
        main()
    except telegram.NoToken as e:
        sys.exit(f"alertbot: {e}")
    except KeyboardInterrupt:
        pass
