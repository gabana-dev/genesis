# The plan — what we build, in what order, and how each piece is found

**Genesis is the laboratory. The product is the instrument it built.** Genesis measures; the
product sells. This file is the ordered build, and every item carries its distribution surface,
because a feature nobody can discover is not shipped.

Written 2026-08-21, after an external strategic review. What that review could not see — it had
no access to this repo — is that roughly two thirds of what it recommended is already live. What
follows separates what is done from what is genuinely missing.

---

## 1. The one sentence

> **Every liquidation map shows you where the exposure is. We measure how much of it can actually
> defend itself.**

Let the incumbents own *liquidation maps*. We own *liquidation vulnerability*. Competing on
"a better map" is a fight against years of brand, traffic and exchange coverage. Creating an
adjacent category is not.

### Say vulnerability, not defensibility

**Defensibility is our mechanism. Vulnerability is the customer's outcome.** Nobody searches for
"position defensibility". The internal vocabulary stays — `cannot_defend_pct` is what the field
measures — but every customer-facing surface leads with what it means for them.

| we compute | we say |
|---|---|
| `cannot_defend_pct` = 92.2% | **$64.8M of $70.3M is vulnerable** |
| zero `withdrawable` | **nothing left to defend with** |
| coverage 25.4% | **we can see a quarter of the market, and we say so** |

## 2. The asset that compounds — start it now

Everything else on this page can be copied. A competitor can clone the map, the wallet check, the
copy, the design, in a fortnight.

**What cannot be copied is a record of our own calls against what subsequently happened.**

```
we say a cluster is highly vulnerable
            │
            ▼
   the market resolves it, or does not
            │
            ▼
   we record which, publicly, including when we were wrong
            │
            ▼
   after six months: "of clusters we called highly vulnerable, N% were
   subsequently reduced" -- a number nobody else has
```

That dataset only accrues with **time**, and it starts accruing the day we begin recording, not
the day the product is polished. **Every day we do not record is a day of moat not built.**

This is also the honest way to earn the right to make stronger claims later. CASCADE-1 (F-0010)
found forced flow does not move price more than a volatility-matched minute, so we do not sell
prediction. If calibration eventually shows vulnerability *does* anticipate resolution, that
finding will be ours and it will be earned. Not before.

**Status: not started. Highest priority after the current build.**

## 3. Distribution is architecture, not a later phase

The rule that keeps marketing from becoming a separate job:

> **One measurement, four surfaces, generated from one source.**

```
        a measurement in the engine
                    │
    ┌───────────┬───┴────────┬─────────────┐
    ▼           ▼            ▼             ▼
  a page      JSON       llms.txt      an MCP tool
 (search)   (machines)  (retrieval)     (agents)
```

This is already how the site works — `generate.py` writes JSON, every page is built from it, and
`llms.txt` and the JSON-LD are generated from the same data so they cannot drift. **The
discipline to keep: nothing is added to the product that does not automatically produce all four.**
The day a number exists on a page but not in the JSON, marketing has become a separate job again.

## 4. What is already live

| the review recommended | status |
|---|---|
| make the scorecard a first-class product | **live** — `/record.html`, 10 claims, 2 refuted by us |
| publish the failures, including CASCADE-1 | **live** — it is a research article |
| alerts may matter more than the dashboard | **live** — Telegram bot, two rules |
| Telegram as a distribution channel | **live** |
| make coverage impossible to ignore | **live** — every figure carries coverage and a provenance tier |
| expose structured, crawlable data | **live** — JSON-LD on 13/13 pages, `llms.txt`, static JSON |
| be careful with prediction | **enforced** — the `predicted` tier is a TypeScript union member that does not exist |

## 5. What is genuinely missing

### 5.1 Search pages — the biggest gap

We rank for nothing. There is exactly **one** market page. The queries that exist are
`BTC liquidation map`, `Hyperliquid liquidation heatmap`, `BTC liquidation levels` — and we
answer none of them by name.

Programmatic pages per asset and per question, **each with a real analytical answer**, never thin
pages generated for their own sake. The test for whether a page deserves to exist: it states a
number, its coverage, and when it changed.

Blocked on one thing: the scanner covers BTC only. **Extending the scanner to ETH and SOL is
therefore a distribution task, not a data task** — that is the reframe.

### 5.2 MCP — agents are a channel, not a feature

An agent asking `get_vulnerable_clusters(asset="BTC")` and getting a structured answer is
distribution: the product becomes a source other software depends on rather than a page competing
for screen space. 0xArchive already ships MCP, CLI and skills; this is where developer discovery
is going.

Cheap to build — it is a thin wrapper over JSON that already exists — and it is the direct answer
to "the platform must be open to agents doing the work".

### 5.3 The shareable artifact

A trader screenshotting a chart into a group chat is how the incumbents got their reach. We
generate nothing designed to be shared. An image or card per alert, carrying the number, the
coverage and the URL.

### 5.4 Willingness to pay — unproven

Nothing here has been paid for by anyone. That is the single largest open risk and no amount of
building reduces it. The first paid trigger has to be discovered from behaviour, not designed.

## 6. Order of work

Each line names what it is for. Anything that cannot state its distribution surface does not get
built.

| # | build | why now | surface |
|---|---|---|---|
| 1 | **calibration recording** | the only compounding asset; every day costs a day | record → scorecard |
| 2 | **ETH + SOL in the scanner** | unblocks every search page | pages, JSON, llms.txt, MCP |
| 3 | **per-asset search pages** | the queries already exist and we answer none | search |
| 4 | **MCP server** | agents as a channel; thin wrapper over existing JSON | agents |
| 5 | **shareable alert cards** | the incumbents' organic reach mechanism | social |
| 6 | **paid tier** | only after 1–5 produce returning users | revenue |

**The API is deliberately not a milestone.** Static JSON already exists and costs nothing; a
documented, supported, rate-limited API is a product with an obligation attached, and it waits
until someone is asking for it.

## 7. What we will not do

- **Not "an AI-powered crypto trading intelligence platform."** There are thousands. AI stays
  under the hood; the product is about vulnerability. Agents are a distribution channel, not a
  positioning.
- **Not execution.** Taking a fee per trade means the product earns when the customer trades,
  which is a different and worse incentive than earning when the customer is well informed.
- **Not a better map.** That is the fight we cannot win and do not need.
- **Not prediction**, until calibration earns it.

## 8. The honest risk

The failure mode is not technical. It is **an intellectually interesting product nobody urgently
needs**. The counter is in §3 and §6: build nothing whose distribution surface cannot be named,
and start the calibration record now so that in six months there is something true to say that
nobody else can say.
