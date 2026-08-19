"""
Single entry point for the whole suite.

    .venv/bin/python tests/run_all.py            # everything
    .venv/bin/python tests/run_all.py recorder   # only suites matching a substring

Each suite is a standalone script with its own runner, so each runs in its own process.
That is deliberate: the suites insert different paths onto `sys.path` and hold module-level
state, and running them in one interpreter would let one suite's imports change another's
behaviour. A test that passes only because of what ran before it is not evidence.

Exit code is non-zero if any suite fails, so this is the command CI would run -- if this
project ever has CI, which today it does not.
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PYTHON = ROOT / ".venv" / "bin" / "python"

# Ordered fastest-first so a broken invariant surfaces before the slow laboratory replays.
SUITES = [
    "test_recorder.py",
    "test_recorder_audit.py",
    "test_multi_connection.py",
    "test_costs.py",
    "test_carry.py",
    "test_dir1.py",
    "test_dir2.py",
    "test_recorder_decimal_qty.py",
    "test_recorder_validity.py",
    "test_health_cli.py",
    "test_status.py",
    "test_provenance.py",
    "test_completeness.py",
    "test_recorder_binance.py",
    "test_recorder_aggtrade.py",
    "test_bav.py",
    "test_market.py",
    "test_ledger.py",
    "test_fills.py",
    "test_holons.py",
    "test_holon_volatility.py",
    "test_holon_cross_section.py",
    "test_rdb_series.py",
    "test_closed_loop.py",
    "test_sparse_loop.py",
    "test_laboratory.py",
    "test_laboratory2.py",
    "test_laboratory3.py",
]


def run(name):
    proc = subprocess.run([str(PYTHON if PYTHON.exists() else sys.executable), str(HERE / name)],
                          capture_output=True, text=True, cwd=ROOT)
    tail = [ln for ln in (proc.stdout or "").strip().splitlines() if ln.strip()]
    summary = tail[-1] if tail else (proc.stderr or "").strip().splitlines()[-1:] or ["no output"]
    return proc.returncode, (summary if isinstance(summary, str) else summary[0]), proc


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    selected = [s for s in SUITES if not argv or any(a in s for a in argv)]
    if not selected:
        print(f"no suite matches {argv}; known suites:\n  " + "\n  ".join(SUITES))
        return 2

    missing = [s for s in selected if not (HERE / s).exists()]
    if missing:
        print("MISSING SUITE FILES: " + ", ".join(missing))
        return 2

    print(f"GENESIS TEST SUITE — {len(selected)} suite(s)")
    print("=" * 78)
    failures = []
    for name in selected:
        code, summary, proc = run(name)
        status = "ok  " if code == 0 else "FAIL"
        print(f"  {status} {name:<30} {summary[:44]}")
        if code != 0:
            failures.append((name, proc))

    print("=" * 78)
    if failures:
        for name, proc in failures:
            print(f"\n----- {name} (exit {proc.returncode}) -----")
            print((proc.stdout or "").strip()[-3000:])
            if proc.stderr.strip():
                print("--- stderr ---")
                print(proc.stderr.strip()[-2000:])
        print(f"\nFAIL — {len(failures)} of {len(selected)} suites failed")
        return 1

    print(f"PASS — {len(selected)} of {len(selected)} suites passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
