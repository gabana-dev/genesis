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
