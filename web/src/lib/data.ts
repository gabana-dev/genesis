/**
 * Loading and formatting. Runs at build time only -- nothing here ships to the browser.
 *
 * THE VALIDATORS ARE THE POINT. TypeScript checks the code; it cannot check a JSON file the
 * Python engine wrote. So every field a page depends on is asserted here, and a mismatch fails
 * the build loudly. The alternative -- what the old generator did -- is a page that renders
 * `undefined%` and looks almost right.
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import type { MarketMap, Meta, Scorecard, Tier } from '../types/data';

const DATA = new URL('../../public/data/', import.meta.url);

function read(name: string): unknown {
  try {
    return JSON.parse(readFileSync(new URL(`${name}.json`, DATA), 'utf8'));
  } catch (e) {
    throw new Error(
      `Cannot read ${name}.json. The engine writes it: .venv/bin/python product/generate.py\n${e}`,
    );
  }
}

function need(obj: unknown, path: string, kind: 'number' | 'string' | 'array'): void {
  let cur: unknown = obj;
  for (const key of path.split('.')) {
    if (typeof cur !== 'object' || cur === null || !(key in cur)) {
      throw new Error(`data contract broken: ${path} is missing (product/generate.py)`);
    }
    cur = (cur as Record<string, unknown>)[key];
  }
  const ok = kind === 'array' ? Array.isArray(cur) : typeof cur === kind;
  if (!ok) {
    throw new Error(`data contract broken: ${path} should be ${kind}, got ${typeof cur}`);
  }
}

export function marketMap(): MarketMap {
  const d = read('map');
  for (const p of [
    'asset', 'venue', 'generated_at', 'map_taken_at', 'coverage.method', 'coverage.tier',
  ]) need(d, p, 'string');
  for (const p of [
    'map_age_seconds', 'spot_at_map', 'coverage.observed_fraction', 'coverage.wallets_scanned',
    'coverage.full_universe_estimate', 'totals.forced_notional_usd', 'totals.cannot_defend_usd',
    'totals.cannot_defend_pct', 'totals.wallets_in_band',
    'book.standing_notional_usd', 'book.band_pct', 'book.observable_reach_pct',
  ]) need(d, p, 'number');
  need(d, 'clusters', 'array');
  const m = d as MarketMap;
  if (m.clusters.length === 0) throw new Error('data contract broken: map has no clusters');
  return m;
}

export function scorecard(): Scorecard {
  const d = read('scorecard');
  need(d, 'findings', 'array');
  need(d, 'generated_at', 'string');
  const s = d as Scorecard;
  for (const f of s.findings) {
    if (!f.id || !f.title || !f.status) {
      throw new Error(`data contract broken: finding ${JSON.stringify(f).slice(0, 80)}`);
    }
  }
  return s;
}

export function meta(): Meta {
  const d = read('meta');
  need(d, 'what_we_cannot_see', 'array');
  return d as Meta;
}

/**
 * The Telegram bot's @name, from the private env file outside this repo.
 *
 * Until a bot exists there is nothing to link to, so the alerts page and its nav entry are not
 * generated at all. A storefront advertising a door that does not open is worse than no door.
 */
export function botHandle(): string {
  try {
    const env = readFileSync(
      fileURLToPath(new URL('alerts/env', `file://${process.env['HOME']}/genesis-private/`)),
      'utf8',
    );
    const line = env.split('\n').find((l) => l.startsWith('GENESIS_TG_BOT='));
    return line ? line.slice('GENESIS_TG_BOT='.length).trim().replace(/^@/, '') : '';
  } catch {
    return '';
  }
}

/**
 * An address to demonstrate the check with, read from the latest snapshot -- NEVER hardcoded.
 *
 * An earlier version hardcoded one reconstructed from a truncated log line, inventing 32
 * characters, and the page confidently reported "no open positions" for an address that does not
 * exist. Chosen mechanically: the largest position in the current scan with zero free collateral,
 * so the example always demonstrates the thing the product is about.
 */
export function liveExample(): string {
  try {
    const path = `${process.env['HOME']}/genesis-evidence/liqmap/snapshots-liq2.jsonl`;
    const lines = readFileSync(path, 'utf8').trimEnd().split('\n');
    const last = lines[lines.length - 1];
    if (!last) return '';
    const snap = JSON.parse(last) as {
      positions?: { wallet: string; withdrawable?: string | number; forced_notional?: number }[];
    };
    const trapped = (snap.positions ?? []).filter(
      (p) => Number(p.withdrawable ?? 0) <= 0 && p.forced_notional,
    );
    if (trapped.length === 0) return '';
    return trapped.reduce((a, b) => ((b.forced_notional ?? 0) > (a.forced_notional ?? 0) ? b : a))
      .wallet;
  } catch {
    return '';
  }
}

// -------------------------------------------------------------------------------------
// Formatting. Shared with the browser island, so keep it dependency-free.
// -------------------------------------------------------------------------------------
export function usd(n: number): string {
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `$${Math.round(n / 1e3)}k`;
  return `$${n.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
}

export function age(seconds: number): string {
  if (seconds < 90) return `${seconds}s`;
  if (seconds < 5400) return `${Math.round(seconds / 60)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

export function signed(n: number, digits = 2): string {
  return `${n > 0 ? '+' : ''}${n.toFixed(digits)}%`;
}

export const TIERS: Record<Tier, string> = {
  observed: 'read directly from the venue',
  calculated: 'arithmetic over observations',
  estimated: 'a model with stated assumptions',
  historical: 'measured over an archive',
};

/**
 * How to describe the population a figure was drawn from.
 *
 * F-0011: the hourly fast tier is the top 300 wallets by position notional, and those sit
 * FURTHER from liquidation than the full universe -- deep scans show median distance 15.5% and
 * 42.8% within 10%, against the fast tier's 31.6% and 23.0%. So an unqualified headline drawn
 * from the fast tier overstates how representative it is.
 *
 * Written once and used on every surface -- home page, map, social card, llms.txt, MCP -- because
 * a caveat that appears on one page and not another is worse than none: it looks like the
 * unqualified number is the reliable one.
 */
export function population(tier: string, wallets: number): string {
  return tier === 'fast'
    ? `${wallets} positions from the hourly scan of the 300 largest, which sit further from liquidation than the full universe (F-0011)`
    : `${wallets} positions from the full frozen universe`;
}

/** Resolve a site-root-relative path against the configured base. */
export function url(path: string): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  return `${base}/${path.replace(/^\//, '')}`;
}

/**
 * The site's absolute root, derived from astro.config.mjs -- never written out by hand.
 *
 * It appeared as a literal in seven places (JSON-LD, llms.txt, robots.txt, the research index),
 * which meant moving to a real domain later would be seven chances to leave one behind pointing
 * at a URL that no longer describes us. Changing `site` or `base` in the config now moves all of
 * them, and the only copy outside this build is product/alerts.py, which is noted there.
 */
export const SITE = new URL(import.meta.env.BASE_URL, import.meta.env.SITE).href.replace(/\/$/, '');

/** An absolute URL for a site-root-relative path. */
export function abs(path: string): string {
  return `${SITE}/${path.replace(/^\//, '')}`;
}
