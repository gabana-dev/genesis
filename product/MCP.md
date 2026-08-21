# Isobath as an MCP server

**Agents are a distribution channel, not a feature.** They do not pay; they cite, and a citation
is a customer arriving pre-trusted. A page competes for screen space against every other
dashboard. A tool an agent depends on is much harder to displace.

## Install

```sh
claude mcp add isobath -- python3 /path/to/genesis/product/mcp_server.py
```

Stdlib only, no install step, no API key, no account. It reads the same public JSON the site is
built from, so it is never a different number than the page shows.

## The four tools

| tool | answers |
|---|---|
| `get_market_map` | where forced selling sits, and how much of it is vulnerable |
| `check_wallet` | how close one address is, and whether it can defend itself |
| `get_findings` | every claim, including the ones we refuted ourselves |
| `get_limits` | what Isobath cannot see and does not claim |

## The rule that makes this different from a JSON dump

**Every response carries its coverage and its provenance tier.**

A model quoting `96.8% vulnerable` to a third party without `30.5% of open interest observed` has
turned a measurement into a claim. That is the failure this product exists to avoid, and an agent
relaying our number to someone who will never visit the site is where it does the most damage. So
coverage is not an optional field, and the tests treat a missing one as a failure.

`get_limits` exists for the same reason. It names the cascade refutation (F-0010) and the empty
`predicted` tier explicitly, so an agent about to attribute a forecast to us has something to
read that says we make none.

## Two failure modes handled deliberately

**An unreachable source returns an error, not empty data.** A model handed `{}` will summarise it
as "no risk found". The response sets `isError` and says nothing was cached.

**An empty wallet result carries a warning.** Hyperliquid returns nothing for an API/agent wallet,
because those authorise trades but never hold positions. Without the warning an agent would tell
someone with a position 2% from liquidation that they are safe.

## Status

Not published to a registry, and deliberately local-first: a remote MCP endpoint needs a domain
and hosting, and neither is settled. The protocol is hand-rolled JSON-RPC over stdio rather than
the SDK — initialize, tools/list, tools/call and two notifications is small enough that a
dependency would cost more than it saves.
