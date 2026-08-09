"""
RDB-1 development runner. Development period ONLY (2015-01..2022-12).

The holdout is not downloaded, not readable, and not referenced here. It becomes
available only after the design is frozen (see config.FREEZE_MARKER).

Usage:
  .venv/bin/python rdb/run.py baselines      # baselines only, no model
  .venv/bin/python rdb/run.py timing         # measure state-space cost before committing
  .venv/bin/python rdb/run.py model          # baselines + state-space, expanding vs rolling
  .venv/bin/python rdb/run.py rolling_only   # one arm, reusing the saved baseline records
  .venv/bin/python rdb/run.py expanding_only # the other arm; reports the adaptation test
"""

import sys
import time

import pandas as pd

import baselines as bl
import harness as H
import series

# Development evaluation window. Training may reach back to 2015; origins are evaluated
# over this span, which brackets the Oct-2021 native-resolution change on both sides.
EVAL_FIRST_ORIGIN = "2021-01-01 00:00:00"
EVAL_LAST_ORIGIN = "2022-12-30 00:00:00"


def load():
    s = series.build("dev")
    print(f"canonical series: {len(s)} obs  {s.index[0]} -> {s.index[-1]}")
    return s


def make_origins(s):
    o = H.origins(s.index, EVAL_FIRST_ORIGIN, EVAL_LAST_ORIGIN)
    print(f"origins: {len(o)}  ({o[0]} -> {o[-1]})")
    return o


def save(results, name):
    """Per-origin records persisted so comparisons are reproducible artifacts."""
    from config import DATA
    out = DATA / "results"
    out.mkdir(parents=True, exist_ok=True)
    results.to_csv(out / f"{name}.csv")
    return out / f"{name}.csv"


def load_saved(*names):
    """Read back persisted per-origin records so a single arm can be re-run alone."""
    from config import DATA
    out = {}
    for name in names:
        p = DATA / "results" / f"{name}.csv"
        if p.exists():
            out[name] = pd.read_csv(p, index_col="origin", parse_dates=["origin"])
    return out


def paired(a, b, col="mae"):
    """Paired per-origin difference (a - b) with a 95% CI. Negative favours a."""
    import numpy as np
    d = (a[col] - b[col]).to_numpy(dtype=float)
    m = d.mean()
    half = 1.96 * d.std(ddof=1) / np.sqrt(len(d))
    return {"mean_diff": m, "ci_low": m - half, "ci_high": m + half,
            "a_better_share": float((d < 0).mean()), "n": len(d)}


def run_baselines(s, origin_list):
    results = {}
    results["persistence"] = H.evaluate(
        s, lambda h, fi: bl.persistence(h.to_numpy(), len(fi)), origin_list)
    results["seasonal_naive"] = H.evaluate(
        s, lambda h, fi: bl.seasonal_naive(h.to_numpy(), len(fi)), origin_list)
    results["calendar_ols"] = H.evaluate(
        s, lambda h, fi: bl.calendar_ols(h.iloc[-52 * 336:], fi), origin_list)
    ref = results["seasonal_naive"]
    for name, r in results.items():
        save(r, name)
        print(f"  {name:16s} {H.summarise(r, ref)}")
    return results


def run_timing(s, origin_list):
    """Measure the imported model's cost before committing to a full evaluation."""
    from model import StateSpaceForecaster
    for mode in ("rolling", "expanding"):
        f = StateSpaceForecaster(mode=mode)
        o = origin_list[0]
        t0 = time.time()
        f(s.loc[:o], H.actuals(s, o).index)
        first = time.time() - t0
        o2 = origin_list[1]
        t0 = time.time()
        f(s.loc[:o2], H.actuals(s, o2).index)
        second = time.time() - t0
        n = len(f._slice(s.loc[:o]))
        print(f"  {mode:10s} train_obs={n:7d}  first(fit+filter)={first:6.1f}s  "
              f"subsequent(filter only)={second:6.1f}s  "
              f"projected_full_run={(second * len(origin_list)) / 60:7.1f} min")


def run_model(s, origin_list):
    from model import StateSpaceForecaster
    out = {}
    for mode in ("expanding", "rolling"):
        f = StateSpaceForecaster(mode=mode)
        t0 = time.time()
        out[mode] = H.evaluate(s, f, origin_list)
        print(f"  state_space[{mode}] fits={f.fits} elapsed={(time.time()-t0)/60:.1f}min")
    return out


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "baselines"
    s = load()
    o = make_origins(s)
    if what == "baselines":
        run_baselines(s, o)
    elif what == "timing":
        run_timing(s, o)
    elif what == "model":
        base = run_baselines(s, o)
        mod = run_model(s, o)
        ref = base["seasonal_naive"]
        for mode, r in mod.items():
            save(r, f"state_space_{mode}")
            print(f"  state_space[{mode}] {H.summarise(r, ref)}")
            print(H.by_year(r))
            print(H.by_season(r))
    elif what in ("rolling_only", "expanding_only"):
        mode = what.removesuffix("_only")
        from model import StateSpaceForecaster
        base = load_saved("persistence", "seasonal_naive", "calendar_ols")
        f = StateSpaceForecaster(mode=mode)
        t0 = time.time()
        r = H.evaluate(s, f, o)
        print(f"  fits={f.fits} elapsed={(time.time()-t0)/60:.1f}min")
        save(r, f"state_space_{mode}")
        print(f"  state_space[{mode}] {H.summarise(r, base['seasonal_naive'])}")
        print("  paired vs persistence   :", paired(r, base["persistence"]))
        print("  paired vs seasonal_naive:", paired(r, base["seasonal_naive"]))
        print(H.by_year(r))
        print(H.by_season(r))
        other = "rolling" if mode == "expanding" else "expanding"
        saved_other = load_saved(f"state_space_{other}")
        if saved_other:
            print(f"  ADAPTATION TEST paired {mode} vs {other}:",
                  paired(r, saved_other[f"state_space_{other}"]))
    else:
        raise SystemExit(f"unknown: {what}")
