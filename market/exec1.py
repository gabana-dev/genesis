"""
EXEC-1: the declared grid, and the aggregations the contract asks for.

WHAT THIS IS FOR
    `fills.simulate` resolves whatever orders it is given. It does not know what orders EXEC-1
    declared, and deliberately so -- the caller chooses, and the caller must not be the
    simulator. This module is that caller, and it chooses nothing: every parameter below is
    copied from CONTRACT-execution.md §4, which was frozen on 2026-08-10 before the recording
    existed.

WHY IT IS WRITTEN BEFORE THE DATA LANDS
    The recording completes 2026-08-17. Writing the analysis afterwards means writing it under
    time pressure against a sample that only exists once, with every arbitrary choice made
    while a result is visible. A grid built after seeing the data is not a grid.

    It also means the arithmetic can be checked against synthetic series with known answers,
    which is the only place a silent error shows itself. RDB-1 lost a week to a variance-ratio
    statistic carrying a stray factor of n: on real data it looked plausible (VR 0.38, p=0.86,
    unrejected) and nothing about the number said it was wrong. A synthetic series with a known
    answer caught it in one line.

WHAT IS DELIBERATELY ABSENT
    No signal, no sizing, no selection of price or time, no P&L. Orders are placed
    unconditionally at every decision time in every cell. That is what makes the result a
    measurement of the market rather than a backtest of a strategy -- and it is why the number
    this produces describes an UNINFORMED maker, which §4 states as a declared limitation.

NOTHING HERE MAY BE TUNED AFTER SEEING A RESULT.
"""

from __future__ import annotations

from dataclasses import dataclass

import fills as F

# ── The grid, from CONTRACT-execution.md §4 ──────────────────────────────────────────────
# Copied, not chosen. Changing any value here changes what was pre-registered, which is a
# contract amendment and needs saying out loud -- not a code edit.

SIDES = ("buy", "sell")
OFFSET_TICKS = (0, 1, 5)
TICK = 0.01
SIZE_USD = 10_000.0
DECISION_EVERY_MS = 60_000.0
TTL_MS = 300_000.0
LATENCY_ARMS_MS = (291.0, 650.0)          # measured floor, measured p95
MARKOUT_MS = (1_000, 10_000, 60_000, 300_000)
BOOK_SAMPLE_MS = 500

CONTRACT = "market/CONTRACT-execution.md"
CONTRACT_SHA256 = "11c6a8ec"              # short form; full value recorded in the ledger

# X5 compares these two windows, by UTC hour. Named here so the comparison cannot quietly
# become a different one later.
QUIET_HOURS_UTC = (3, 4, 5)               # 03:00-06:00 UTC
US_SESSION_UTC = (14, 15, 16, 17, 18, 19, 20)


@dataclass(frozen=True)
class Cell:
    """One grid cell. Six per decision time, before the latency arm is applied."""
    side: str
    offset_ticks: int

    @property
    def key(self) -> str:
        return f"{self.side}@{self.offset_ticks}t"


def cells() -> list[Cell]:
    """The six cells, in a fixed order. Fixed so that output ordering is never a choice."""
    return [Cell(side, off) for side in SIDES for off in OFFSET_TICKS]


def decision_times(start_ms: float, end_ms: float, every_ms: float = DECISION_EVERY_MS) -> list[float]:
    """
    Every decision time in the window, on a fixed cadence.

    Half-open [start, end): an order decided exactly at the end of the recording could never
    resolve, and including it would put an `unresolved_at_end_of_recording` in every cell for
    no reason.
    """
    if end_ms <= start_ms:
        return []
    out, t = [], float(start_ms)
    while t < end_ms:
        out.append(t)
        t += every_ms
    return out


def build_orders(start_ms: float, end_ms: float, *, every_ms: float = DECISION_EVERY_MS,
                 ttl_ms: float = TTL_MS, size_usd: float = SIZE_USD) -> list[F.Order]:
    """
    The full declared order set for ONE latency arm.

    One arm at a time because `fills.simulate` takes latency as a single parameter for the
    pass; E5 is then the comparison of two complete passes, not a mixed population.

    order_id encodes the cell and decision time so that every row in the output can be traced
    back to the grid position that produced it, without a side table.
    """
    orders = []
    for t in decision_times(start_ms, end_ms, every_ms):
        for c in cells():
            orders.append(F.Order(
                order_id=f"{c.key}|{int(t)}",
                side=c.side,
                size_usd=size_usd,
                decided_at_ms=t,
                offset_ticks=c.offset_ticks,
                tick=TICK,
                ttl_ms=ttl_ms,
            ))
    return orders


