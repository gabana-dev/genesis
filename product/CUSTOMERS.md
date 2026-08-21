# Who this is for, and what we have been getting wrong

**Genesis is the engine. The product is something else, and it is not built for us.**

---

## The mistake in what we have shipped

The site currently leads with `99.7% cannot defend`, a coverage figure, a methodology page and a
record of our own refutations.

**That is our value system, not a customer's.** It is a research lab being proud in public.

A leveraged trader does not wake up wanting epistemics. They wake up wanting to know whether
they are about to be liquidated. We have built a beautiful answer to a question nobody asked.

**Honesty is a trust mechanism, not the product.** It must be visible and subordinate — the thing
that makes them believe the number, never the thing on the marquee.

## The four customers, and what each actually wants

### 1. The leveraged trader — traffic, urgency, virality

**Their question is not "how vulnerable is the market". It is "how vulnerable am I".**

They visit when price moves against them. They are frightened, on a phone, and have ten seconds.
They do not care what fraction of open interest we observe until they have a reason to trust us.

| they want | we currently give them |
|---|---|
| *am I close to being liquidated?* | a market-wide aggregate |
| *is there a wall under me that drags me in?* | a table sorted by distance |
| *can I get out, or am I trapped?* | the answer, but about strangers |
| *tell me before it matters* | nothing |

**The gap is personal.** Everything we compute about the market, we can compute about *their
wallet* — the venue publishes it, free, per address.

**Revenue: low per head, high volume, and the only surface that spreads.** "Check your
liquidation risk" is a thing people send each other. A market aggregate is not.

### 2. The watcher — attention, no money

Wants to see what whales are doing. Entertainment with a signal attached. Served by Hyperdash
and ASXN. High traffic, near-zero willingness to pay.

**Worth serving only because it feeds the funnel**, never as the product.

### 3. B2B — quant desks, market makers, HLP depositors — the revenue

The only segment that pays real money, and **the only one that cares about what we are already
good at**: coverage, methodology, provenance, history, an honest record.

They need an API, stated limits, and a reason to trust the numbers. Everything the trader ignores
is what closes this sale.

**HLP depositors are underserved and directly exposed**: the vault takes the other side of every
liquidation, and nobody sells them a view of what they are absorbing.

### 4. AI agents — distribution, not revenue

They do not pay. They **cite**, and a citation is a customer arriving pre-trusted.

They need structured, timestamped, method-carrying answers. We have that already. It costs
nothing to keep and compounds.

## The system this implies

```
research  ──►  citations + search  ──►  free wallet check  ──►  alerts  ──►  API
(trust)        (distribution)          (traffic, viral)       (retail $)   (B2B $$)
```

Each stage feeds the next and each is useless alone. Research with no product is a blog. A
product with no research is another dashboard nobody trusts.

**Every layer is powered by one engine and one source of truth.** That is the structural argument
for keeping Genesis separate from the product: Genesis measures, the product sells.

## What this changes in the build

**The front door becomes a wallet check.** Paste an address, see *your* position, *your*
liquidation price, *your* free collateral, and whether you sit inside a cluster. Free, no signup,
instantly shareable.

We can build it today — `clearinghouseState` is public and per-address, and it is the same call
the scanner already makes 300 times an hour.

**The market view becomes context, not the headline.** It is what you see *after* your own
answer, or when you arrive without a wallet.

**Trust moves below the fold.** Coverage, provenance and the record stay on every page — they are
why the number is believable — but they stop being the first thing a frightened person reads.

**The research stays public and loud.** It is the top of the funnel and the reason a B2B buyer
takes a call.

## Design, in systems

Every screen answers **one question for one persona**, and the hierarchy follows their urgency
rather than our pride.

| layer | job | who reads it |
|---|---|---|
| the answer | one number, one sentence | trader, in ten seconds |
| the context | how it compares, what sits nearby | trader, once calm |
| the provenance | observation count, age, coverage | B2B, and anyone deciding to trust us |
| the method | how it is computed, what it cannot show | B2B, agents, sceptics |

**Progressive disclosure is not a style choice — it is the funnel expressed as layout.** The
trader stops at layer one. The buyer reads all four. The agent parses layers three and four
directly.

## The commercial shape

| | who | what they pay for |
|---|---|---|
| **free** | trader, watcher, agent | wallet check, market view, research |
| **alerts** | trader | being told *before* it matters — the only thing they will pay for |
| **API** | B2B | coverage, history, structured answers, stated limits |
| **data** | funds, desks | derived datasets and custom work |

**Alerts are the retail conversion, not the dashboard.** Nobody pays to look at a page. They pay
to be told something while they are asleep.

## Language: vulnerability, not defensibility

**Defensibility is our analytical mechanism. Vulnerability is the customer's outcome.** Nobody
wakes up and searches for "position defensibility"; they want to know how much of a wall is real.

The internal vocabulary does not change -- `cannot_defend_pct` is precisely what the field
measures, and renaming a measured quantity to suit marketing is how numbers start drifting from
what they mean. What changes is every customer-facing sentence: lead with what it means for them,
and let the mechanism be the explanation underneath.

## What we must stop doing

- Leading with what impresses us
- Treating the market aggregate as the product
- Assuming the trader will read the methodology before trusting the number
- Building surfaces before knowing which persona they serve
