# The stack — what we use, why, and the one open decision

**Written 2026-08-21, late.** We discussed this days ago and I never wrote it down, so there was
nothing to follow and nothing to check myself against. That is the actual failure this document
fixes: a decision that lives only in a conversation is not a decision.

---

## What is actually running today

| layer | built with | why |
|---|---|---|
| collectors, recorders | Python 3, **stdlib only** | no install, no version drift, runs anywhere |
| the scanner | Python (`market/liqmap.py`) | it is the research instrument; the product borrows it |
| the alert engine | Python (`product/alerts.py`) | imports the scanner's own HTTP path — one implementation |
| the site | Python generating HTML (`product/site.py`) | one source of truth: pages are built *from* the JSON the API serves |
| the wallet check | ~117 lines of vanilla JS in the browser | calls Hyperliquid directly — no server, no key, scales without us |
| scheduling | launchd | cron is dead on this machine (`d918c8a`) |
| hosting | GitHub Pages | free, and the repo is already the deploy artifact |
| storage | JSONL + JSON files | no database, because nothing here needs one yet |

**24,107 lines of Python. Zero lines of TypeScript. No Node, no package.json.**

Everything runs on hardware already owned and costs nothing per month. That was the binding
constraint and it still holds.

## Astro and TypeScript — the confusion worth clearing up

These are not alternatives to each other, and "free" is not the axis they differ on.

- **TypeScript is a language.** JavaScript with types checked before the code runs.
- **Astro is a site framework.** A tool that takes components and produces static HTML.

You write TypeScript *inside* Astro. Astro is the box; TypeScript is what goes in it. Both are
free and open source, and so is the Python we are using — cost was never what separated them.

**The real comparison is this:**

| | today | the alternative |
|---|---|---|
| what generates the HTML | `product/site.py` — 732 lines of Python | Astro — components in TypeScript |
| what it outputs | static files in `docs/` | static files in `dist/` |
| what it costs | nothing | nothing |
| where it deploys | GitHub Pages | GitHub Pages |
| build step | `python product/site.py` | `npm run build` |

Both produce the same kind of thing. Neither is more "free" than the other. The difference is
what the code is like to work in, and what it is worth to have written.

## The case for moving the frontend to Astro + TypeScript

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

## The case against moving it today

It works, it ships, and it costs nothing to keep. A rewrite now delays the only surface with
revenue attached, and delivers a page that looks identical to the one already live.

## The proposal

**Split by what each language is actually good at, and move at the moment it is free to move.**

- **Python keeps the engine.** Collection, measurement, the scanner, the alert bot. This is not
  sentiment — the research, the contracts and every measurement live there, and rewriting
  measurement code is how measurements silently change.
- **TypeScript takes the frontend**, at the naming and rebrand. The shell is being rebuilt then
  anyway, so the cost is paid once instead of twice.
- **The two meet at JSON**, with the shape declared as TypeScript types. That turns an unchecked
  boundary into a checked one, which is a real gain and not just a language preference.

**Astro rather than Next**, if we go: the product is content plus one interactive island (the
wallet check). Astro ships zero JavaScript by default, which suits a site whose whole argument is
that it is legible and fast. Next would mean a server we do not need and cannot afford.

Tailwind v4 with `@tailwindcss/vite` if styling moves too — **not** `@astrojs/tailwind`, which
only supports v3.

**Status: proposed, not decided.** Nothing is being rewritten until Gabana says so.

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
