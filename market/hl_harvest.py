"""
Harvest Hyperliquid fill history by wallet, from the public API, for nothing.

WHY THIS EXISTS
    Hyperliquid publishes a historical archive, but it is a Requester Pays S3 bucket -- it needs
    AWS credentials and costs money per download. `userFillsByTime` is free and pages backwards
    through the same history. It was tested before this module was written: a request for a
    24-hour window seven days ago returned 2,000 fills for an active wallet.

WHAT IT COLLECTS AND WHY THAT MATTERS
    Every fill carries `crossed` -- the venue stating whether that user took liquidity -- plus
    price, size, time, coin and direction. That is precisely what a wallet-informativeness
    method needs, and it is the one thing no centralised venue provides.

THE SAMPLING BIAS, DECLARED HERE RATHER THAN DISCOVERED LATER
    Wallets are harvested from Genesis's OWN live recording, so only wallets active during that
    window are visible. A wallet that traded heavily in June and stopped is invisible to this
    harvest. **Any result computed from this data describes currently-active wallets, not the
    population**, and must say so.

    This is the difference between the free route and the paid archive, and it is the whole of
    the difference.

RATE LIMITING, MEASURED NOT ASSUMED
    The info endpoint is a token bucket, not a per-request delay. Measured 2026-08-19: ~1.9
    requests/second sustained briefly, then HTTP 429 after roughly 70 cumulative requests,
    regardless of the spacing between them. Backoff is therefore on the budget, not on latency.

ADAPTIVE WINDOWING
    A response is capped at 2,000 fills. Requesting a narrow window for a quiet wallet wastes a
    request; requesting a wide one for a busy wallet silently truncates. So a window that comes
    back at exactly the cap is SPLIT and retried, and one that does not is accepted. That turns
    request count into a function of activity rather than of calendar time.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter

INFO = "https://api.hyperliquid.xyz/info"
OUT_DIR = os.path.expanduser("~/genesis-evidence/hl-fills")
FILLS_PATH = f"{OUT_DIR}/fills.jsonl"
STATE_PATH = f"{OUT_DIR}/harvested.json"

PAGE_CAP = 2000                     # the venue's per-response limit
DAY_MS = 86_400_000
MAX_WINDOW_MS = 7 * DAY_MS          # start wide; split on truncation
MIN_WINDOW_MS = 60 * 60 * 1000      # below an hour, accept truncation and record it
BASE_SLEEP = 0.35
MAX_BACKOFF = 60.0


def _post(body, budget):
    """One request, with backoff on 429. `budget` carries the current sleep between calls."""
    req = urllib.request.Request(INFO, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    for attempt in range(8):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.loads(r.read())
            budget["sleep"] = max(BASE_SLEEP, budget["sleep"] * 0.95)
            time.sleep(budget["sleep"])
            return out
        except urllib.error.HTTPError as e:
            if e.code == 429:
                budget["sleep"] = min(MAX_BACKOFF, max(1.0, budget["sleep"] * 2.0))
                budget["throttled"] += 1
                time.sleep(budget["sleep"])
                continue
            raise
        except Exception:
            time.sleep(min(MAX_BACKOFF, 2 ** attempt))
    return None


def wallets_from_recording(path, top=None):
    """Distinct wallets seen in a Hyperliquid recording, ordered by how often they appear."""
    seen = Counter()
    for line in open(path):
        e = json.loads(line)
        if e.get("event_class") != "OBSERVATION":
            continue
        raw = e.get("body", {}).get("world", {}).get("raw", {})
        if raw.get("channel") != "trades":
            continue
        for t in raw.get("data") or []:
            for u in (t.get("users") or []):
                seen[u] += 1
    ordered = [w for w, _ in seen.most_common()]
    return ordered[:top] if top else ordered


def fetch_window(user, start_ms, end_ms, budget, out_fh, stats):
    """
    One time window for one wallet, splitting on truncation.

    A response at exactly PAGE_CAP means the venue truncated and there is more inside the
    window. Accepting it would silently drop history, so the window is halved and retried --
    down to MIN_WINDOW_MS, below which the truncation is RECORDED rather than hidden.
    """
    body = {"type": "userFillsByTime", "user": user,
            "startTime": int(start_ms), "endTime": int(end_ms)}
    fills = _post(body, budget)
    stats["requests"] += 1
    if fills is None:
        stats["failed_windows"] += 1
        return
    if not isinstance(fills, list):
        stats["failed_windows"] += 1
        return

    if len(fills) >= PAGE_CAP and (end_ms - start_ms) > MIN_WINDOW_MS:
        mid = (start_ms + end_ms) // 2
        fetch_window(user, start_ms, mid, budget, out_fh, stats)
        fetch_window(user, mid, end_ms, budget, out_fh, stats)
        return

    truncated = len(fills) >= PAGE_CAP
    if truncated:
        stats["truncated_windows"] += 1
    for f in fills:
        out_fh.write(json.dumps({"user": user, "window_start": int(start_ms),
                                 "window_end": int(end_ms), "truncated": truncated,
                                 "fill": f}) + "\n")
    stats["fills"] += len(fills)


def harvest(recording, days_back=20, top_wallets=500, progress_every=25, start_rank=0):
    """
    Page each wallet backwards over `days_back`, appending raw fills verbatim.

    Resume-safe WITHIN a run: completed (wallet, window) pairs are recorded, so an interruption
    continues rather than re-downloading.

    ACROSS runs it is not, and `start_rank` exists because of that. Window keys are derived from
    `now`, which advances between runs, so a later run would generate shifted windows for
    already-complete wallets, miss the dedupe, and append overlapping fills. Extending the
    harvest therefore means skipping the ranks already done -- not re-running with a larger
    `top_wallets`.

    Ranking is by appearance count in the recording, so `start_rank` walks mechanically down that
    fixed order. It selects on activity, never on any wallet's results.
    """
    os.makedirs(OUT_DIR, exist_ok=True)
    done = set()
    if os.path.exists(STATE_PATH):
        done = {tuple(x) for x in json.load(open(STATE_PATH))}

    wallets = wallets_from_recording(recording, top=top_wallets)[start_rank:]
    now = int(time.time() * 1000)
    budget = {"sleep": BASE_SLEEP, "throttled": 0}
    stats = {"requests": 0, "fills": 0, "truncated_windows": 0, "failed_windows": 0,
             "wallets": 0}
    t0 = time.time()

    with open(FILLS_PATH, "a") as fh:
        for i, w in enumerate(wallets, 1):
            end = now
            while end > now - days_back * DAY_MS:
                start = max(now - days_back * DAY_MS, end - MAX_WINDOW_MS)
                key = (w, int(start))
                if key not in done:
                    fetch_window(w, start, end, budget, fh, stats)
                    done.add(key)
                end = start
            stats["wallets"] = i
            if i % progress_every == 0:
                fh.flush()
                json.dump([list(k) for k in done], open(STATE_PATH, "w"))
                el = time.time() - t0
                print(f"  {i}/{len(wallets)} wallets  {stats['fills']:,} fills  "
                      f"{stats['requests']:,} reqs  {stats['requests']/max(el,1):.2f}/s  "
                      f"throttled {budget['throttled']}  {el/60:.1f}min", flush=True)
    json.dump([list(k) for k in done], open(STATE_PATH, "w"))
    stats["elapsed_s"] = round(time.time() - t0)
    stats["throttled"] = budget["throttled"]
    stats["sampling_bias"] = ("wallets are those active in the source recording; a wallet that "
                              "traded earlier and stopped is invisible. Results describe "
                              "currently-active wallets, not the population.")
    return stats
