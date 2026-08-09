"""
RDB-1 adaptation report: the frozen comparison between the two training-slice arms.

The arms differ ONLY in the training slice (expanding = all history to the origin;
rolling = the last 26 weeks). Everything else -- specification, refit schedule, origins,
horizon, metrics -- is held fixed by the contract, so any difference is attributable to
the slice and nothing else.

Paired inference is reported two ways. Origins step 24h and the horizon is 24h, so the
forecast windows do not overlap -- but adjacent days share weather and regime, so the
per-origin differences are serially correlated and the iid interval understates the
spread. The moving-block bootstrap is the interval of record; the iid one is printed
beside it to make the size of that correction visible rather than assumed.
"""

import numpy as np
import pandas as pd

from config import DATA

RESULTS = DATA / "results"
ARMS = ["persistence", "seasonal_naive", "calendar_ols",
        "state_space_expanding", "state_space_rolling"]
SEASONS = {12: "summer", 1: "summer", 2: "summer", 3: "autumn", 4: "autumn", 5: "autumn",
           6: "winter", 7: "winter", 8: "winter", 9: "spring", 10: "spring", 11: "spring"}


def load(name):
    return pd.read_csv(RESULTS / f"{name}.csv", index_col="origin", parse_dates=["origin"])


def block_bootstrap_ci(d, block=14, n_boot=20000, seed=7):
    """
    Moving-block bootstrap on the paired per-origin differences. A 14-day block spans
    two weekly cycles, so within-block serial dependence is carried rather than broken.
    """
    rng = np.random.default_rng(seed)
    d = np.asarray(d, dtype=float)
    n = len(d)
    n_blocks = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(n_boot, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(n_boot, -1)[:, :n]
    means = d[idx].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def paired(a, b, col="mae"):
    """Paired difference (a - b). Negative favours `a`."""
    d = (a[col] - b[col]).dropna().to_numpy(dtype=float)
    m = d.mean()
    half = 1.96 * d.std(ddof=1) / np.sqrt(len(d))
    lo, hi = block_bootstrap_ci(d)
    return {"mean_diff": m, "iid_lo": m - half, "iid_hi": m + half,
            "boot_lo": lo, "boot_hi": hi,
            "a_better_share": float((d < 0).mean()), "n": len(d)}


def fmt(p):
    return (f"{p['mean_diff']:+8.2f}  boot95[{p['boot_lo']:+7.2f},{p['boot_hi']:+7.2f}]  "
            f"iid95[{p['iid_lo']:+7.2f},{p['iid_hi']:+7.2f}]  "
            f"a_wins={p['a_better_share']:.1%}  n={p['n']}")


def main():
    r = {name: load(name) for name in ARMS}
    ref = r["seasonal_naive"]

    print("=" * 100)
    print("HEADLINE  (729 daily origins, 2021-01-01..2022-12-30, 48-step horizon)")
    print("=" * 100)
    print(f"{'arm':24s} {'MAE':>9s} {'RMSE':>9s} {'skillMAE':>9s} "
          f"{'cov50':>7s} {'cov80':>7s} {'cov95':>7s} {'CRPS':>9s}")
    for name in ARMS:
        d = r[name]
        skill = 1 - d["mae"].mean() / ref["mae"].mean()
        cov = [f"{d[c].mean():7.3f}" if c in d else f"{'--':>7s}"
               for c in ("cov50", "cov80", "cov95")]
        crps = f"{d['crps'].mean():9.2f}" if "crps" in d else f"{'--':>9s}"
        print(f"{name:24s} {d['mae'].mean():9.2f} {d['rmse'].mean():9.2f} "
              f"{skill:+9.3f} {' '.join(cov)} {crps}")

    exp, rol = r["state_space_expanding"], r["state_space_rolling"]

    print()
    print("=" * 100)
    print("THE ADAPTATION TEST — expanding minus rolling (positive = rolling better)")
    print("=" * 100)
    for col in ("mae", "rmse", "crps"):
        print(f"  {col.upper():5s} {fmt(paired(exp, rol, col))}")

    print()
    print("Each arm against the baselines (positive = baseline better)")
    for arm_name, arm in (("expanding", exp), ("rolling", rol)):
        for base in ("persistence", "seasonal_naive"):
            print(f"  {arm_name:9s} vs {base:15s} {fmt(paired(arm, r[base]))}")

    print()
    print("=" * 100)
    print("STABILITY — is the gap an artifact of one period?")
    print("=" * 100)
    gap = (exp["mae"] - rol["mae"]).dropna()
    for label, grouper in (("year", gap.index.year),
                           ("season", gap.index.month.map(SEASONS)),
                           ("half", np.where(gap.index < "2022-01-01", "2021", "2022"))):
        g = gap.groupby(grouper).agg(["mean", "count"])
        g["rolling_wins"] = gap.groupby(grouper).apply(lambda x: (x > 0).mean())
        print(f"\nby {label} (mean expanding-minus-rolling MAE):")
        print(g.to_string())

    print("\nper-arm MAE by year / season:")
    for name, d in (("expanding", exp), ("rolling", rol)):
        by_y = d.groupby(d.index.year)["mae"].mean()
        by_s = d.groupby(d.index.month.map(SEASONS))["mae"].mean()
        print(f"  {name:10s} " + "  ".join(f"{k}={v:7.1f}" for k, v in by_y.items())
              + " | " + "  ".join(f"{k}={v:7.1f}" for k, v in by_s.items()))


if __name__ == "__main__":
    main()
