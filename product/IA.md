# Isobath — information architecture

**Version 2, 2026-08-22.** v1 is kept at `product/IA-v1-2026-08-21.md`. It was written when the
product had one differentiator; three measurements have since changed what can honestly be sold,
and one of them changed what the site is allowed to say.

**Principle, unchanged: answer the question before showing the data.**

---

## 0. Four things this document refuses to build, and why

A product review proposed the shape below. Most of it is adopted. These four are not, and the
reasons are measurements, not preferences. They are recorded here so the same suggestions do not
return in three months looking reasonable.

| proposed | why not |
|---|---|
| **A scorecard with "Forecasts: 42 · Correct: 21 · Accuracy 67.7%"** | Isobath makes **no forecasts**. F-0005 measured that detecting a 52% directional edge on one instrument at daily horizon needs 4,900 independent observations — **13.4 years**. An accuracy percentage would require predictions we have measured we cannot power. The `predicted` provenance tier is empty on purpose and stays empty. |
| **Headline "We observe 53.3% of BTC open interest"** | **32% is observed. 53.3% is the full-universe estimate** (F-0003). Quoting the estimate as the observation is the exact error that sat in the business plan for a day, and this site exists to not make it. The observed figure leads; the estimate appears next to it, labelled. |
| **Cluster rows reading "73% unable to defend / 81% unable"** | F-0012 measured `cannot_defend_pct` at **~100% for 71% of clusters**, median 100.0. It does not vary like that. A mock that invents variance teaches the reader to look for a signal that is not there. |
| **"Defensibility score: 28/100"** | A score with no measured basis is the LOW/MODERATE/HIGH problem with more decimal places. If a number is going to rank wallets, the ranking has to be measured first — and F-0012 is the evidence that this particular quantity cannot rank anything. |

**One correction accepted in full.** The homepage claimed *"Almost nothing near liquidation can
defend itself — across every scan we have taken."* Our scans see a third of open interest, from
the 300 largest positions, and F-0011 measured that this tier is **not** a random sample — it sits
further from liquidation than the full universe. The claim now says *"almost nothing **we can
see**"*, states the coverage inline, and says the sample is not random. Fixed 2026-08-22.

---

## 1. The four jobs

Every page belongs to exactly one. A page that serves two is a page that serves neither.

| job | the user's actual words | surface |
|---|---|---|
| **① Can I save my position?** | "how bad is it, and can I do anything" | `/check` |
| **② Where is the exposure?** | "what does the market look like right now" | `/markets/*` |
| **③ What does the evidence say?** | "is any of this real" | `/research/*` |
| **④ How often are you wrong?** | "why should I believe you" | `/record` |

`/methodology` and `/api` support all four and belong to none. Neither earns primary navigation.

## 2. Positioning — revised, and why

v1 said: *"Let the incumbents own liquidation maps. We own liquidation vulnerability."*

**That is no longer supportable as the whole banner.** F-0012 measured that vulnerability is
close to a constant, so it cannot be the thing a customer chooses between clusters with. It is
still true, still unique, still unbuyable elsewhere — it just cannot carry the product alone.

The honest banner is one level up:

> **Every liquidation map shows you where the exposure is.**
> **Isobath tells you what it can and cannot see, how much of it can defend itself, and how big
> it actually is against the book.**

Three legs instead of one, and the third is new:

| leg | measurement | can a competitor copy it? |
|---|---|---|
| **coverage stated** | F-0003 | yes, in a week — none has |
| **defensibility** | F-0001, needs `withdrawable`, which is **not derivable** | not without collecting it |
| **scale against the book** | F-0014 | yes, in a week — none has |
| **a public record of being wrong** | 14 claims, 2 self-refuted | **no.** It accrues only with time |

## 3. Page map

Each row is fixed before any styling. **"Not shown" is as binding as "shown."**

### `/` — the front door
- **Job:** route to ① or ②, and establish why anyone should trust either.
- **Primary question:** *what is this and can it help me right now?*
- **Primary action:** paste an address. One field, one button, above the fold.
- **Shown:** the check; the hero contours with their true-scale caption; the two things every map
  omits (defensibility, scale); the constant-vulnerability finding **with its coverage qualifier**;
  the record count.
- **Not shown:** the full ladder, per-cluster tables, any methodology detail beyond one link.
- **AEO:** `Dataset` JSON-LD carrying forced notional, defensibility, coverage, standing book.

### `/check` — job ①
- **Primary question:** *can I save this position?*
- **Shown now:** positions, liquidation price, distance, free collateral, whether it can defend.
- **Wanted, and BLOCKED — see F-0015.** *"Add $500 and your liquidation price moves to X"* is the
  right feature: decision support rather than a forecast, offered by nobody. The gate above was
  run on 2026-08-22 and **the feature failed it.** The documented formula reproduces the venue
  within 10 bps for 56.4% of positions, is internally inconsistent within a single account for
  71.8% of accounts, and the observed response does not match the predicted one.
  **It must be measured, not computed** — join real deposits from `userNonFundingLedgerUpdates`
  to `liquidationPx` before and after. That needs per-wallet state over time, which is the one
  asset competitors lack, and it needs a thicker archive than three days.
- **Until then `/check` ships the honest version of the same job:** what the venue reports, what
  free collateral it actually has, and *"we cannot yet tell you what adding margin would do, and
  here is why"* — with a link to F-0015. Saying so is more trustworthy than a number that is
  wrong for two positions in five.
- **Not shown:** a 0–100 score; any statement about where price will go.
- **Language:** the heading is **"Can you defend this position?"**, never "defensibility". The
  technical term lives in `/methodology`, the API, and nowhere else a trader reads.
