# The design system

**The concept is the name.** An isobath is a depth contour — a line on a nautical chart joining
points where the water is equally deep. Charts exist for one purpose: to stop a vessel running
aground. That is not a metaphor we are borrowing. It is what this product does.

So the visual language is the **information design of a nautical chart**, and nothing else.

---

## 1. Why this, and not the two things everyone else does

| | what it is | why not |
|---|---|---|
| **the terminal** — Hyperdash, Coinglass | dense panels, red/green, no whitespace | functional and ugly; inherited from Bloomberg by people who never chose it |
| **the enterprise template** — Kaiko | blue gradient hero, logo wall, orange CTA | competent, and interchangeable with every other B2B data company |

Neither was designed. That gap is the whole opportunity: **there is no crypto data product with a
considered visual identity.**

## 2. Strange, and familiar — the balance, resolved deliberately

A trader scanning under stress needs instant familiarity. A product whose pitch is *"not another
dashboard"* needs to not look like one. Those pull in opposite directions and the resolution is to
be **conventional in structure and unconventional in surface.**

| familiar — never fight this | strange — where we spend it |
|---|---|
| price ladder, high to low | chart hazard **magenta**, not red/green |
| tabular figures, aligned | contour linework as the structural motif |
| distance as a percentage | soundings — precise small numerals in the field |
| dark interface | a ground with real chroma, not neutral grey |
| the shape of a liquidation map | editorial typography and generous space |

**The discipline: take the information design of charts, never the props.** No parchment, no
compass rose, no rope borders, no wood. A chart is beautiful because it is ruthlessly functional
at extreme density, and that is the part worth stealing.

## 3. Colour — every value inherited from the domain

Real charts encode danger by saturation: deep water is white and safe, shallow water grows bluer,
and **hazards are magenta**. We invert the lightness for a dark interface and keep the logic.

```
--abyss    #0a1416   deepest ground — the page
--deep     #0f1e21   raised surfaces, cards
--shoal    #162c30   shallower — hover, active
--reef     #1d3a3e   the shallowest tier, borders

--sounding #e8ede9   figures and primary text
--ink      #a9bdb8   body
--faint    #62807d   labels, provenance

--hazard   #e8467f   UNDEFENDABLE. magenta because that is the chart hazard colour
--safe     #5fd4a3   defendable, free collateral, stand-down
--depth    #4a9db5   the contour system, links, structure
```

**Magenta is the single most important decision here.** Every competitor uses red for danger,
which in a trading context also means *price down* — an ambiguity we inherit for free and should
refuse. Magenta means one thing on a chart: **hazard, and it does not move.** That is precisely
what an undefendable position is.

The ground is a desaturated deep teal, not grey. Neutral near-black is what "dull" looks like;
chroma at very low lightness reads as considered without shouting.

## 4. Typography — three roles, no overlap

| role | face | used for |
|---|---|---|
| **display** | Instrument Serif | headlines only. High contrast, editorial, unmistakably chosen |
| **interface** | Geist | body, navigation, controls |
| **figures** | Geist Mono | every number, every address, every provenance line |

**Not Inter.** It is the default that signals no decision was made.

Numerals are **tabular everywhere they align**. A ladder whose digits shift width as prices move
cannot be scanned, and scanning is the only way it gets read.

Labels are the chart convention: uppercase, small, wide letter-spacing, faint. They name a thing
without competing with it.

Self-hosted, subset, `font-display: swap`. No third-party request on any page.

## 5. Width — a scale, not a number

The current single 46rem measure is a prose width applied to a data product, which is why it feels
cramped and why the map has nowhere to breathe.

```
--w-prose    38rem   research, long reads — a real reading measure
--w-page     64rem   the standard: most pages
--w-wide     82rem   the map, tables, anything with columns
```

One page may use several. The map goes wide; the paragraph explaining it does not.

## 6. Hierarchy — what the eye does, in order

The current failure is that headings, body, provenance and notes all sit inside a narrow contrast
band, so nothing leads. The fix is **three tiers with real distance between them**:

1. **The answer.** One per page. Display face, large, `--hazard` or `--safe`. Nothing else on the
   page may use that size.
2. **The sentence that explains it.** Interface face, comfortable, `--ink`.
3. **The provenance.** Mono, small, `--faint`. Always present, never competing.

A caveat set at tier 3 that *matters* gets promoted to tier 2 — as the population note now does.
Invisible honesty is not honesty.

## 7. Motion — one moment, then stillness

Charts do not animate. But a page that never moves feels dead, and the user is right that it
currently does.

- **Contours draw in once** on the hero, `stroke-dashoffset` over ~900ms. One orchestrated moment.
- **Map bars extend from zero** on first paint, staggered ~20ms apart. It reads as depth being
  sounded.
- **Figures cross-fade** when data refreshes, so a changing number is noticed rather than missed.
- **Hover is instantaneous.** Never animate a state a user is waiting on.

Everything behind `prefers-reduced-motion`. Nothing blocks content. No parallax, no scroll-jacking,
no reveal-on-scroll — those signal template, which is exactly what we are avoiding.

## 8. Language by audience — the same discipline as colour

One product, three registers. Getting this wrong is the fastest way to look generic.

**The trader** — home, check, alerts. Second person, present tense, short. The vocabulary they
already use: *liquidation, margin, notional, size, wick, get filled*. Never "leverage your
insights". Never "empower".

**The developer** — API, MCP. No marketing sentences at all. A `curl` that runs, a response shape,
a rate limit, a stated failure mode. Developers read code blocks and skip prose; write for the
skip.

**The desk** — B2B, later. Coverage, method, limits, SLA, what happens when it is wrong.
Procurement reads for risk, not for benefit.

**Everywhere:** crypto-native and specific. "Forced selling" not "market volatility". "Zero free
collateral" not "elevated risk". The product's credibility comes from sounding like someone who
has actually held a position.

## 9. What must never happen

- A gradient hero. It is the single clearest tell of a template.
- A logo wall.
- Red/green as the primary semantic pair.
- An icon that is not load-bearing.
- Rounded-everything. Charts are drawn with fine straight lines; radius is 2–3px or absent.
- Any element that cannot answer *what is this for*.

## 10. How this gets judged

Not "does it look nice". **Can a frightened trader, on a phone, in ten seconds, find their answer
— and does the page look like a person decided every part of it?**

If a competitor could ship the same page by changing the logo, it has failed.
