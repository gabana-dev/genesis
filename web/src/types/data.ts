/**
 * The contract between the Python engine and this site.
 *
 * `product/generate.py` writes these files; every page here reads them. Until now that boundary
 * was unchecked -- a renamed field in the engine produced a page that rendered wrong rather than
 * a build that failed. These types plus the validators in `lib/data.ts` close that hole.
 *
 * Keep in step with product/generate.py. If a field moves, this file is the second place to change
 * and the build will tell you if you forgot.
 */

/** The four tiers on the provenance ladder (product/IA.md). There is deliberately no `predicted`. */
export type Tier = 'observed' | 'calculated' | 'estimated' | 'historical';

/** A finding's lifecycle. REFUTED entries are never deleted -- see product/IA.md. */
export type Status = 'MEASURED' | 'PRELIMINARY' | 'ASSUMED' | 'REFUTED' | 'SUPERSEDED';

export interface Coverage {
  /** Scanned position notional / exchange open interest, for THIS scan. A lower bound. */
  observed_fraction: number;
  tier: string;
  wallets_scanned: number;
  method: string;
  note: string;
  /** What a full-universe scan is estimated to reach (F-0003). Never shown as this scan's figure. */
  full_universe_estimate: number;
  reference: string;
}

export interface Totals {
  wallets_with_positions: number;
  wallets_in_band: number;
  forced_notional_usd: number;
  cannot_defend_usd: number;
  cannot_defend_pct: number;
}

export interface Cluster {
  /** Signed distance from the map's spot, in percent. Negative is below. */
  distance_pct: number;
  price: number;
  side: 'buy' | 'sell';
  notional_usd: number;
  wallets: number;
  cannot_defend_pct: number;
  thinly_defended_pct: number;
}

/**
 * The liquidity a cluster would have to move. F-0014: the median published cluster is 0.44% of
 * this and the p90 is 5.1%, which is why reaching one moves price about a tenth as much as the
 * move it arrives on. Every other heatmap omits this number, and so did this one.
 */
export interface Book {
  /** Resting notional within `band_pct` of mid, both sides. */
  standing_notional_usd: number;
  band_pct: number;
  mid: number;
  /** How far the returned levels actually reach. Beyond this the book is not observable. */
  observable_reach_pct: number;
  source: string;
  note: string;
  reference: string;
}

export interface MarketMap {
  asset: string;
  venue: string;
  generated_at: string;
  map_taken_at: string;
  map_age_seconds: number;
  spot_at_map: number;
  coverage: Coverage;
  book: Book;
  totals: Totals;
  clusters: Cluster[];
  definitions: Record<string, string>;
  we_do_not_claim: string[];
}

export interface Finding {
  id: string;
  title: string;
  status: Status;
  observation: string | null;
  sample: string | null;
  method: string | null;
  confidence: string | null;
  first_recorded: string;
  last_updated: string;
}

export interface Scorecard {
  generated_at: string;
  note: string;
  counts: Partial<Record<Status, number>>;
  findings: Finding[];
}

export interface Meta {
  generated_at: string;
  what_we_cannot_see: string[];
  surfaces: unknown[];
}
