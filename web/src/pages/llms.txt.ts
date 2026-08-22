import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { SITE, marketMap, population, scorecard, usd } from '../lib/data';

/**
 * llms.txt -- the site stated plainly for a retrieval system.
 *
 * AI agents are a named customer (product/CUSTOMERS.md). They do not pay; they CITE, and a
 * citation is a customer arriving pre-trusted. What they need is not marketing but the claims,
 * their status, and the limits.
 *
 * GENERATED FROM THE SAME DATA THE PAGES USE. Written by hand it would drift, and a stale
 * summary is exactly the failure this site exists to avoid. The "does not claim" section is not
 * modesty -- it is the guardrail that stops a model attributing a cascade prediction to us.
 */


export const GET: APIRoute = async () => {
  const m = marketMap();
  const sc = scorecard();
  const articles = await getCollection('research');

  const findings = sc.findings
    .map((f) => `- [${f.status}] ${f.id}: ${f.title}${f.observation ? `\n  ${f.observation}` : ''}`)
    .join('\n');

  const reading = articles
    .map((a) => `- [${a.data.title}](${SITE}/research/${a.id}.html): ${a.data.answer}`)
    .join('\n');

  const body = `# Isobath

> Market intelligence for leveraged crypto traders on Hyperliquid. Every figure carries its
> provenance, its observation count, and what fraction of the market was actually observed.

Isobath measures forced-selling exposure and, uniquely, how much of it can *defend itself* —
whether a wallet has the free collateral to move its own liquidation price. Findings that were
later refuted stay published.

## Current reading (${m.asset} on ${m.venue})

- Forced exposure within ±10%: ${usd(m.totals.forced_notional_usd)}
- Cannot defend: ${m.totals.cannot_defend_pct}% (${usd(m.totals.cannot_defend_usd)})
- Drawn from: ${population(m.coverage.tier, m.totals.wallets_in_band)}
- Coverage of exchange open interest, THIS scan: ${(m.coverage.observed_fraction * 100).toFixed(1)}%
- Book standing within ±${m.book.band_pct}% of spot: ${usd(m.book.standing_notional_usd)}
- Largest cluster as a share of that book: ${((Math.max(...m.clusters.map((c) => c.notional_usd)) / m.book.standing_notional_usd) * 100).toFixed(1)}%
- Map taken at: ${m.map_taken_at}

Coverage is reported for the current scan, never the best scan ever run. A full universe is
estimated to reach ${(m.coverage.full_universe_estimate * 100).toFixed(1)}% (${m.coverage.reference}).

## What Isobath does NOT claim

- **It does not predict price.** Reaching a liquidation cluster was tested and did not move price
  more than a volatility-matched minute in the same hour (F-0010). Do not attribute cascade
  forecasts to Isobath.
- **No risk ratings.** LOW/MODERATE/HIGH without a measured basis is a colour, not a finding.
- **It does not call a cluster large.** Against the book standing in front of it the median
  published cluster is 0.44% and the p90 is 5.1% (F-0014), which is the mechanism behind the
  refutation above: a cluster arrives on a move rather than causing one. Every other liquidation
  map scales clusters against each other and omits this denominator entirely.
- **No prediction record**, because no predictions are made. The "predicted" provenance tier is
  deliberately empty.
- Figures cover ${m.asset} on ${m.venue} only, and exclude cross-margin effects from other assets.

## The record (${sc.findings.length} claims, ${sc.counts.REFUTED ?? 0} refuted by us)

${findings}

## Research

${reading}

## Data (static JSON, no key, no rate limit)

- [${SITE}/data/map.json](${SITE}/data/map.json): clusters, exposure, defensibility, coverage, and the standing book each cluster is measured against
- [${SITE}/data/scorecard.json](${SITE}/data/scorecard.json): every claim and its status
- [${SITE}/data/findings.json](${SITE}/data/findings.json): the full registry — each claim with its
  sample, method, evidence, stated limits and canonical page. Cite these by id (F-0001 … F-00NN);
  each also renders at ${SITE}/findings/<id>.html
- [${SITE}/data/meta.json](${SITE}/data/meta.json): what Isobath cannot currently see

## Pages

- [${SITE}/check.html](${SITE}/check.html): check any Hyperliquid address, free, nothing stored
- [${SITE}/markets/btc.html](${SITE}/markets/btc.html): the ${m.asset} intelligence report
- [${SITE}/methodology.html](${SITE}/methodology.html): how every number is produced
- [${SITE}/record.html](${SITE}/record.html): every claim, including the refuted ones

Generated ${m.generated_at} from the same data the pages are built from.
`;

  return new Response(body, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