def cell_of(order: F.Order) -> Cell:
    return Cell(order.side, order.offset_ticks)


def group_by_cell(orders) -> dict[str, list]:
    """E4 lives here: the same summary computed per distance from the touch."""
    out: dict[str, list] = {c.key: [] for c in cells()}
    for o in orders:
        out.setdefault(cell_of(o).key, []).append(o)
    return out


def group_by_offset(orders) -> dict[int, list]:
    """Both sides pooled at each distance. X3, X4 and X7 are stated in terms of distance."""
    out: dict[int, list] = {off: [] for off in OFFSET_TICKS}
    for o in orders:
        out.setdefault(o.offset_ticks, []).append(o)
    return out


def _utc_hour(ms: float) -> int:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).hour


def _utc_day(ms: float) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")


def group_by_day(orders) -> dict[str, list]:
    """
    §9: "Results are reported by day as well as pooled. Seven days is short, and a figure that
    is unstable across days is not a figure."

    Keyed on the DECISION time, not the fill time, so an order always lands in the day whose
    conditions produced it -- otherwise a fill just after midnight would be attributed to a day
    it was not decided in, and the daily figures would smear across the boundary.
    """
    out: dict[str, list] = {}
    for o in orders:
        out.setdefault(_utc_day(o.decided_at_ms), []).append(o)
    return dict(sorted(out.items()))


def group_by_session(orders) -> dict[str, list]:
    """
    X5: quiet hours (03:00-06:00 UTC) against the US session.

    Orders outside both windows go to "other" and are reported but not compared -- X5 names
    two specific windows, and silently folding the rest into one of them would answer a
    different question than the one declared.
    """
    out: dict[str, list] = {"quiet": [], "us_session": [], "other": []}
    for o in orders:
        h = _utc_hour(o.decided_at_ms)
        key = "quiet" if h in QUIET_HOURS_UTC else "us_session" if h in US_SESSION_UTC else "other"
        out[key].append(o)
    return out


def advantage_lost(orders, horizon_ms: int = 60_000, pool: str = "certain") -> float | None:
    """
    E3, the deliverable: the fraction of the 3 bps per-side maker advantage lost to adverse
    selection at `horizon_ms`.

    Positive means the advantage is being eaten. 1.0 means it is exactly consumed, which is
    the §6 kill condition -- above 1.0, resting is worse than crossing and the maker column of
    the MEASURE-1 break-even table is withdrawn.

    Reported for a stated pool because the recording has no trade stream: "certain" is the
    lower bound on fills and "certain_plus_optimistic" the upper. Quoting one without the other
    would hide the width the contract calls a first-class number.
    """
    s = F.summarise(orders, markout_ms=(horizon_ms,))
    a = s["adverse_selection"].get(pool)
    return None if a is None else a["fraction_of_advantage_lost"]


def markout_series(orders, horizon_ms: int, pool: str = "certain") -> list[float]:
    """
    Per-fill signed markouts, in FILL-TIME order, for interval estimation.

    Returned as a raw series rather than a summary statistic because the confidence interval
    must come from a moving-block bootstrap: consecutive fills are not independent, and an IID
    interval on a dependent series is too narrow -- it would make a noisy number look settled.

    The ordering is load-bearing, not cosmetic. A moving-block bootstrap resamples CONTIGUOUS
    runs precisely to carry that dependence into the resample; hand it a series in arbitrary
    order and the blocks contain unrelated observations, which reproduces the IID interval it
    was chosen to avoid -- while still looking like a block bootstrap in the code.

    Sorted on fill time rather than decision time because dependence lives in when fills
    actually happened: two orders decided a minute apart can fill seconds apart, in a single
    burst of the same move.
    """
    key = f"{horizon_ms}ms"
    if pool == "certain":
        pool_orders = [o for o in orders if o.outcome == "certain"]
    else:
        pool_orders = [o for o in orders if o.outcome in ("certain", "optimistic_only")]
    have = [o for o in pool_orders if key in o.markouts]
    have.sort(key=lambda o: (o.fill_at_ms if o.fill_at_ms is not None else o.decided_at_ms))
    return [o.markouts[key] for o in have]


def _fraction_lost(markouts) -> float:
    """
    The E3 statistic: the fraction of the maker advantage consumed by adverse selection.

    Median, matching fills.summarise. A mean markout is dominated by the tail of large adverse
    moves, and the question is what a typical fill costs, not what the worst ones do.
    """
    import numpy as np
    return float(-np.median(markouts) / F.MAKER_ADVANTAGE)


