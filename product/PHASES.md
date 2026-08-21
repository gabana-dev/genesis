# Phases

Everything outstanding, ordered by what unblocks what. Each phase has a **gate** — the thing that
must be true to leave it — because a phase without a gate is a list, and lists get half-done.

The ordering embeds one claim worth arguing with: **correctness and design come before traffic.**
Sending people to a page whose headline carries an unstated caveat, or that looks like a hobby
project, spends the scarcest thing we have — first impressions — on a version we already know is
wrong. Traffic can be got again; a trader who dismissed us once is gone.

Research runs as a **parallel track**, not a phase. It has its own clock and does not wait.

---

## Phase 0 — Close the open gates

**Goal:** stop the two things that get more expensive every day.
**Gate:** the token is rotated and the domain is decided.
**Owner: Gabana.** Neither is something I can do.

| | why it cannot wait much longer |
|---|---|
| rotate the bot token | it is in a chat transcript; today it guards one subscriber, and the cost of rotating rises the moment a stranger subscribes |
| decide `isobath.io` | every crawl and citation from here builds equity for a `github.io` path, and a 301 recovers most of it but never all |

Neither blocks building. Both block **Phase 3**, which is the point of everything else.

## Phase 1 — Make the live numbers honest

**Goal:** nothing on a public page states more than it has earned.
**Gate:** every headline figure carries the population it came from, and the calibration record
has a contract before it has enough data to tempt a conclusion.

- **F-0011 on the front page.** The map now names its scan tier, but the home page headline and
  the OG card quote the same figure with no caveat at all. `96.8% cannot defend` is *among the
  300 largest positions*, which sit further from liquidation than the full population. The
  headline is currently the least qualified number on the site and the most seen.
- **The calibration contract.** Recording is running; nothing states what would have to be true
  for it to mean anything. Write the kill conditions **before** the data is suggestive — the
  variance problem found on day one (71% of clusters at exactly 100%) means the obvious question
  may be unanswerable as framed, and that has to be settled in advance rather than discovered
  while staring at a result.
- **Resolve the ETH/SOL question.** The first multi-asset deep scan decides whether their empty
  maps are our population or the market's. Publish per-asset pages, or write down why not.

## Phase 2 — Make it worth arriving at

**Goal:** a trader who lands has a reason to trust it and a reason to come back.
**Gate:** Gabana is content with the design, and the landing page answers *why you* before it
asks for an address.

- **The design pass.** Currently a research instrument's aesthetic, not a considered identity.
  The question to answer is not "make it prettier" but **what the eye should do, in what order,
  in ten seconds on a phone.** The map is where this matters most: the number, the wall and the
  hollow currently compete rather than sequence.
- **The trust gap.** A stranger has no idea who we are or why our number beats the map they
  already use. One checkable claim, early.
- **A reason to return.** Everything today is a one-shot lookup except alerts, which nobody
  knows exist.

## Phase 3 — First contact

**Goal:** find out what people actually use it for.
**Gate:** ten strangers have used it and we can say, from data rather than impression, what for.

- **Instrumentation first.** We cannot answer C-2 — *what did you use it for today?* — because
  nothing is measured. No analytics of any kind. Privacy-respecting, self-hosted, no third-party
  script; the alert bot's own logs already answer part of it.
- **Submit for indexing.** Google, Bing, IndexNow. Deliberately after Phase 0, so the equity
  lands on the right domain.
- **Post it somewhere traders are.** One place, once, and watch.

**This phase generates the only genuinely new information left.** Every item after it is a guess
until it is done.

## Phase 4 — Revenue

**Goal:** find out whether anyone pays, at the smallest possible cost.
**Gate:** one stranger has paid, or enough have declined to say why.

- **Wallet-native payment** (`product/PAYMENTS.md`): entitlements keyed on payer wallet, verified
  on-chain, no processor and no company. Payment instructions must specify the **spot** balance —
  a subscription paid from the perp account reduces the exact quantity we measure.
- **C-1** — will a crypto-native audience pay in stablecoins? Hypothesis, not assumption.
- **A conventional rail only when someone asks.** Polar supports Kenya and individuals. Building
  it before the request is the trap that ate the last two products.

## Phase 5 — Depth

**Goal:** the things that are only worth building once demand is proven.
**Gate:** none — this phase is entered by evidence from Phase 3 and 4, not by finishing Phase 4.

- Per-asset and per-question search pages, if Phase 1 justified them
- Wider wallet universe, if coverage turns out to be what limits the product
- The API as a supported product, when someone is asking for it
- B2B: entity, invoicing, contracts — only against a named customer

---

## Parallel track — research

Does not wait for any phase, and has dates attached that we do not control.

| | when | what it settles |
|---|---|---|
| **F-0006** | as `hl2` accumulates | whether Binance depth physics transfers to Hyperliquid — the evaporation finding rests on it |
| **COND-1** | q5 closes ~25 Aug | the recording is already running |
| **F-0009, F-0011** | more samples | both PRELIMINARY; one sample is a coincidence |
| **ECON-1** | first read ~mid-Nov | already known underpowered |
| **FADE-1** | blocked on a decision | needs ~900 more harvested wallets, about 8 hours of recording |

---

## What this ordering assumes

**That the product is closer to done than the business.** Six phases and most of the remaining
work is not code. If that reads wrong — if the honest answer is that the product is not good
enough to show anyone yet — then Phase 2 is larger than written here and should be said so
plainly rather than discovered during Phase 3.
