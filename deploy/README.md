# deploy/ — what runs on the always-on box

**Host:** `187.124.32.36` — Ubuntu 24.04, systemd 255, Python 3.12.3.

---

## Why anything moved off the laptop

Not preference. Measured, 2026-08-21: the LIQ-2 archive had **21 snapshots in 42.5 hours** where
an hourly cadence is due 42. **Twenty-two hours lost, 52% of the archive**, and
`clearinghouseState` has no history so they are gone permanently.

The cause was macOS idle sleep. `pmset` logged sleep across exactly the gap windows and every
resumed scan landed within two minutes of a wake event. launchd's `StartInterval` does not fire
while the machine sleeps — it fires once on wake, which looks like a working schedule and is not.

For the archive that costs history. **For alerts it costs the product**: a missed alert is the
customer not being told the thing they subscribed for, at the moment it mattered.

## What runs here, and what stays local

| here | local |
|---|---|
| the alert bot (subscriptions) | the site build and deploy |
| the alert engine (every 5 min) | research, contracts, analysis |
| LIQ-2 scans (fast hourly, deep 6-hourly) | the q5/hl2 recorders, for now |

The split is by **whether a gap is recoverable**. A missed site rebuild fixes itself on the next
run; a missed scan or alert does not.

## Layout

```
/opt/genesis/market/{liqmap,hl_harvest}.py     code, root-owned, read-only to the service
/opt/genesis/product/{alerts,alertbot,telegram}.py
/home/genesis/genesis-evidence/liqmap/         the archive
/home/genesis/genesis-private/alerts/          watchlist, state, and the token (0600)
/etc/systemd/system/genesis-*                  the units in this directory
```

**Zero code changes were needed.** Everything is stdlib-only, and the paths are
`~/genesis-evidence` and `~/genesis-private` — systemd sets `HOME` from the service account, so
`expanduser` resolves under `/home/genesis` on the server exactly as it does under `/Users/gabana`
locally. That portability was the reason for writing it that way.

Runs as a dedicated `genesis` system account, never root: this box also serves three production
sites. The units are confined with `ProtectSystem=strict` and a single `ReadWritePaths`, because
the whole job is outbound HTTPS plus appending to its own files.

## Installing or updating

```sh
scp market/liqmap.py market/hl_harvest.py root@187.124.32.36:/opt/genesis/market/
scp product/{alerts,alertbot,telegram}.py    root@187.124.32.36:/opt/genesis/product/
scp deploy/systemd/*                          root@187.124.32.36:/etc/systemd/system/
ssh root@187.124.32.36 'systemctl daemon-reload && systemctl restart genesis-alertbot'
```

The token is **not** in this repo and not in any unit — it lives only in
`/home/genesis/genesis-private/alerts/env`, mode 600, referenced by `EnvironmentFile=`.

## Two things worth knowing about the units

**`genesis-liqmap@.service` is templated on the tier** (`fast`, `deep`) and calls `scan.sh`,
which wraps `flock -n`. systemd stops a unit overlapping *itself*, but fast and deep are separate
units sharing one archive and one fast set, and a deep scan runs ~2h22m. `-n` means a tier that
cannot take the lock exits immediately rather than queueing behind two hours of work and then
scanning a market that has moved.

The wrapper exists because the first version put `flock` straight in `ExecStart` with
`SuccessExitStatus=1` — which made a lock skip and a genuine python failure produce the
**identical** journal line, "Deactivated successfully" in zero seconds. It cost twenty minutes of
misdiagnosis on the day it was deployed. `flock -E 99` now gives the skip its own exit code, and
the wrapper logs it in words:

```
scan.sh[1384626]: skipped: the fast tier could not take the scan lock; another scan is in progress
```

**`Persistent=true`** on every timer: a run missed while the box was down fires once on boot
rather than waiting a full interval.

## Checking on it

```sh
ssh root@187.124.32.36 'systemctl list-timers genesis-*
  systemctl status genesis-alertbot
  journalctl -u genesis-alerts -n 20
  tail /home/genesis/genesis-private/alerts/alerts.log'
```
