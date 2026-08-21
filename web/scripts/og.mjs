/**
 * Generate the Open Graph card.
 *
 * WHY THIS EXISTS. A link to this site currently renders in Telegram, X and Discord as a bare
 * URL: no title, no number, nothing. The alert bot sends links all day, and every one of them is
 * a wasted impression. A trader screenshotting a chart into a group chat is how the incumbents
 * built their reach; we generate nothing designed to travel.
 *
 * Hand-written SVG rasterised with sharp, which Astro already ships -- no new dependency, and no
 * headless browser. The card carries the live number AND its coverage, because a figure without
 * its coverage is exactly what this product exists not to publish. That rule does not get
 * suspended because the surface is social.
 */
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const ROOT = new URL('../', import.meta.url);
const map = JSON.parse(readFileSync(new URL('public/data/map.json', ROOT), 'utf8'));

const usd = (n) =>
  n >= 1e9 ? `$${(n / 1e9).toFixed(2)}B`
  : n >= 1e6 ? `$${(n / 1e6).toFixed(1)}M`
  : `$${Math.round(n / 1e3)}k`;

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const t = map.totals;
const cov = Math.round(map.coverage.observed_fraction * 100);

// 1200x630 is the size every platform crops to. Anything important stays well inside it.
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630">
  <rect width="1200" height="630" fill="#14130f"/>
  <rect x="0" y="0" width="1200" height="6" fill="#d9705a"/>

  <text x="80" y="118" font-family="Iowan Old Style,Palatino,Georgia,serif" font-size="42"
        font-weight="600" fill="#ece8dc">Isobath</text>
  <text x="80" y="158" font-family="Helvetica,Arial,sans-serif" font-size="21" fill="#726d61">
    how much water you have left</text>

  <text x="80" y="270" font-family="Helvetica,Arial,sans-serif" font-size="23"
        letter-spacing="3" fill="#a8a294">CANNOT DEFEND THEIR POSITION</text>

  <text x="80" y="420" font-family="Menlo,monospace" font-size="150" font-weight="600"
        fill="#d9705a">${t.cannot_defend_pct}%</text>

  <text x="80" y="486" font-family="Helvetica,Arial,sans-serif" font-size="30" fill="#ece8dc">
    ${esc(usd(t.cannot_defend_usd))} of ${esc(usd(t.forced_notional_usd))} in BTC forced exposure</text>
  <text x="80" y="528" font-family="Helvetica,Arial,sans-serif" font-size="30" fill="#ece8dc">
    sits with wallets holding zero free collateral.</text>

  <line x1="80" y1="562" x2="1120" y2="562" stroke="#2e2b23" stroke-width="1"/>
  <text x="80" y="596" font-family="Menlo,monospace" font-size="20" fill="#726d61">
    ${t.wallets_in_band} positions observed · ${cov}% of open interest · read from Hyperliquid</text>
</svg>`;

const out = fileURLToPath(new URL('public/og.png', ROOT));
mkdirSync(fileURLToPath(new URL('public/', ROOT)), { recursive: true });
const buf = await sharp(Buffer.from(svg)).png({ compressionLevel: 9 }).toBuffer();

// A blank card is worse than none: it looks broken rather than absent. sharp silently produces a
// flat image if the SVG fails to rasterise, so the build refuses rather than shipping it.
const stats = await sharp(buf).stats();
const spread = stats.channels[0].max - stats.channels[0].min;
if (spread < 50) {
  throw new Error(`og.png rasterised blank (tonal spread ${spread}) - text did not render`);
}

writeFileSync(out, buf);
console.log(`og.png  ${(buf.length / 1024).toFixed(0)} KB  ${t.cannot_defend_pct}% · ${cov}% coverage`);
