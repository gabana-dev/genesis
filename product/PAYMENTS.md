# Getting paid

**The paying wallet establishes initial product identity.** That is the whole design, and the
wording is deliberate — see §2 for why the shorter version of this sentence was wrong.

---

## 1. Why this product escapes a problem the previous two did not

Two earlier SaaS products were built for Kenyan SMEs and struggled on the same three frictions:
the customer was not accustomed to buying online, the payment rails did not reach them, and
accepting cards required a company, a bank account, a permit and a gateway relationship.

Isobath's customer is a leveraged perpetuals trader. They already transact online — it is their
entire activity. They already hold stablecoins, because that is what they trade with. They need
no card.

**This is a consequence of the customer, not a workaround.** The friction is selected out rather
than engineered around, which is the only durable way to remove it.

## 2. The mechanism, and the correction that matters

Hyperliquid publishes transfers. Verified against the live API:

```json
{"time": 1756818029018, "hash": "0x0387…",
 "delta": {"type": "internalTransfer", "usdc": "10.0",
           "user": "0xb83de…", "destination": "0xed0c…", "fee": "0.0"}}
```

Sender, destination, amount, timestamp, hash — from `userNonFundingLedgerUpdates`, the same
endpoint family the product already reads. A payment can be verified with one public call. No
processor, no webhook, no account creation, no password.

**The correction.** The first version of this design said *"payment is identity"*. That collapses
a commercial mechanism into the identity model, and it forecloses things a customer will want
almost immediately: pay from wallet A but watch wallet B, watch several wallets, hand a
subscription to a colleague, use an API key instead of a wallet.

The model is therefore three fields, not one:

```
subscription
  ├── payer_wallet          who paid
  ├── monitored_wallets[]   what we watch
  └── entitlements          what they get
```

`payer_wallet == monitored_wallets[0]` is the **default**, not a law. Getting this wrong costs
nothing to fix today and is painful to unpick once subscriptions exist.

## 3. What it costs — stated precisely

Not "zero". The correct claim is **near-zero marginal payment-processing cost relative to card
and merchant-of-record rails**.

| still a real cost | |
|---|---|
| reconciliation | matching payments to entitlements, and handling the ones that do not match |
| accounting and tax | Kenyan obligations do not change because the money arrived as USDC |
| treasury | converting or holding stablecoins is a decision with its own costs |
| support and abuse | underpayment, double payment, wrong-chain sends |

What genuinely goes away is the **per-transaction** cut. On a $15–30 ticket, a merchant of record
takes roughly 4–5% plus $0.40 — around 7% of revenue at the low end. That is the number this
avoids, and it is worth being exact about rather than rounding to "free". Precision is the
product's whole brand; the business plan does not get to be looser than the research.

## 4. The thing that only shows up if you know the product

**A subscription paid from the perp account reduces the number we sell.**

`withdrawable` — free collateral, the measurement this entire product is built on — is the
spendable balance of the perp account. USDC sent from there comes out of the same pool. So a
customer paying us from their trading balance makes their own position marginally more
defenceless, in exactly the units we alert them about. For a wallet already near zero, our own
alert could plausibly fire *because they paid us*.

At $29 against six-figure margin this is immaterial in size. It is not immaterial in principle:
a product whose bill is denominated in the resource it warns you about has an incentive problem
baked into its plumbing.

**So: take payment from the spot balance, not the perp balance.** Hyperliquid separates the two
and `accountClassTransfer` moves between them, so this is a matter of instruction, not
engineering. The payment page must say which account to send from.

*Inferred from the ledger's own account classes, not yet measured directly. Verify against a real
transfer before relying on it.*

## 5. What this does NOT solve

**B2B.** Desks, funds and HLP depositors — the segment with actual money — mostly cannot pay this
way. Procurement wants an invoice, an entity, a contract, tax forms. That is a wall.

It is also a wall reached *later*, which is the point. Crypto payment unblocks retail revenue now
at near-zero fixed cost. By the time a fund asks for an invoice, there is revenue to justify an
entity. **Do not buy the entity before the revenue.** A conventional rail — Polar supports Kenya
and supports individuals rather than only companies — is a fallback to evaluate *when someone
asks*, not before. Someone saying "I want this but cannot pay in USDC" is useful evidence; a
payment integration nobody requested is the trap that ate the last two products.

## 6. The two experiments

The point of this is not the payment architecture. It is that the architecture makes the first
honest commercial experiment cheap. Willingness to pay is the largest unknown in `PLAN.md` and no
amount of building reduces it.

### C-1 — will a crypto-native audience pay in stablecoins?

**Hypothesis.** A material share of target users will prefer paying in USDC because they already
operate inside a crypto-native financial environment.

**This is a hypothesis, not a fact.** An earlier draft asserted that a Hyperliquid trader "already
holds USDC" as though it were established. Funding paths vary — bridges, custodians, exchanges,
separate wallets — and the honest question is *what proportion of target users can and will pay
in USDC from a wallet we can observe*. Asserting a population fact without measuring it is the
error this project spends most of its effort avoiding, and it appeared here in a business
document because business documents felt exempt. They are not.

**Measure.** visitor → payment conversion; completion rate; time from intent to activation;
failed and mismatched payments; 7- and 30-day retention; renewal; wallets monitored per
subscriber.

**Falsification.** If users repeatedly ask for cards, invoices or conventional account flows
despite the audience, the wallet-native assumption is wrong and the fallback rail moves forward.

### C-2 — what do people actually use it for?

More important than C-1 and easier to skip. The question is not "do you like it" but **"what did
you use it for today?"**, with answers classified rather than summarised.

The plausible answers — liquidation proximity, whale positioning, liquidity conditions, "tell me
when my position becomes vulnerable" — imply materially different products. Building the
commercial layer heavily before this is answered is how the elegant parts get built and the
needed parts do not.

## 7. What we will not do with wallet identity

Knowing which wallet a customer holds makes personalisation possible, and that is where the
product could quietly betray its own evidence.

A personalised panel reading *"depth resilience: declining, position resilience: CONDITIONAL"*
looks like intelligence and is not. Depth resilience on Hyperliquid is **F-0006 — an ASSUMED
finding, unresolved**, with the `hl2` recorder still collecting to settle it. Publishing it as a
per-position readout would be selling an assumption as a measurement, to the one audience least
able to check.

The rule stands: **describe the environment and the position, never the action.** Personalisation
may only surface figures that already carry a provenance tier. If a field cannot say where it
came from, it does not go on the page — least of all a page addressed to one frightened person
about their own money.
