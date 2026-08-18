"""
CARRY-1: the declared grid from CONTRACT-carry.md, and nothing else.

This module chooses nothing. Every parameter is copied from the contract, frozen 2026-08-18
at sha256 9154377855b64c4a56b7fe420ef0ed71fed0b91becf42fa27600f42425faf66d, before any carry
figure had been computed.

THE POSITION, DERIVED RATHER THAN ASSERTED
    Short perp, long spot, equal notional N, entered at spot S_e / perp P_e and exited at
    S_x / P_x.

        long spot   P&L/N = S_x/S_e - 1
        short perp  P&L/N = 1 - P_x/P_e
        together          = S_x/S_e - P_x/P_e

    With basis b = (P - S)/S, so P = S(1 + b):

        = (S_x/S_e) * (b_e - b_x) / (1 + b_e)

    So the position profits when the basis NARROWS, which is what shorting a premium means.
    The contract writes this term as "(basis_exit - basis_entry), signed for a
    short-perp/long-spot position"; the sign that makes it correct is (entry - exit), and it
    is computed from the identity above rather than from the sign convention, so a convention
    error cannot survive.

FUNDING ACCRUAL
    Entry is decided on the rate published at settlement t and taken immediately after it, so
    the position is held ACROSS settlements t+1 .. t+H and receives those. The rate at t is
    the entry signal and is NOT collected -- collecting it would pay Genesis for a position it
    did not hold, which is the same class of error as assuming a fill.

    Positive funding means longs pay shorts. Short perp therefore RECEIVES. Only positive
    funding is tradeable here; the negative case needs a spot borrow Genesis does not have and
    is excluded by the contract, not inverted.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import costs as C  # noqa: E402
import stats as S  # noqa: E402

CONTRACT = "market/CONTRACT-carry.md"
CONTRACT_SHA256 = "9154377855b64c4a56b7fe420ef0ed71fed0b91becf42fa27600f42425faf66d"

DATA = os.path.expanduser("~/genesis-evidence/carry1")

# CONTRACT-carry.md section 6.
HOLD_DAYS = (1, 3, 7, 14)
THRESHOLDS = (0.0, 0.00005, 0.0001, 0.0002)      # >=0, >=0.5bp, >=1bp, >=2bp per interval
SETTLEMENTS_PER_DAY = 3
MIN_ROUND_TRIPS = 100                            # K1
ALPHA = 0.05
BPS = 1e-4

# Fee tiers: primary first. Spot is unchanged between them -- that is the point of Y4.
TIERS = (("futures_vip0+spot_vip0", "futures_vip0", "spot_vip0"),
         ("futures_vip9+spot_vip0", "futures_vip9", "spot_vip0"))


INTERVAL_MS = 8 * 3600 * 1000


def _snap(t_ms: int) -> int:
    """Round a settlement stamp to the 8h boundary it belongs to. See D-K1 in `load`."""
    return int(round(t_ms / INTERVAL_MS) * INTERVAL_MS)


def load():
    """Raw public payloads, unmodified. Keyed on the 8h settlement boundary."""
    funding = json.load(open(f"{DATA}/funding.json"))
    perp = json.load(open(f"{DATA}/perp_klines.json"))
    spot = json.load(open(f"{DATA}/spot_klines.json"))

    # Kline close time is 1 ms before the boundary; round to the boundary it closes on.
    def by_close(kl):
        return {int((k[6] + 1)): float(k[4]) for k in kl}

    # D-K1: funding timestamps JITTER. 4,321 of 7,604 land exactly on the 8h boundary; the
    # rest are 1-37 ms late. Exact-match keying against klines dropped 43% of settlements --
    # and worse than losing them, it broke contiguity, so `rows[i+h]` became "h SURVIVING
    # settlements later" rather than "h intervals later" and every declared holding period was
    # silently longer than declared. Snapped to the boundary the settlement belongs to.
    return (
        [(_snap(int(f["fundingTime"])), float(f["fundingRate"])) for f in funding],
        by_close(perp), by_close(spot),
    )


def align(funding, perp, spot):
    """
    Settlements for which BOTH legs have a price at that boundary.

    K5: settlements missing a leg are reported and excluded, never interpolated. A carry P&L
    computed from an invented price is a fabricated observation.
    """
    rows, missing = [], 0
    for t, rate in funding:
        # Funding stamps land on the boundary; klines close 1 ms before the next one.
        p, s = perp.get(t), spot.get(t)
        if p is None or s is None:
            missing += 1
            continue
        rows.append({"t": t, "rate": rate, "perp": p, "spot": s,
                     "basis": (p - s) / s})
    rows.sort(key=lambda r: r["t"])
    return rows, missing


def round_trips(rows, hold_days, threshold, maker_perp, fee_spot):
    """
    Every settlement meeting the threshold opens a position. Unconditional within the cell --
    no timing, no selection, overlaps permitted (section 6). Dependence from overlap is
    carried by the block bootstrap, not removed by discarding data.
    """
    h = hold_days * SETTLEMENTS_PER_DAY
    fees = 2 * fee_spot + 2 * maker_perp
    out, skipped = [], []
    for i in range(len(rows) - h):
        e = rows[i]
        if e["rate"] <= 0 or e["rate"] < threshold:
            continue
        x = rows[i + h]
        # The holding period is a claim about elapsed time, not about row count. If the
        # record has a hole, `rows[i+h]` is further away than declared and the trip is
        # dropped rather than silently reinterpreted (K5).
        if x["t"] - e["t"] != h * INTERVAL_MS:
            skipped.append(e["t"])
            continue
        # Held across settlements i+1 .. i+h; short perp receives positive funding.
        accrued = sum(rows[j]["rate"] for j in range(i + 1, i + h + 1))
        b_e, b_x = e["basis"], x["basis"]
        basis_pnl = (x["spot"] / e["spot"]) * (b_e - b_x) / (1.0 + b_e)
        out.append({
            "entry_t": e["t"], "exit_t": x["t"],
            "funding": accrued, "basis_pnl": basis_pnl, "fees": fees,
            "net": accrued + basis_pnl - fees,
            "basis_move": b_x - b_e,
        })
    return out, skipped


def _median(xs):
    """
    numpy-safe. `block_bootstrap_ci` passes the resample as an ndarray, and `if xs` on an
    ndarray raises "truth value of an array is ambiguous" -- which the bootstrap swallowed as
    a per-cell error, so every confidence interval in the first run came back n/a.
    """
    import numpy as np
    a = np.asarray(xs, dtype=float)
    return float(np.median(a)) if a.size else None


def _iqr(xs):
    if len(xs) < 4:
        return None
    ys = sorted(xs)
    n = len(ys)
    return ys[int(0.75 * n)] - ys[int(0.25 * n)]


def cell(rows, hold_days, threshold, tier_name, perp_tier, spot_tier, n_boot=2000):
    m_perp, _ = C.fees(perp_tier)
    m_spot, _ = C.fees(spot_tier)
    trips, skipped = round_trips(rows, hold_days, threshold, m_perp, m_spot)
    n = len(trips)
    enough = n >= MIN_ROUND_TRIPS

    nets = [t["net"] for t in trips]
    out = {
        "hold_days": hold_days, "threshold_bps": threshold / BPS, "tier": tier_name,
        "n_round_trips": n,
        "n_skipped_noncontiguous": len(skipped),
        "sufficient": enough,
        "excluded_reason": None if enough else f"fewer than {MIN_ROUND_TRIPS} round trips",
        "fees_bps": (2 * m_spot + 2 * m_perp) / BPS,
    }
    if not enough:
        return out

    out.update({
        "median_net_bps": _median(nets) / BPS,
        "mean_net_bps": (sum(nets) / n) / BPS,
        "worst_net_bps": min(nets) / BPS,
        "fraction_profitable": sum(1 for x in nets if x > 0) / n,
        "median_funding_bps": _median([t["funding"] for t in trips]) / BPS,
        "median_basis_pnl_bps": _median([t["basis_pnl"] for t in trips]) / BPS,
        # Y6 / K6: is the outcome decided by funding or by the basis moving?
        "iqr_basis_move_bps": (_iqr([t["basis_move"] for t in trips]) or 0) / BPS,
    })
    out["basis_dominates"] = out["iqr_basis_move_bps"] > out["median_funding_bps"]

    # Section 7.2 -- overlapping holds are dependent; block >= the holding period.
    block = hold_days * SETTLEMENTS_PER_DAY
    try:
        lo, hi = S.block_bootstrap_ci(nets, _median, n_boot=n_boot, block=block, alpha=ALPHA)
        out["median_net_ci_bps"] = [lo / BPS, hi / BPS]
        # Significance for BH: does the interval exclude zero?
        out["excludes_zero"] = (lo > 0) or (hi < 0)
    except Exception as e:
        out["median_net_ci_bps"] = None
        out["excludes_zero"] = None
        out["ci_error"] = f"{type(e).__name__}: {e}"
    return out


def run(n_boot=2000):
    funding, perp, spot = load()
    rows, missing = align(funding, perp, spot)

    report = {
        "contract": CONTRACT, "contract_sha256": CONTRACT_SHA256,
        "data": {
            "funding_settlements": len(funding),
            "aligned": len(rows), "excluded_missing_leg": missing,
            "first": rows[0]["t"], "last": rows[-1]["t"],
            "negative_funding_settlements": sum(1 for r in rows if r["rate"] < 0),
            "note": ("negative funding is reported and EXCLUDED from every result: the mirror "
                     "position needs a spot borrow Genesis does not have (contract section 5)"),
        },
        "grid": {"hold_days": list(HOLD_DAYS),
                 "thresholds_bps": [t / BPS for t in THRESHOLDS],
                 "declared_trials": len(HOLD_DAYS) * len(THRESHOLDS)},
        "cells": {},
    }

    for tier_name, perp_tier, spot_tier in TIERS:
        for h in HOLD_DAYS:
            for th in THRESHOLDS:
                key = f"{tier_name}|{h}d|>={th/BPS:g}bp"
                report["cells"][key] = cell(rows, h, th, tier_name, perp_tier, spot_tier,
                                            n_boot=n_boot)
    return report
