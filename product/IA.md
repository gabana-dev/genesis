# Genesis — information architecture

**Principle: answer the question before showing the data.**

A trader should not need to understand liquidation mechanics, margin, or our methodology to use
Genesis. They should open it and know whether there is danger, how much, and how much of the
market we can actually see.

---

## The six questions the product answers

| question | surface | status |
|---|---|---|
| Where is the forced selling? | market page | **built** |
| How much is there? | market page | **built** |
| How defensible is it? | market page — **the unique one** | **built** |
| How much can Genesis see? | everywhere, always | **built** |
| What happens if it is reached? | research | **answered: no evidence it moves price (F-0010)** |
| How often has Genesis been wrong? | record | **built — 2 of 10 refuted** |

The fifth answer is a negative one. That is not a gap to fill later with a forecast; **it is the
finding**, and no competitor publishes it.

## Routes

Every route is a real indexable page, generated from the same JSON the API serves. One source of
truth — never an SEO page written separately from the data.

```
/                         overview: assets, headline risk figures, what we cannot see
/markets/btc              the intelligence report for one asset
/research                 evidence library index
/research/<slug>          one finding, written out with method and limits
/record                   every claim published, including refutations
/methodology              how each number is produced
/methodology/<concept>    defensibility, coverage, evaporation, episodes
/api                      the machine surface
/data/*.json              the machine surface itself
```

## Provenance ladder — shown on every number

Adopted because "71%" alone is a claim and "71%, from 43 observed positions, 46 minutes old,
covering 25% of open interest" is a measurement.

| tier | meaning | example |
|---|---|---|
| **observed** | read directly from the venue | liquidation price, `withdrawable` |
| **calculated** | arithmetic over observations | cluster notional, defensibility |
| **estimated** | a model with stated assumptions | full-universe coverage 53.3% |
| **historical** | measured over an archive | depth evaporation 0.8462 |

Anything that would be **predicted** is not shipped. That tier is empty on purpose.

## What we never do

- Publish a cascade magnitude. F-0010 found forced flow does not beat a volatility-matched
  minute, and a range would be selling what we disproved.
- Publish a risk rating without a measured basis. LOW/MODERATE/HIGH is a colour, not a finding.
- Publish a prediction count before making predictions.
- Show the full-universe coverage estimate on a page whose data came from a narrower scan.
- Use a placeholder number anywhere. Four external documents have now built on mockup figures
  that were mistaken for findings.

## Human and machine, one source

Each page is generated from the same JSON its API route serves. The page carries JSON-LD so an
agent can retrieve the claim, its observation count, its timestamp, its coverage and its method
without parsing a chart.

## Design constraints

Warm paper, restrained colour, typography carrying the hierarchy, one primary answer per screen,
progressive disclosure for the rest. Mobile first — the situation should be legible in ten
seconds on a phone. No neon, no gradients, no terminal aesthetic, no wall of tiny charts.

**The differentiator is legibility.** Every competitor ships a docs site, a JSON blob, or a wall
of charts. None of them is readable.

## Positioning

> **Genesis — market intelligence for leveraged crypto traders.**
> See the risk behind the liquidation map.

Deliberately not "a liquidation intelligence service": today it is liquidation and defensibility,
and the same engine extends to positioning, crowding, funding and liquidity risk without
rebranding.
