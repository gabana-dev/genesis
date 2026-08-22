"""
The standing book, archived. Q3 in research/QUEUE.md.

WHY. F-0014 measured that a liquidation cluster's size means nothing until it is divided by the
liquidity standing in front of it -- the median published cluster is 0.44% of the book. The site
now shows that ratio live. What nobody has, including us, is the ratio THROUGH TIME: whether
forced exposure as a share of the book is a market-level quantity that varies, and if so whether
it varies with anything. F-0016 searched nine public variables and found nothing; this is the
first candidate that is actually ours.

WHY A SEPARATE FILE rather than a field on the LIQ-2 snapshot. LIQ-2's schema is frozen by
contract. Adding a key would be additive and probably harmless, and "probably harmless" is exactly
the reasoning a freeze exists to refuse. This appends to its own archive and the analysis joins on
time, which costs one line of code and keeps the contract absolute.

It also samples on its own cadence. The book moves in seconds; the deep position scan runs every
12.9 hours. Tying them together would throw away the resolution of the cheaper measurement.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

import liqmap as L

PATH = f"{L.STATE_DIR}/book-btc.jsonl"
BANDS = (0.2, 1.0, 2.0)


def collect(coin=None, verbose=True):
    os.makedirs(L.STATE_DIR, exist_ok=True)
    budget = {"sleep": L.BASE_SLEEP, "throttled": 0}
    coin = coin or L.COIN
    row = {"t": int(time.time() * 1000), "coin": coin,
           "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    for band in BANDS:
        got = L.standing_book(budget, coin=coin, band_pct=band)
        if got is None:
            return {"error": "no book"}
        notional, mid, reach = got
        row[f"notional_{band}pct"] = round(notional, 2)
        row["mid"] = mid
        # Recorded every time rather than assumed. The 20-level cap means reach depends on the
        # venue's aggregation, and a band wider than the reach would be silently truncated --
        # the analysis needs to know that from the row, not from a comment in this file.
        row["reach_pct"] = round(reach, 3)
    with open(PATH, "a") as f:
        f.write(json.dumps(row) + "\n")
    if verbose:
        print(json.dumps(row))
    return row


if __name__ == "__main__":
    collect()
