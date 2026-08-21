# Alerts — the first thing anyone will pay for

**Nobody pays to look at a page. They pay to be told something while they are asleep.**

The wallet check is commercially inert: it answers a question the trader already knew to ask.
The alert answers one they did not — at the moment it matters, without them being at a screen.

---

## Why Telegram, and not email

| | Telegram | email |
|---|---|---|
| cost to start | free | needs a verified sending domain |
| deliverability | a bot message arrives | spam folder is a real failure mode |
| where the customer is | already there | not while a position is moving |
| infrastructure | `getUpdates` long-polls **out** | needs an inbound endpoint or a provider |
| subscription flow | `/watch 0x…` in the app they already have | a form, a confirmation, a stored email |

Telegram needs **no domain, no server, no webhook, no database**. The bot polls outward from
wherever the process runs, so the whole subscription system is a long-poll loop and a JSONL file.

That is not a compromise made because we are cheap. An inbound webhook would need a public HTTPS
endpoint — a cost, a certificate and an attack surface — to do something a loop already does.

## Why it runs where the scanner runs

The alert engine is the scanner pointed at *one* wallet instead of the top 300. Same endpoint,
same parsing, same rate budget. Putting it anywhere else would mean a second implementation of
the thing most likely to be wrong.

**A laptop is the wrong host for an alarm** — it sleeps, and an alert that arrives late is worse
than none, because it teaches the customer the alarm cannot be trusted. The engine is written
host-agnostic (stdlib only, two state files) so it moves to the always-on box unchanged.

## What we alert on

Two rules ship. Both are **observed or calculated** — nothing on the predicted tier, which stays
deliberately empty (`product/IA.md`).

### A. Proximity — you are close

Fires when the closest liquidation crosses **into** a tighter band: 25%, 15%, 10%, 5%, 2%.

Bands, not a continuous stream, because a threshold crossed is an event and a distance is a
number. **Hysteresis of 1.25×** — a band cannot fire again until distance has recovered a
quarter past it. Without that, price oscillating around 10.0% sends an alert every cycle, and a
customer who is spammed once unsubscribes forever.

The mirror rule fires **once**: a position that goes from inside 10% back out past 25% gets a
stand-down. It costs nothing and it is the message that proves the alarm was watching.

### B. Cannot defend — you are close *and* trapped

Fires when free collateral collapses against margin in use while a position is within 25%.

**This is the one nobody else sends.** F-0001 measured that the obvious arithmetic for free
collateral matches the exchange's own figure **19%** of the time and misclassifies **one wallet
in five** as able to defend when it is not — always in the direction of looking safer. A tool
that computes it the obvious way will tell a trapped trader they are fine.

Trips below a cushion of **0.05**, re-arms above **0.10**.

### C. Crowd ahead — deliberately not shipped

We can see the forced selling sitting between a wallet and its own liquidation price. It is the
most impressive thing we could send and it is **the most likely to mislead**.

CASCADE-1 (F-0010) measured that reaching a cluster does not move price more than a
volatility-matched minute in the same hour. An alert saying "$40M of forced selling sits between
you and liquidation" would be read as *you are about to be dragged in* — which is the thing we
disproved. Shipping it would be selling our own refuted claim back to a frightened person.

**Not closed, withheld.** The measurement that would justify it does not exist yet. If one
arrives, the rule is already written in outline and the data is already collected.

## The state machine

Every alert is a **transition**, never a level. The engine holds one record per
`chat · address · coin`:

```
band:    the tightest band already reported     (None until first crossing)
cushion: "ok" | "trapped"
```

An alert is emitted only when one of these changes. This is the whole anti-spam design, and it
is also why the engine is stateless between runs except for one small file: if the state file is
lost, the worst case is one duplicate alert per position, never a missed one.

## Privacy

An address paired with a chat id is personal data. **The watchlist never enters the public
repo** — it lives in `~/genesis-private/alerts/`, alongside the business plan.

The public site's wallet check stores nothing at all; the lookup happens in the visitor's own
browser. Subscribing to alerts is the moment that changes, and it must be the customer's
deliberate act — `/watch`, typed by them.

## The commercial shape

Free is three addresses. That is not a trial, it is the whole product for a retail trader with
one account, and it should stay genuinely useful — the free tier is the distribution.

What is worth money is not more addresses:

| paid for | why someone pays |
|---|---|
| **faster interval** | 5 minutes is fine at 10%; at 2% it is not |
| **more bands, custom thresholds** | a desk wants 1.5%, not our ladder |
| **many addresses** | funds, treasuries, HLP depositors |
| **the same alerts as a webhook** | B2B does not read Telegram, it ingests |

No billing is built. The limit exists as one constant so the boundary is real from the first
subscriber rather than retrofitted onto people who got used to unlimited.

## Measured 2026-08-21: the laptop is not a host

"A laptop is the wrong host for an alarm" was written above as an argument. It is now a
measurement, taken from the collector that has been running longest.

| | |
|---|---|
| LIQ-2 archive span | 42.5h |
| hourly scans due | 42 |
| snapshots actually taken | 21 |
| **hours lost** | **22 — 52% of the archive** |

`clearinghouseState` has no history, so every one of those hours is gone permanently.

The cause is not the scanner. macOS `pmset` logs idle sleep across exactly the gap windows, and
every resumed scan lands within two minutes of a wake event — `02:01Z` follows a UserActivity
wake at `01:59Z`, `06:42Z` follows one at `06:26Z`. launchd's `StartInterval` does not fire while
the machine sleeps; it fires once on wake. Power Nap is off, and it sleeps on AC as well as
battery.

**The collector watch was right and I assumed it was twitchy.** Three of the four overnight
STALLED alarms were real data loss. The other three alarms in that log were already-fixed
config: `econ1` fired before its archive could publish (`advance_from` since moved to the 23rd)
and `hl2` used `recorder.out` as its liveness signal when a continuous recorder only writes it at
start and stop (since pointed at the data file).

**The consequence for this product is worse than for the archive.** A missed scan costs one hour
of history. A missed alert costs the customer the thing they subscribed for, at the exact moment
it mattered — and they only find out afterwards.

Target host: `187.124.32.36` — Ubuntu 24.04, systemd 255, Python 3.12.3, up 11 weeks, 19 GB free.
The engine is stdlib-only and host-agnostic for exactly this move.
