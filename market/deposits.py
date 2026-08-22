"""
The account-state transition recorder — deposits, withdrawals and transfers, per wallet.

WHY THIS EXISTS. F-0015 measured that a liquidation price's response to added margin cannot be
DERIVED: Hyperliquid's documented formula reproduces the venue's own `liquidationPx` for only
56.4% of cross positions, is internally inconsistent inside a single account for 71.8% of
accounts, and the observed response does not match the predicted one. So the one product feature
two independent reviews both wanted -- "add $500 and your liquidation moves to X" -- has to be
MEASURED instead.

The measurement needs three things joined:

    a real deposit          this file, from `userNonFundingLedgerUpdates`
    liquidationPx before    LIQ-2 fast snapshots, hourly
    liquidationPx after     the same

Nothing else needs to be built. The fast tier already records the position side hourly; the only
missing half is knowing when collateral actually moved and by how much.

THIS FILE RECORDS. IT DOES NOT CONCLUDE. Same discipline as product/calibration.py: recording
makes no claim and needs no pre-registration, but the moment anyone says "a dollar of margin moves
the liquidation price by X" that is a finding and needs a frozen contract with kill conditions.

POPULATION. The fast set, because that is the population whose liquidation price we hold HOURLY.
Recording deposits for wallets we only see every 12.9 hours would give a before/after window wide
enough for the position itself to have changed, which is the confound that made F-0013
unmeasurable. Better to measure 300 wallets properly than 5,395 uselessly.

COST. One request per wallet per run, and `startTime` advances to the last event seen, so a quiet
wallet returns an empty list. 300 wallets at the standard budget is under two minutes.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

import liqmap as L

STATE_DIR = L.STATE_DIR
LEDGER_PATH = f"{STATE_DIR}/ledger-events.jsonl"
CURSOR_PATH = f"{STATE_DIR}/ledger-cursor.json"

# Every non-funding ledger type Hyperliquid emits that moves collateral. Recorded exhaustively
# rather than filtered to "deposit": a withdrawal moves the liquidation price too, and it is the
# same measurement with the sign flipped. Filtering at collection time would throw away half the
# observations for a distinction the analysis can make later.
COLLATERAL_TYPES = {
    "deposit", "withdraw", "accountClassTransfer", "internalTransfer",
    "subAccountTransfer", "spotTransfer", "send", "receive", "vaultDeposit",
    "vaultWithdraw", "vaultCreate",
}

# First run only. Far enough back to pick up a useful backlog, short enough that the response is
# not enormous for an active wallet.
BACKFILL_MS = 7 * 86_400_000

# The venue caps a response at 2,000 events. VERIFIED 2026-08-22 that it returns the OLDEST 2,000
# from `startTime` and not the newest: a wallet queried from exactly 7 days ago came back spanning
# 2026-08-15T00:22 to 2026-08-19T05:06, forward from the boundary. That direction is what makes
# cursor-based paging safe -- had it returned the newest 2,000, advancing the cursor would have
# skipped everything in between and lost it silently. Re-checked here rather than trusted, because
# a full response is otherwise indistinguishable from a complete one.
PAGE_CAP = 2000
MAX_PAGES = 12


def _cursor():
    if os.path.exists(CURSOR_PATH):
        return json.load(open(CURSOR_PATH))
    return {}


def _seen_hashes():
    """Hashes already on disk, so a re-run cannot double-count an event.

    The cursor alone is not enough: it is advanced to the last event's time, and the venue
    returns events at or after `startTime`, so the boundary event comes back every run.
    """
    seen = set()
    if os.path.exists(LEDGER_PATH):
        for line in open(LEDGER_PATH):
            try:
                seen.add(json.loads(line)["hash"])
            except Exception:
                continue
    return seen


def fastset():
    if not os.path.exists(L.FASTSET_PATH):
        return []
    return json.load(open(L.FASTSET_PATH))["wallets"]


def _write(events, wallet, now, seen, fh):
    """Append the collateral-moving events not already on disk. Returns how many were new.

    The raw delta is preserved whole. Its shape differs by type -- `usdc` here, `amount` there, a
    `token` on spot transfers -- and normalising at collection time would silently drop the field
    some future question needs.
    """
    n = 0
    for e in events:
        h, t, d = e.get("hash"), e.get("time"), e.get("delta") or {}
        if not h or not t or h in seen or d.get("type") not in COLLATERAL_TYPES:
            continue
        seen.add(h)
        fh.write(json.dumps({"wallet": wallet, "t": int(t), "hash": h,
                             "type": d.get("type"), "delta": d,
                             "recorded_at": now}) + "\n")
        n += 1
    return n


def collect(wallets=None, verbose=True):
    os.makedirs(STATE_DIR, exist_ok=True)
    wallets = wallets if wallets is not None else fastset()
    if not wallets:
        return {"error": "no fast set yet; a deep scan must run first"}

    budget = {"sleep": L.BASE_SLEEP, "throttled": 0}
    cursor = _cursor()
    seen = _seen_hashes()
    now = int(time.time() * 1000)
    written = queried = 0

    with open(LEDGER_PATH, "a") as fh:
        for w in wallets:
            start = cursor.get(w, now - BACKFILL_MS)
            latest = start
            # Page forward while the venue keeps returning full responses. Waiting for the next
            # scheduled run instead would let a busy wallet fall permanently behind.
            for _page in range(MAX_PAGES):
                r = L._post({"type": "userNonFundingLedgerUpdates", "user": w,
                             "startTime": int(latest)}, budget)
                queried += 1
                if not isinstance(r, list) or not r:
                    break
                before = latest
                written += _write(r, w, now, seen, fh)
                latest = max(latest, max(int(e["time"]) for e in r if e.get("time")))
                if len(r) < PAGE_CAP or latest <= before:
                    break
            cursor[w] = latest

    json.dump(cursor, open(CURSOR_PATH, "w"))
    out = {"t": now, "wallets": len(wallets), "queried": queried,
           "events_written": written, "throttled": budget["throttled"],
           "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if verbose:
        print(json.dumps(out))
    return out


if __name__ == "__main__":
    collect()
