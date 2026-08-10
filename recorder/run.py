"""
Recorder CLI.

  .venv/bin/python recorder/run.py record  <log> <ticker> [--seconds N]  # live; needs creds
  .venv/bin/python recorder/run.py verify  <log>
  .venv/bin/python recorder/run.py health  <log>
  .venv/bin/python recorder/run.py book    <log> <ticker> [--at ISO8601]
  .venv/bin/python recorder/run.py account <log> [--at ISO8601]

`record` is the only subcommand that touches the network, and it is the only one that has
never been exercised against the live venue.
"""

import argparse
import json
import sys

import health
import replay
from log import EventLog, verify
from stream import Ingestor


def _arg(args, flag, default=None):
    return getattr(args, flag, default)


MANIFEST_TEMPLATE = {
    "purpose": "Validate the recorder against externally generated live traffic.",
    "not_testing": ["trading", "prediction", "decision quality", "profitability",
                    "Genesis environment selection"],
    "external_specification": {
        "source": "Binance published depth reconciliation rules",
        "rules": ["drop events where u <= lastUpdateId of the REST snapshot",
                  "first kept event satisfies U <= lastUpdateId+1 <= u",
                  "every subsequent event satisfies U == previous u + 1"],
    },
    "must_hold_or_the_run_failed": [
        "live connection established",
        "REST snapshot and stream messages captured",
        "sequence semantics handled per the external specification",
        "venue and receipt timestamps both preserved and distinct",
        "decimal quantities preserved without loss",
        "replay reconstructs state deterministically",
        "health reports completeness honestly",
        "no silent repair of missing information",
    ],
    "observed_only_if_they_occur": [
        "natural sequence gaps", "natural reconnects", "malformed messages",
        "timestamp anomalies", "undocumented fields",
        "-- absence of these is reported as NOT OBSERVED, never as success",
    ],
    "fail_conditions": [
        "recorder crashes",
        "a sequence discontinuity occurs that the recorder does not record",
        "replay disagrees with itself",
        "health claims complete over an interval containing a recorded gap",
        "any silent repair, default or interpolation of missing data",
    ],
    "binding_rule": ("The recorder is NOT modified during or after this run to make the "
                     "results look cleaner (DR0003). Any defect found is recorded first."),
}


def cmd_bav(args):
    """BAV-1. Implements recorder/CONTRACT-book-agreement.md exactly."""
    import asyncio
    import hashlib
    import pathlib

    import bav
    import binance
    import dialects
    import events as E

    contract_path = pathlib.Path(__file__).resolve().parent / "CONTRACT-book-agreement.md"
    contract_bytes = contract_path.read_bytes()
    schedule = bav.build_schedule(args.seed)

    manifest = {
        "experiment": "BAV-1 Book Agreement Validation",
        "contract_file": contract_path.name,
        "contract_sha256": hashlib.sha256(contract_bytes).hexdigest(),
        "run_commit": args.commit,
        "sampling_seed": args.seed,
        "environment": "Binance Spot (public market data, unauthenticated)",
        "symbol": args.symbol.upper(),
        "stream": "depth",
        "n_slots": bav.N_SLOTS, "n_controlled": bav.N_CONTROLLED,
        "warmup_slots": bav.WARMUP_SLOTS,
        "dwell_s": bav.DWELL, "probe_offset_s": bav.PROBE_OFFSET,
        "skew_exclude_ms": bav.SKEW_EXCLUDE_MS,
        "thin_book_levels": bav.THIN_BOOK_LEVELS,
        "required_usable_incomplete": bav.REQUIRED_USABLE_INCOMPLETE,
        "controlled_slots": [x["slot"] for x in schedule if x["controlled"]],
        "last_scheduled_action_s": max(t for t, _, _ in bav.timeline(schedule)),
        "min_recording_s": args.min_seconds,
        "declared_resolution": (
            "Contract 12.1 requires a recording of at least 60 minutes; the 60-slot schedule "
            "at this seed completes earlier. Recording continues to min_recording_s after the "
            "last probe. No probe parameter, metric, exclusion or threshold is affected."),
        "not_testing": ["trading", "prediction", "decision quality", "profitability",
                        "Genesis environment selection", "hypothesis 0001"],
        # Recorded BEFORE the run, so it is a known limitation rather than an excuse
        # constructed from the result.
        "known_limitation_declared_in_advance": {
            "condition": "Contract section 13 PASS requires >=95% of complete trials with "
                         "skew_ms < 300 to achieve M1.",
            "expectation": "STRUCTURALLY UNEVALUABLE on the current fetch path. The <300ms "
                           "regime is not reachable from this environment; the denominator "
                           "is expected to be empty again.",
            "independent_measurement_2026_08_10": {
                "method": "standalone timed REST requests, no recorder involved",
                "api_v3_time_28B_new_conn": "n=40 min 291.2ms p50 297.0ms, 23/40 under 300ms",
                "depth_limit5_367B_new_conn": "n=25 min 291.4ms p50 314.2ms, 9/25 under 300ms",
                "depth_limit1000_62KB_new_conn_SAME_AS_BAV": "n=30 min 321.9ms p50 331.6ms, "
                                                             "0/30 under 300ms",
                "depth_limit1000_persistent_conn": "n=20 min 244.9ms p50 248.1ms, "
                                                   "14/20 under 300ms",
                "conclusion": "~291ms floor is network RTT + DNS + TLS; the 62KB payload adds "
                              "only ~30ms; connection reuse would save ~84ms. Run 1's skew "
                              "(min 327ms, 0/60 under 300ms) was not anomalous.",
            },
            "decisions_taken": [
                "The 300ms threshold is NOT changed. It was an engineering proxy with no "
                "empirical basis, but replacing one arbitrary number with another because "
                "the first proved inconvenient would be worse.",
                "The fetch mechanism is NOT changed to persistent connections. That may be a "
                "legitimate future instrument improvement, but introducing it here would add "
                "a third variable and confound attribution of any difference to D-A/D-B.",
            ],
            "consequence": "PASS is expected to be reported as structurally unevaluable. "
                           "Question B does NOT depend on this threshold: it is a "
                           "within-stratum comparison and remains answerable in the "
                           "300-1000ms band, which held 56 of 60 trials in run 1.",
        },
        "run_1_defects_corrected": {
            "D-A": "REST snapshots were given a stream sequence from lastUpdateId, so every "
                   "fetch after the first emitted a SEQUENCE_GAP with market_ticker=None, "
                   "which invalidated every market and left zero complete trials.",
            "D-B": "REST price keys were raw while replay keys were canonical, so set "
                   "intersection was empty by construction and M3/M4/M5/M6 measured nothing.",
            "scope": "Only these two fixes were applied. No contract condition changed.",
        },
        "binding_rule": ("Contract, thresholds, metrics, seed, schedule, controlled protocol "
                         "and exclusions are FIXED. No metric may be added after seeing "
                         "results. No probe may be repaired, reinterpreted or rerun."),
        "started_at": None,
    }

    with EventLog(args.log) as log:
        ing = Ingestor(log, dialect=dialects.BINANCE)
        manifest["started_at"] = E.now()
        ing.started(manifest)
        try:
            asyncio.run(bav.run(ing, args.symbol, schedule,
                                min_seconds=args.min_seconds))
        except KeyboardInterrupt:
            ing.error("interrupted", "KeyboardInterrupt")
        finally:
            ing.stopped("BAV-1 run complete")
    print(health.render(health.report(args.log)))


