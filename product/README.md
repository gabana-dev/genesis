# Genesis v1

Static surfaces. `product/generate.py` writes JSON into `public/data/`; `public/index.html`
reads it. No server, no database, no build step.

    .venv/bin/python product/generate.py     # regenerate
    cd public && python3 -m http.server 8787 # preview

## Why static

A generated file on a CDN cannot go down, costs nothing to serve and needs no ops. Build a
service only when someone asks a question that cannot be precomputed.

## What the page says that no competitor's does

**Coverage, on the map itself.** This snapshot's own figure -- 25% on a fast-tier scan -- not the
53.3% a full universe reaches (F-0003). Publishing the better number would be exactly the
dishonesty this surface exists to avoid.

**Defensibility.** The share of each cluster held by wallets with zero free collateral. Requires
`withdrawable`, which no surveyed provider sells and which is not derivable (F-0001).

**Map age.** The position scan lags the live book by up to an hour (F-0008). Every other product
presents its map as current.

**A record.** Ten published claims, two of them refuted by us, generated from `findings/` and
never hand-edited.

## What it refuses to claim

Nothing here forecasts price. CASCADE-1 found forced flow does not move price more than a
volatility-matched minute on Binance (F-0010). The page says so in the body, above the fold.
