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