def cmd_binance(args):
    """Public market data only. No account, no credentials, no orders."""
    import asyncio

    import binance
    import dialects

    manifest = dict(MANIFEST_TEMPLATE)
    manifest.update({
        "environment": "Binance Spot (public market data, unauthenticated)",
        "symbol": args.symbol.upper(),
        "stream": "depth",
        "duration_seconds": args.seconds,
        "forced_reconnect_after_seconds": args.reconnect_after,
        "started_at": None,   # filled below, from the Genesis clock
    })

    with EventLog(args.log) as log:
        ing = Ingestor(log, dialect=dialects.BINANCE)
        import events as E
        manifest["started_at"] = E.now()
        # The manifest is event 0, inside the hash chain: pre-committed and tamper-evident.
        ing.started(manifest)
        try:
            asyncio.run(binance.record(ing, args.symbol,
                                       stop_after=args.seconds,
                                       reconnect_after=args.reconnect_after))
        except KeyboardInterrupt:
            pass
        finally:
            ing.stopped("run complete")
    print(health.render(health.report(args.log)))


def cmd_record(args):
    import asyncio

    import kalshi

    with EventLog(args.log) as log:
        ing = Ingestor(log)
        ing.started({"markets": args.tickers, "url": kalshi.WS_URL,
                     "seconds": args.seconds})
        try:
            asyncio.run(kalshi.record(ing, args.tickers, stop_after=args.seconds))
        except KeyboardInterrupt:
            pass
        finally:
            ing.stopped("cli exit")
    print(health.render(health.report(args.log)))


def cmd_verify(args):
    ok, problems = verify(args.log)
    print(f"integrity_verified: {ok}")
    if problems:
        print(json.dumps(problems, indent=2))
    return 0 if ok else 1


def cmd_health(args):
    rep = health.report(args.log)
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        print(health.render(rep))


def cmd_book(args):
    out = replay.order_book_at(args.log, args.ticker, at=args.at)
    print(json.dumps(out, indent=2, sort_keys=True))
    if not out["complete"]:
        print(f"\nINCOMPLETE: {out['reason']}", file=sys.stderr)


def cmd_account(args):
    print(json.dumps(replay.account_state_at(args.log, at=args.at), indent=2, sort_keys=True))


def main(argv=None):
    p = argparse.ArgumentParser(prog="recorder")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record"); r.add_argument("log"); r.add_argument("tickers", nargs="+")
    r.add_argument("--seconds", type=float, default=60.0); r.set_defaults(fn=cmd_record)

    bn = sub.add_parser("binance"); bn.add_argument("log"); bn.add_argument("symbol")
    bn.add_argument("--seconds", type=float, default=1800.0)
    bn.add_argument("--reconnect-after", type=float, default=None, dest="reconnect_after")
    bn.set_defaults(fn=cmd_binance)

    bv = sub.add_parser("bav"); bv.add_argument("log"); bv.add_argument("symbol")
    bv.add_argument("--seed", type=int, required=True)
    bv.add_argument("--commit", default="unknown")
    bv.add_argument("--min-seconds", type=float, default=3600.0, dest="min_seconds")
    bv.set_defaults(fn=cmd_bav)

    v = sub.add_parser("verify"); v.add_argument("log"); v.set_defaults(fn=cmd_verify)

    h = sub.add_parser("health"); h.add_argument("log")
    h.add_argument("--json", action="store_true"); h.set_defaults(fn=cmd_health)

    b = sub.add_parser("book"); b.add_argument("log"); b.add_argument("ticker")
    b.add_argument("--at", default=None); b.set_defaults(fn=cmd_book)

    a = sub.add_parser("account"); a.add_argument("log")
    a.add_argument("--at", default=None); a.set_defaults(fn=cmd_account)

    args = p.parse_args(argv)
    return args.fn(args) or 0


if __name__ == "__main__":
    sys.exit(main())
