# The stack — what we use and why

**Written 2026-08-21, late.** We discussed this days ago and I never wrote it down, so there was
nothing to follow and nothing to check myself against. That is the actual failure this document
fixes: a decision that lives only in a conversation is not a decision.

Written as a proposal that morning, approved and executed the same day. The reasoning below is
kept in its original form rather than rewritten to sound inevitable — the arguments against are
the ones worth still being able to read.

---

## What is actually running today

| layer | built with | why |
|---|---|---|
| collectors, recorders | Python 3, **stdlib only** | no install, no version drift, runs anywhere |
| the scanner | Python (`market/liqmap.py`) | it is the research instrument; the product borrows it |
| the alert engine | Python (`product/alerts.py`) | imports the scanner's own HTTP path — one implementation |
| the site | **Astro 5 + TypeScript** (`web/`) | components, a typed data contract, one shared stylesheet |
| the wallet check | a TypeScript island (`web/src/scripts/check.ts`) | calls Hyperliquid directly — no server, no key, scales without us |
| scheduling | launchd | cron is dead on this machine (`d918c8a`) |
| hosting | GitHub Pages | free, and the repo is already the deploy artifact |
| storage | JSONL + JSON files | no database, because nothing here needs one yet |

**The frontend rewrite is DONE (2026-08-21).** Python keeps the engine; Astro + TypeScript own
the site. The two meet at `web/public/data/*.json`, and that boundary is now validated at build
time by `web/src/lib/data.ts` — a renamed field in the engine fails the build instead of
publishing a page that renders `undefined%`.

Everything runs on hardware already owned and costs nothing per month. That was the binding
constraint and it still holds.

## Astro and TypeScript — the confusion worth clearing up

These are not alternatives to each other, and "free" is not the axis they differ on.

- **TypeScript is a language.** JavaScript with types checked before the code runs.
- **Astro is a site framework.** A tool that takes components and produces static HTML.

You write TypeScript *inside* Astro. Astro is the box; TypeScript is what goes in it. Both are
free and open source, and so is the Python we are using — cost was never what separated them.

**The real comparison is this:**

| | before | after |
|---|---|---|
| what generates the HTML | `product/site.py` — 732 lines of Python | Astro — components in TypeScript |
| what it outputs | static files in `docs/` | static files in `docs/` |
| what it costs | nothing | nothing |
| where it deploys | GitHub Pages | GitHub Pages |
| build step | `python product/site.py` | `npm run build` |

Both produce the same kind of thing. Neither is more "free" than the other. The difference is
what the code is like to work in, and what it is worth to have written.

## The case for moving, as argued at the time

**1. `site.py` is HTML inside Python f-strings, and it is 732 lines.** It works, but there is no
component model, no type checking, and the styling lives in a separate CSS file that nothing
verifies against the markup. It gets worse from here, not better.

**2. The engine/frontend boundary is currently unchecked.** `generate.py` writes JSON;
`site.py` reads it. If a field is renamed, nothing catches it — the page just renders wrong.
A typed contract at that boundary is exactly what TypeScript is for.

**3. It is the piece that doubles as a hiring artifact.** The stated goal is a remote
React/Next/TypeScript contract at $40–80/hr. Nobody assessing that hires on a Python f-string
HTML generator. A typed frontend consuming a real measurement engine is a portfolio piece; this
is the only part of the system where the language choice has a second payoff.

## The case against, as argued at the time

It works, it ships, and it costs nothing to keep. A rewrite now delays the only surface with
revenue attached, and delivers a page that looks identical to the one already live.

## What was decided

**Split by what each language is actually good at, and move at the moment it is free to move.**

- **Python keeps the engine.** Collection, measurement, the scanner, the alert bot. This is not
  sentiment — the research, the contracts and every measurement live there, and rewriting
  measurement code is how measurements silently change.
- **TypeScript takes the frontend.** Proposed for the rebrand, brought forward on Gabana's
  call the same day.
- **The two meet at JSON**, with the shape declared as TypeScript types. That turns an unchecked
  boundary into a checked one, which is a real gain and not just a language preference.

**Astro rather than Next:** the product is content plus one interactive island (the
wallet check). Astro ships zero JavaScript by default, which suits a site whose whole argument is
that it is legible and fast. Next would mean a server we do not need and cannot afford.

Styling stayed as the hand-written stylesheet it already was; Tailwind was not introduced and
is not needed for 119 lines of CSS. If it ever is: Tailwind v4 with `@tailwindcss/vite`, **not**
`@astrojs/tailwind`, which only supports v3.

**Status: DONE.** Approved and executed 2026-08-21. All 13 published URLs survived the rewrite
unchanged — `build.format: 'preserve'` exists in the config for exactly that reason, because a
link someone already sent a friend must not break in a refactor.

## Where the data-structure work actually is

Worth recording, because "we should do DSA" turns into nothing unless it is pointed at something
real. Three places where it has already paid:

- **`recorder/stream.py`** — the duplicate-detection window called `sorted()` on every insert,
  making restart quadratic in log size. Replaced with O(1) eviction: 161 µs → 5.6 µs per event,
  22×, and a restart went from over an hour to ~90 seconds.
- **`market/evaporation_run.py`** — streaming instead of loading ~45M entries. 0.06 GB resident
  over 1,324 days of data.
- **`product/alerts.py`** — a state machine whose entire purpose is *not* emitting. The
  hysteresis rule is the difference between a product and a spam cannon.

None of that came from practising exercises. It came from something being too slow or too loud.