- **AEO:** `WebApplication`, price 0, and a canonical shareable URL per address.

### `/markets/btc` — job ②
- **Primary question:** *where is forced exposure, and is any of it big enough to matter?*
- **Shown:** the headline defensibility answer; the book-scale bar; the ladder with `% of book`;
  coverage; what we cannot see.
- **Not shown:** forty cards. Seventeen numbers. A second chart that repeats the first.
- **AEO:** one indexable page per asset, server-rendered, `Dataset` JSON-LD, stable URL.

### `/research` and `/research/<slug>` — job ③
- **Primary question:** *is this real, and how would you know if it were not?*
- **Structure per finding, fixed:** Question → What we tested → What we found → **What would
  change our mind** → Data → Status.
- **"What would change our mind" is not a rhetorical flourish.** Every contract in `market/`
  already carries explicit kill conditions. Surfacing them is publishing something we have and
  nobody else does.
- **Not shown:** a publication date presented as freshness for a finding whose sample ended
  months earlier.

### `/record` — job ④
- **Primary question:** *how often are you wrong?*
- **Named `/record`, not `/scorecard`.** "Scorecard" implies a score, a score implies accuracy,
  and accuracy implies forecasts we do not make. The heading may read **"Track record"**; the
  route stays `/record` because the URL is already published and links to it exist.
- **Shown:** all 14 claims, status first, refutations never removed and never demoted.
- **Not shown:** an accuracy percentage. Ever. See §0.

### `/methodology`, `/api`
- Support surfaces. `/api` is job ⑤ in disguise — *give it to my agent* — and gets example
  responses, schema, freshness, coverage and provenance per endpoint.

### Answer pages — to be built
Question-shaped routes, each carrying **live Isobath data plus original measurement**, never
generic explainer text: what Hyperliquid liquidation risk is · how a liquidation price is
calculated · whether liquidation clusters move price (F-0010) · what free collateral is and why
the obvious formula fails (F-0001) · how big a liquidation cluster actually is (F-0014).

## 4. Navigation

```
Isobath        Markets   Check a wallet   Research   Record            API
```

`Methodology` moves to the footer — important, but nobody arrives to read it. **`Alerts` comes
out of primary navigation until the bot has been used by someone who is not us.** A half-built
surface in the top bar reads as an unfinished product, and it currently has zero users.

## 5. The number contract

Every published figure answers four questions, in this order, or it does not ship:

1. **What is it** — in the reader's words, not the schema's
2. **How was it measured** — the provenance badge: observed / calculated / estimated / historical
3. **How much of the market it covers** — this scan's coverage, never the best scan ever run
4. **How fresh** — age of the underlying scan, not the page build time

## 6. Provenance ladder

| tier | meaning | example |
|---|---|---|
| **observed** | read directly from the venue | liquidation price, `withdrawable`, standing book |
| **calculated** | arithmetic over observations | cluster notional, `% of book` inside the book's reach |
| **estimated** | a model with stated assumptions | full-universe coverage 53.3%; `% of book` beyond the book's reach |
| **historical** | measured over an archive | depth evaporation 0.8462 |

**`predicted` does not exist.** Nothing is shipped that would need it.

## 7. What we never do

- Publish a cascade magnitude (F-0010).
- Publish a risk rating or score without a measured basis.
- Publish an accuracy figure, because no predictions are made (F-0005).
- Show the full-universe estimate on a page whose data came from a narrower scan (F-0003).
- Call a cluster large without saying large against what (F-0014).
- Claim about "the market" what was measured on the 300 largest wallets (F-0011).
- Use a placeholder number anywhere.

## 8. Human and machine, one source

Each page is generated from the same JSON its data route serves. The page carries JSON-LD so an
agent retrieves the claim, its count, its timestamp, its coverage and its method without parsing
a chart. **The human sees the interpretation; the agent sees the structure. Neither is a
translation of the other written separately** — that is how they drift.

## 9. Design constraints

Depth palette, restrained colour, typography carrying hierarchy, one primary answer per screen,
progressive disclosure for the rest. Mobile first. Colour is semantic only: hazard, safe, depth.
No neon, no gradients, no terminal aesthetic, no wall of tiny charts. The metaphor is the name —
an isobath joins points of equal depth — and the visual language is soundings, contours and what
is under the surface, not red-and-green crypto.

**The differentiator is legibility.** Every competitor ships a docs site, a JSON blob, or a wall
of charts. None of them is readable.

## 10. Build order

1. ~~`/check` — "what would change this"~~ **BLOCKED by F-0015.** Do not ship a computed margin
   response. The replacement task is instrumentation: record deposits against liquidation prices
   until the response can be measured.
2. ~~Navigation and language pass~~ **DONE 2026-08-22.** Nav is the four jobs plus API set apart:
   Markets · Check a wallet · Research · Record | API. Alerts left the top bar and lives where it
   belongs — after a result on `/check` — and Methodology moved to the footer alongside the API
   and the findings JSON. The language audit found "defensibility" was *already* confined to
   methodology, the API and the research library; trader-facing copy said "nothing to defend
   with" throughout. The real gap was `/check` never mentioning what F-0015 blocked, and it now
   carries **What we cannot tell you yet**, shown only after a result.
3. **`/research/<slug>` restructured** to Question → Test → Result → **What would change our
   mind** → Data → Status, pulling kill conditions from the contracts that already hold them.
4. **Answer pages**, each one carrying live data and an original measurement.
5. **Instrumentation, then first contact.** Still zero users. **Still the thing that killed the
   last three products, and no amount of further design addresses it.**

**Steps 1–4 are worth roughly a week. Step 5 is the one that decides whether any of it mattered,
and it is blocked on registering `isobath.io`.**
