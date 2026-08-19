"""
COND-1: the declared grid from CONTRACT-conditioners.md, and nothing else.

Contract frozen 2026-08-18 at sha256
b8a295dd7769e36c46a47a62aff28656727d3d859da06d402e34a3446d912e7f.

WRITTEN BEFORE THE DATA LANDS, DELIBERATELY
    q5 closes ~2026-08-25. Writing this afterwards would mean writing it under time pressure
    against a sample that exists once, with every arbitrary choice made while a result is
    visible. `exec1.py` was written the same way for the same reason, and its docstring puts
    it better than this one can: a grid built after seeing the data is not a grid.

    It also means the arithmetic can be checked against synthetic series with known answers
    before real prices are ever involved -- the only place a silent error shows itself.

WHAT COND-1 ACTUALLY MEASURES, RESTATED
    Markout at 60 s is the adverse-selection term. The horizon study since measured adverse
    selection at 0.1301 bps at ONE DAY against 1.1871 at 60 s, so for a daily strategy this
    conditions roughly 8% of the cost stack. COND-1 is still worth running -- it is frozen,
    the recording is paid for, and markout matters for any shorter-horizon work -- but it is
    NOT the cost lever, and no result here should be reported as if it were.

NOTHING HERE MAY BE TUNED AFTER SEEING A RESULT.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import ledger as L  # noqa: E402
import stats as ST  # noqa: E402

CONTRACT = "market/CONTRACT-conditioners.md"
CONTRACT_SHA256 = "b8a295dd7769e36c46a47a62aff28656727d3d859da06d402e34a3446d912e7f"

BPS = 1e-4

# Section 4. Every value copied from the contract; none chosen here.
BASIS_BUCKETS_BPS = [(0.0, 0.5), (0.5, 1.5), (1.5, 3.0), (3.0, float("inf"))]
BASIS_SIGNS = ("positive", "negative")
B_LOOKBACKS_MS = (1_000, 5_000)
B_THRESHOLDS = (0.25, 0.50)
C_DEPLETION = (0.50, 0.80)
C_BURST_MS = (200, 1_000)
C_QUIET_MS = 500                       # single value, fixed
D_SWEEP_BUCKETS_BTC = [(0.0, 0.1), (0.1, 1.0), (1.0, 5.0), (5.0, float("inf"))]
D_MAX_GAP_MS = (1, 50)

PRIMARY_HORIZON_MS = 60_000            # section 2
POOL = "certain"
MIN_FILLS = 200                        # K1
ALPHA = 0.05
DECLARED_TRIALS = 29                   # 24 conditioned + 5 reference
BONFERRONI = ALPHA / DECLARED_TRIALS

# K4
MAX_INCOMPLETE_FRACTION = 0.25
# K3
C_PRECISION_ABANDON = 0.30
# K5 -- section 7's unverified assumption
MAX_CLOCK_DISAGREEMENT_MS = 50


def cells():
    """
    The 29 declared cells, enumerated so the family cannot silently grow.

    Returned as (conditioner, key, params). `reference` cells carry params=None and are the
    unconditioned baseline plus each conditioner pooled across its own buckets.
    """
    out = [("reference", "unconditioned", None)]
    for sign in BASIS_SIGNS:
        for lo, hi in BASIS_BUCKETS_BPS:
            out.append(("A", f"basis_{sign}_{lo:g}-{hi:g}bps", {"sign": sign, "lo": lo, "hi": hi}))
    for lb in B_LOOKBACKS_MS:
        for th in B_THRESHOLDS:
            out.append(("B", f"cancel_{lb}ms_{th:g}", {"lookback_ms": lb, "threshold": th}))
    for dep in C_DEPLETION:
        for burst in C_BURST_MS:
            out.append(("C", f"cascade_{dep:g}_{burst}ms",
                        {"depletion": dep, "burst_ms": burst, "quiet_ms": C_QUIET_MS}))
    for lo, hi in D_SWEEP_BUCKETS_BTC:
        for gap in D_MAX_GAP_MS:
            out.append(("D", f"sweep_{lo:g}-{hi:g}btc_{gap}ms",
                        {"lo": lo, "hi": hi, "max_gap_ms": gap}))
    for c in ("A", "B", "C", "D"):
        out.append(("reference", f"pooled_{c}", None))
    return out


def check_family():
    """The count is fixed by the contract. If this fails, the grid drifted."""
    n = len(cells())
    if n != DECLARED_TRIALS:
        raise AssertionError(f"family drifted: {n} cells against {DECLARED_TRIALS} declared")
    return n


# ---------------------------------------------------------------------------------------
# Conditioner primitives. Each takes observations and returns a per-fill mask.
# ---------------------------------------------------------------------------------------

def basis_bps(perp_mid: float, spot_mid: float) -> float:
    """(perp - spot)/spot in bps. Section 5, conditioner A."""
    return ((perp_mid - spot_mid) / spot_mid) / BPS


def a_mask(basis_series, sign, lo, hi):
    b = np.asarray(basis_series, dtype=float)
    side = (b > 0) if sign == "positive" else (b < 0)
    mag = np.abs(b)
    return side & (mag >= lo) & (mag < hi)


def cancellation_ratio(removed_size, traded_size, visible_depth):
    """
    Conditioner B. Size that LEFT a price level without a matching trade, over visible
    same-side depth.

    Binance's diff-depth stream cannot tell a cancel from a fill on its own -- a level going to
    zero is ambiguous. With trades on the same clock it becomes decidable, and that is the
    whole reason q5 records both. `traded_size` is subtracted rather than assumed zero.
    """
    removed = np.asarray(removed_size, dtype=float)
    traded = np.asarray(traded_size, dtype=float)
    depth = np.asarray(visible_depth, dtype=float)
    cancelled = np.maximum(removed - traded, 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(depth > 0, cancelled / depth, np.nan)
    return r


def b_mask(ratio, threshold):
    r = np.asarray(ratio, dtype=float)
    return np.isfinite(r) & (r > threshold)


def cascade_fires(taker_volume, visible_depth, depletion):
    """
    Conditioner C's detector: one-sided taker volume consuming more than `depletion` of
    same-side visible depth inside the burst window.
    """
    v = np.asarray(taker_volume, dtype=float)
    d = np.asarray(visible_depth, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        frac = np.where(d > 0, v / d, np.nan)
    return np.isfinite(frac) & (frac > depletion)


def precision_against_key(fired, key_present):
    """
    C's DECLARED primary. Of the windows where the detector fired, the fraction in which the
    venue published at least one liquidation.

    Precision only, and the contract says why: `!forceOrder@arr` publishes only the largest
    liquidation per symbol per 1000 ms, so ABSENCE IS NOT EVIDENCE OF ABSENCE. The negative
    cell of a 2x2 is unreliable, recall is a lower bound, and a Fisher exact over the full
    table would be biased by an amount Genesis cannot quantify.
    """
    f = np.asarray(fired, dtype=bool)
    k = np.asarray(key_present, dtype=bool)
    if f.sum() == 0:
        return None
    return float((f & k).sum() / f.sum())


def reconstruct_sweeps(trade_ids, sides, times_ms, sizes, max_gap_ms):
    """
    Conditioner D. Consecutive trade ids, same aggressor side, within `max_gap_ms` -- one
    taker order sweeping the book.

    Aggressor side is READ from Binance's `m` flag, never inferred. This is not aggTrade:
    aggTrade merges same-price fills from one taker order, so a sweep across four levels
    appears as four records. Reconstruction from individual trades recovers the parent.
    """
    ids = np.asarray(trade_ids, dtype=np.int64)
    t = np.asarray(times_ms, dtype=float)
    sz = np.asarray(sizes, dtype=float)
    sd = np.asarray(sides)
    sweeps, start = [], 0
    for i in range(1, len(ids) + 1):
        broken = (i == len(ids)) or (ids[i] != ids[i - 1] + 1) \
            or (sd[i] != sd[i - 1]) or (t[i] - t[i - 1] > max_gap_ms)
        if broken:
            sweeps.append({"first": int(ids[start]), "last": int(ids[i - 1]),
                           "side": sd[start], "size": float(sz[start:i].sum()),
                           "t0": float(t[start]), "t1": float(t[i - 1])})
            start = i
    return sweeps


def d_mask(sweep_sizes, lo, hi):
    s = np.asarray(sweep_sizes, dtype=float)
    return (s >= lo) & (s < hi)


# ---------------------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------------------

def cell_report(markouts, name, conditioner):
    """One cell. K1 governs sufficiency; a thin cell is reported, never merged."""
    m = np.asarray([x for x in markouts if np.isfinite(x)], dtype=float)
    out = {"cell": name, "conditioner": conditioner, "n_fills": int(m.size)}
    if m.size < MIN_FILLS:
        out.update({"sufficient": False,
                    "excluded_reason": f"K1: {m.size} fills against {MIN_FILLS} required"})
        return out
    out.update({"sufficient": True,
                "median_markout_bps": float(np.median(m)) / BPS,
                "mean_markout_bps": float(m.mean()) / BPS})
    try:
        lo, hi = ST.block_bootstrap_ci(m, lambda a: float(np.median(a)),
                                       n_boot=2000, block=64, alpha=ALPHA)
        out["median_ci_bps"] = [lo / BPS, hi / BPS]
    except Exception as e:
        out["median_ci_bps"] = None
        out["ci_error"] = f"{type(e).__name__}: {e}"
    return out


def correct(p_values):
    """Section 2: BH at q=0.05, with Bonferroni reported alongside. Neither chosen after."""
    keep, crit = L.benjamini_hochberg(p_values, alpha=ALPHA)
    return {"benjamini_hochberg_survivors": keep, "bh_critical": crit,
            "bonferroni_alpha": BONFERRONI, "declared_trials": DECLARED_TRIALS}


def k4_window(incomplete_fraction):
    """
    K4. Above 25% incomplete, the analysis window is restricted to complete intervals AND the
    restriction is reported on every result -- never applied silently.
    """
    restricted = incomplete_fraction > MAX_INCOMPLETE_FRACTION
    return {"incomplete_fraction": incomplete_fraction,
            "restricted_to_complete_intervals": bool(restricted),
            "must_be_reported_on_every_result": bool(restricted)}


def k5_clock(spot_ts_ms, perp_ts_ms):
    """
    K5. Conditioner A compares two books by venue timestamp, on an assumption Genesis has
    never verified. If the engines disagree by more than 50 ms, A is VOID -- B, C and D are
    unaffected.
    """
    d = float(np.median(np.abs(np.asarray(spot_ts_ms, dtype=float)
                               - np.asarray(perp_ts_ms, dtype=float))))
    return {"median_abs_disagreement_ms": d,
            "A_void": bool(d > MAX_CLOCK_DISAGREEMENT_MS),
            "threshold_ms": MAX_CLOCK_DISAGREEMENT_MS}


# ---------------------------------------------------------------------------------------
# The driver. Written before q5 closed; see the module docstring.
# ---------------------------------------------------------------------------------------

SPOT = "binance_spot"
PERP = "binance_futures"


def auxiliary_series(path, market="BTCUSDT"):
    """
    One pass over the log collecting everything the conditioners need that is NOT the spot
    book: the perp mid (A), spot trades (B, C, D), and liquidations (C's answer key).

    WHY A SEPARATE PASS RATHER THAN ONE FUSED LOOP
        `book.stream` reconstructs ONE instrument's book. Conditioner A needs two mids on one
        clock, and rebuilding both inside a single generator would mean reimplementing the
        replay layer here. Two passes over the same file is cheaper in code and in defects, and
        the join is on venue timestamps which are exact.
    """
    from log import read
    import events as E

    perp_mid, spot_trades, liquidations = [], [], []
    perp_bid = perp_ask = None

    for ev in read(path):
        if ev.get("event_class") != E.WORLD:
            continue
        body = ev.get("body", {})
        inst = body.get("observation", {}).get("instrument")
        world = body.get("world", {})
        typ = ev.get("event_type")
        raw = world.get("raw") or {}
        vts = world.get("venue_ts_ms")

        if inst == PERP and typ == "depthUpdate":
            # Top of book only -- A needs the mid, not the depth.
            b = (raw.get("b") or [[None]])[0]
            a = (raw.get("a") or [[None]])[0]
            try:
                if b and b[0] is not None and float(b[1]) > 0:
                    perp_bid = float(b[0])
                if a and a[0] is not None and float(a[1]) > 0:
                    perp_ask = float(a[0])
            except (TypeError, ValueError, IndexError):
                pass
            if perp_bid and perp_ask and vts:
                perp_mid.append((float(vts), (perp_bid + perp_ask) / 2.0))

        elif inst == SPOT and typ == "aggTrade":
            try:
                spot_trades.append({
                    "t": float(vts), "px": float(raw["p"]), "sz": float(raw["q"]),
                    # Aggressor side is READ from Binance's `m` flag, never inferred:
                    # m=True means the buyer was the maker, so the aggressor sold.
                    "side": "S" if raw.get("m") else "B",
                    "first": int(raw["f"]), "last": int(raw["l"]),
                })
            except (KeyError, TypeError, ValueError):
                pass

        elif typ == "forceOrder":
            o = raw.get("o") or {}
            if vts:
                liquidations.append({"t": float(vts), "symbol": o.get("s"),
                                     "side": o.get("S")})

    perp_mid.sort(key=lambda x: x[0])
    spot_trades.sort(key=lambda x: x["t"])
    liquidations.sort(key=lambda x: x["t"])
    return {"perp_mid": perp_mid, "spot_trades": spot_trades,
            "liquidations": liquidations}


def _mid_at(series, t):
    """Last perp mid at or before t. Never interpolated -- an invented mid is a fabricated
    observation, and A's whole quantity is a difference of two observed mids."""
    import bisect
    ts = [x[0] for x in series]
    i = bisect.bisect_right(ts, t) - 1
    return series[i][1] if i >= 0 else None


def clock_disagreement(path, market="BTCUSDT", sample=5000):
    """
    K5. Compares the venue timestamps the two feeds attach to observations arriving in the same
    receipt window. If the engines disagree by more than 50 ms, conditioner A is VOID -- the
    basis would be a difference across two differently-timestamped books.
    """
    from log import read
    import events as E
    from datetime import datetime

    rows = []
    for ev in read(path):
        if ev.get("event_class") != E.WORLD or len(rows) >= sample:
            continue
        body = ev.get("body", {})
        obs, world = body.get("observation", {}), body.get("world", {})
        if world.get("venue_ts_ms") and obs.get("received_at") and obs.get("instrument"):
            try:
                r = datetime.fromisoformat(obs["received_at"]).timestamp() * 1000.0
            except ValueError:
                continue
            rows.append((obs["instrument"], float(world["venue_ts_ms"]), r))
    lag = {SPOT: [], PERP: []}
    for inst, v, r in rows:
        if inst in lag:
            lag[inst].append(r - v)
    import statistics as st
    if not lag[SPOT] or not lag[PERP]:
        return {"evaluable": False, "reason": "one instrument absent from the sample",
                "A_void": None}
    d = abs(st.median(lag[SPOT]) - st.median(lag[PERP]))
    return {"evaluable": True, "median_abs_disagreement_ms": d,
            "spot_median_lag_ms": st.median(lag[SPOT]),
            "perp_median_lag_ms": st.median(lag[PERP]),
            "A_void": bool(d > MAX_CLOCK_DISAGREEMENT_MS),
            "threshold_ms": MAX_CLOCK_DISAGREEMENT_MS}


def book_series(path, market="BTCUSDT", instrument=SPOT, every_ms=500):
    """
    Touch price and depth over time for one instrument. B and C both need depth at the fill,
    and `fills.simulate` holds the book internally without exposing it, so it is sampled here.

    Uses the D-6 instrument filter. Without it this would silently return the PERP book, since
    q5 records both venues under the ticker BTCUSDT and a snapshot replaces rather than merges.
    """
    import book as bk
    out = []
    for t_iso, b in bk.stream(path, market, every_ms=every_ms, instrument=instrument):
        if not b.ready():
            continue
        out.append((bk._ms(t_iso), b.best_bid, b.best_ask,
                    b.size_at("bids", b.best_bid), b.size_at("asks", b.best_ask)))
    return out


def _window(series, t, back_ms, idx=0):
    """Rows of `series` in (t - back_ms, t]. `series` must be sorted on its first element."""
    import bisect
    ts = [r[idx] for r in series]
    hi = bisect.bisect_right(ts, t)
    lo = bisect.bisect_left(ts, t - back_ms)
    return series[lo:hi]


def conditioner_values(fills, aux, books):
    """
    Per fill, every quantity the four conditioners need. Computed once; the cells then mask.

    A fill with any input missing gets NaN for that conditioner and is EXCLUDED from its cells
    rather than defaulted -- a defaulted conditioner value is a fabricated observation.
    """
    tr = aux["spot_trades"]
    tr_t = [x["t"] for x in tr]
    rows = []
    for f in fills:
        t = f["t"]
        pm = _mid_at(aux["perp_mid"], t)
        sm = f["mid"]
        basis = basis_bps(pm, sm) if (pm and sm) else float("nan")

        b_at = _window(books, t, 1, idx=0)
        depth = b_at[-1][3] if b_at else float("nan")     # bid-side depth at the touch

        row = {"t": t, "markout": f["markout"], "basis_bps": basis}

        for lb in B_LOOKBACKS_MS:
            w = _window(books, t, lb, idx=0)
            removed = sum(max(w[i - 1][3] - w[i][3], 0.0) for i in range(1, len(w)))
            traded = sum(x["sz"] for x in
                         tr[_bisect_lo(tr_t, t - lb):_bisect_hi(tr_t, t)])
            row[f"cancel_{lb}"] = float(cancellation_ratio([removed], [traded], [depth])[0])

        for burst in C_BURST_MS:
            vol = sum(x["sz"] for x in tr[_bisect_lo(tr_t, t - burst):_bisect_hi(tr_t, t)])
            row[f"taker_{burst}"] = vol
            row[f"depth_{burst}"] = depth
            # The QUIET after the burst: no trades in the declared interval before the fill.
            recent = tr[_bisect_lo(tr_t, t - C_QUIET_MS):_bisect_hi(tr_t, t)]
            row[f"quiet_{burst}"] = len(recent) == 0
            # C's answer key: did the venue publish a liquidation inside the burst window?
            lq = aux["liquidations"]
            lqt = [x["t"] for x in lq]
            row[f"key_{burst}"] = _bisect_hi(lqt, t) > _bisect_lo(lqt, t - burst)

        for gap in D_MAX_GAP_MS:
            w = tr[_bisect_lo(tr_t, t - 60_000):_bisect_hi(tr_t, t)]
            if w:
                sw = reconstruct_sweeps([x["first"] for x in w], [x["side"] for x in w],
                                        [x["t"] for x in w], [x["sz"] for x in w], gap)
                row[f"sweep_{gap}"] = sw[-1]["size"] if sw else float("nan")
            else:
                row[f"sweep_{gap}"] = float("nan")
        rows.append(row)
    return rows


def _bisect_lo(ts, v):
    import bisect
    return bisect.bisect_left(ts, v)


def _bisect_hi(ts, v):
    import bisect
    return bisect.bisect_right(ts, v)


def run(path, market="BTCUSDT", n_boot=2000):
    """
    COND-1 end to end. Four passes over q5: the clock check, the auxiliary series, the spot
    book, and the fill simulation. Nothing here chooses a parameter.
    """
    import exec1 as X
    import fills as F
    import numpy as np

    check_family()
    report = {"contract": CONTRACT, "contract_sha256": CONTRACT_SHA256,
              "declared_trials": DECLARED_TRIALS, "bonferroni_alpha": BONFERRONI,
              "primary": {"endpoint": "median markout, bps", "horizon_ms": PRIMARY_HORIZON_MS,
                          "pool": POOL}}

    # K5 first: if the engines disagree, A is void and must not be computed at all.
    k5 = clock_disagreement(path, market)
    report["K5_clock"] = k5
    a_void = bool(k5.get("A_void"))

    aux = auxiliary_series(path, market)
    books = book_series(path, market, instrument=SPOT)
    report["inputs"] = {"perp_mid_points": len(aux["perp_mid"]),
                        "spot_trades": len(aux["spot_trades"]),
                        "liquidations": len(aux["liquidations"]),
                        "book_frames": len(books)}
    if not books:
        report["unevaluable"] = "no spot book frames -- check the instrument label"
        return report

    start, end = books[0][0], books[-1][0]
    orders = X.build_orders(start, end)
    F.simulate(path, market, orders, latency_ms=291.0,
               markout_ms=(PRIMARY_HORIZON_MS,), every_ms=X.BOOK_SAMPLE_MS,
               instrument=SPOT)
    key = f"{PRIMARY_HORIZON_MS}ms"
    fills = [{"t": o.fill_at_ms, "mid": o.mid_before_fill, "markout": o.markouts[key]}
             for o in orders
             if o.outcome == "certain" and key in o.markouts and o.fill_at_ms]
    report["n_certain_fills"] = len(fills)
    if not fills:
        report["unevaluable"] = "no certain fills with a 60s markout"
        return report

    rows = conditioner_values(fills, aux, books)
    mk = np.array([r["markout"] for r in rows], dtype=float)

    def emit(name, cond, mask):
        sel = mk[mask] if mask is not None else mk
        report["cells"][name] = cell_report(sel, name, cond)

    report["cells"] = {}
    emit("unconditioned", "reference", None)

    basis = np.array([r["basis_bps"] for r in rows], dtype=float)
    if a_void:
        for sign in BASIS_SIGNS:
            for lo, hi in BASIS_BUCKETS_BPS:
                report["cells"][f"basis_{sign}_{lo:g}-{hi:g}bps"] = {
                    "cell": f"basis_{sign}_{lo:g}-{hi:g}bps", "conditioner": "A",
                    "sufficient": False,
                    "excluded_reason": "K5: spot and perp clocks disagree; A is VOID"}
        report["cells"]["pooled_A"] = {"cell": "pooled_A", "conditioner": "A",
                                       "sufficient": False, "excluded_reason": "K5: A is VOID"}
    else:
        for sign in BASIS_SIGNS:
            for lo, hi in BASIS_BUCKETS_BPS:
                emit(f"basis_{sign}_{lo:g}-{hi:g}bps", "A", a_mask(basis, sign, lo, hi))
        emit("pooled_A", "reference", np.isfinite(basis))

    for lb in B_LOOKBACKS_MS:
        r = np.array([x[f"cancel_{lb}"] for x in rows], dtype=float)
        for th in B_THRESHOLDS:
            emit(f"cancel_{lb}ms_{th:g}", "B", b_mask(r, th))
    emit("pooled_B", "reference",
         np.isfinite(np.array([x[f"cancel_{B_LOOKBACKS_MS[0]}"] for x in rows], dtype=float)))

    c_precision = {}
    for dep in C_DEPLETION:
        for burst in C_BURST_MS:
            vol = np.array([x[f"taker_{burst}"] for x in rows], dtype=float)
            dep_arr = np.array([x[f"depth_{burst}"] for x in rows], dtype=float)
            fired = cascade_fires(vol, dep_arr, dep)
            quiet = np.array([x[f"quiet_{burst}"] for x in rows], dtype=bool)
            keyp = np.array([x[f"key_{burst}"] for x in rows], dtype=bool)
            c_precision[f"{dep:g}_{burst}ms"] = precision_against_key(fired, keyp)
            emit(f"cascade_{dep:g}_{burst}ms", "C", fired & quiet)
    report["C_precision_against_key"] = c_precision
    # K3: precision below 0.30 abandons the detector rather than tuning it.
    vals = [v for v in c_precision.values() if v is not None]
    report["K3_detector"] = {
        "evaluable": bool(vals),
        "best_precision": max(vals) if vals else None,
        "abandon": bool(vals and max(vals) < C_PRECISION_ABANDON),
        "threshold": C_PRECISION_ABANDON,
    }
    emit("pooled_C", "reference", None)

    for gap in D_MAX_GAP_MS:
        sw = np.array([x[f"sweep_{gap}"] for x in rows], dtype=float)
        for lo, hi in D_SWEEP_BUCKETS_BTC:
            emit(f"sweep_{lo:g}-{hi:g}btc_{gap}ms", "D", d_mask(sw, lo, hi))
    emit("pooled_D", "reference",
         np.isfinite(np.array([x[f"sweep_{D_MAX_GAP_MS[0]}"] for x in rows], dtype=float)))

    report["n_cells_reported"] = len(report["cells"])
    return report