def advantage_lost_ci(orders, horizon_ms: int = 60_000, pool: str = "certain",
                      alpha: float = 0.05, n_boot: int = 2000) -> dict | None:
    """
    E3 with a moving-block bootstrap interval.

    WHY AN INTERVAL AT ALL
        §6 turns E3 into a threshold decision at 1.0, and §9 warns that "a figure that is
        unstable across days is not a figure". A point estimate of 0.95 and one of 0.95 whose
        interval spans 0.4 to 1.6 support completely different actions, and only one of them
        is honest about seven days of one instrument.

    Returns None when there are too few fills to say anything -- block_bootstrap_ci needs at
    least 8 observations and returns NaN below that. A NaN silently formatted into a report
    reads as a number; None does not.
    """
    import numpy as np
    from stats import block_bootstrap_ci

    xs = markout_series(orders, horizon_ms, pool)
    if len(xs) < 8:
        return None

    point = _fraction_lost(xs)
    lo, hi = block_bootstrap_ci(xs, _fraction_lost, n_boot=n_boot, alpha=alpha)
    if np.isnan(lo) or np.isnan(hi):
        return None

    return {
        "horizon_ms": horizon_ms,
        "pool": pool,
        "n_fills": len(xs),
        "fraction_of_advantage_lost": point,
        "ci_low": lo,
        "ci_high": hi,
        "alpha": alpha,
        # Stated so the reader can see the threshold sits inside the interval without having
        # to compare two numbers themselves. NOT a verdict on §6: the kill condition is
        # adjudicated as declared trial 3488b1e1, in the ledger, once.
        "interval_contains_kill_threshold": lo <= 1.0 <= hi,
        "block_length": max(2, int(round(len(xs) ** (1 / 3)))),
        "method": "moving-block bootstrap (Kunsch 1989; Politis & Romano 1994), median statistic",
    }


def e3_by_day(orders, horizon_ms: int = 60_000, pool: str = "certain") -> dict[str, float | None]:
    """
    §9: "Results are reported by day as well as pooled. Seven days is short, and a figure that
    is unstable across days is not a figure."

    Per-day point estimates only -- seven days rarely leaves enough fills in a single day for a
    bootstrap to mean much, and quoting a per-day interval built on 20 fills would dress up
    noise as precision. The spread ACROSS days is the stability evidence here.
    """
    return {day: (advantage_lost(os_, horizon_ms=horizon_ms, pool=pool) if os_ else None)
            for day, os_ in group_by_day(orders).items()}


def report(orders, *, markout_ms=MARKOUT_MS) -> dict:
    """
    Everything the contract asks for, in one structure, with no interpretation.

    §9 fixes the order: raw outcomes before interpretation, and the fill bracket alongside
    every fill-dependent number. This returns facts only -- no verdict on any prediction, and
    no comparison that would constitute a trial. Trials are declared in the ledger and run
    deliberately; nothing here may quietly become one by being printed.
    """
    return {
        "grid": {
            "sides": list(SIDES), "offset_ticks": list(OFFSET_TICKS),
            "size_usd": SIZE_USD, "decision_every_ms": DECISION_EVERY_MS,
            "ttl_ms": TTL_MS, "markout_ms": list(markout_ms),
            "book_sample_ms": BOOK_SAMPLE_MS, "contract": CONTRACT,
        },
        "pooled": F.summarise(orders, markout_ms=markout_ms),
        "by_cell": {k: F.summarise(v, markout_ms=markout_ms) for k, v in group_by_cell(orders).items()},
        "by_offset": {str(k): F.summarise(v, markout_ms=markout_ms) for k, v in group_by_offset(orders).items()},
        "by_day": {k: F.summarise(v, markout_ms=markout_ms) for k, v in group_by_day(orders).items()},
        "by_session": {k: F.summarise(v, markout_ms=markout_ms) for k, v in group_by_session(orders).items() if v},
    }


def run_arm(path, market, start_ms, end_ms, latency_ms, *, every_ms=BOOK_SAMPLE_MS,
            markout_ms=MARKOUT_MS):
    """
    One complete latency arm: build the declared orders, resolve them, report.

    Returns (orders, report) so the caller keeps the resolved orders for interval estimation --
    `report` intentionally returns summaries, and a summary cannot be bootstrapped.
    """
    orders = build_orders(start_ms, end_ms)
    F.simulate(path, market, orders, latency_ms=latency_ms,
               markout_ms=markout_ms, every_ms=every_ms)
    return orders, report(orders, markout_ms=markout_ms)
