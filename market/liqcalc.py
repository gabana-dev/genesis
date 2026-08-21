"""
What moving margin does to a liquidation price -- and whether our arithmetic matches the venue.

WHY THIS EXISTS. Hyperliquid already shows a trader their liquidation price, so repeating it is
not a product. What it does not show is the thing the trader actually wants:

    "add $500 and your liquidation moves from 72,840 to 72,310"

That is decision support rather than a forecast, and no competitor offers it.

WHY IT IS GATED. F-0001 measured what happens when derived arithmetic is trusted without checking
it against the venue: naive free-collateral matched `withdrawable` 19% of the time and called one
wallet in five able to defend itself when it was not, ALWAYS in the safer direction. The same
mistake here would tell someone $500 saves them when it does not. So this module reproduces the
venue's OWN liquidationPx first, on real positions, and reports the error distribution. Nothing
ships to the check page until that error is small.

THE FORMULA (Hyperliquid docs):

    liq_px = entry - side * margin_available / |szi| / (1 - l * side)

    side              +1 long, -1 short
    margin_available  account value minus maintenance margin required
    l                 1 / maintenance leverage, i.e. the maintenance margin fraction

The snapshots already carry account_value, maint_margin, entryPx, szi and the venue's own
liquidationPx, so validation needs no API calls at all.
"""
import json
import os
import statistics as st
import sys

SNAP = os.path.expanduser("~/genesis-evidence/liqmap/snapshots-liq2.jsonl")


def predict(entry, szi, account_value, maint_margin, l, extra_margin=0.0):
    """Liquidation price implied by the venue's formula, optionally after adding collateral."""
    side = 1.0 if szi > 0 else -1.0
    margin_available = account_value - maint_margin + extra_margin
    denom = 1.0 - l * side
    if szi == 0 or denom == 0:
        return None
    return entry - side * margin_available / abs(szi) / denom


def latest(path=SNAP):
    last = None
    for line in open(path):
        last = line
    return json.loads(last)


def validate(snap, l):
    """Signed relative error against the venue's own liquidationPx, in basis points."""
    errs, used = [], 0
    for p in snap["positions"]:
        try:
            entry = float(p["entryPx"])
            szi = float(p["szi"])
            av = float(p["account_value"])
            mm = float(p["maint_margin"])
            venue = float(p["liquidationPx"])
        except (TypeError, ValueError, KeyError):
            continue
        if not entry or not szi or venue <= 0:
            continue
        got = predict(entry, szi, av, mm, l)
        if got is None:
            continue
        errs.append((got - venue) / venue * 1e4)
        used += 1
    return errs, used


def report(errs, used, label):
    if not errs:
        print(f"{label}: no usable positions")
        return
    a = sorted(abs(e) for e in errs)
    within = lambda bps: sum(1 for e in a if e <= bps) / len(a) * 100
    print(f"{label:<22} n={used:<5} median |err| {st.median(a):8.1f} bps   "
          f"within 10bps {within(10):5.1f}%   within 100bps {within(100):5.1f}%")


if __name__ == "__main__":
    snap = latest()
    print(f"snapshot {snap['t']}  {len(snap['positions'])} positions, spot {snap['spot']}\n")
    # BTC max leverage is 40, so maintenance leverage is 80 and l = 0.0125. The neighbours are
    # tried too: guessing this constant wrong is exactly the kind of silent error F-0001 caught,
    # and the data can say which value the venue actually used.
    for name, l in (("l=1/80 (40x max)", 1 / 80), ("l=1/100 (50x)", 1 / 100),
                    ("l=1/40  (20x)", 1 / 40), ("l=1/20  (10x)", 1 / 20)):
        errs, used = validate(snap, l)
        report(errs, used, name)
