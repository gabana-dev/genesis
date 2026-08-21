/**
 * The wallet check island -- the only JavaScript that ships to a visitor.
 *
 * It calls Hyperliquid directly from the browser: no server, no key, nothing stored, and it
 * scales without us. The exchange's responses are typed here because they are the one input this
 * page cannot control, and `szi` arriving as a string is exactly the kind of thing that silently
 * produced NaN in the untyped version.
 */

const API = 'https://api.hyperliquid.xyz/info';

/** Every numeric field on Hyperliquid's REST surface is a decimal string, not a number. */
type Decimal = string;

interface Position {
  coin: string;
  szi: Decimal;
  liquidationPx: Decimal | null;
  entryPx: Decimal | null;
  leverage?: { value?: number };
}

interface ClearinghouseState {
  marginSummary?: { accountValue?: Decimal; totalMarginUsed?: Decimal };
  withdrawable?: Decimal;
  assetPositions?: { position?: Position }[];
}

type AllMids = Record<string, Decimal>;

interface Row {
  coin: string;
  side: 'long' | 'short';
  liq: number;
  mid: number;
  dist: number;
  notional: number;
}

const $ = <T extends HTMLElement>(id: string): T => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`missing #${id}`);
  return el as T;
};

const usd = (n: number): string =>
  n >= 1e9 ? `$${(n / 1e9).toFixed(2)}B`
  : n >= 1e6 ? `$${(n / 1e6).toFixed(2)}M`
  : n >= 1e3 ? `$${(n / 1e3).toFixed(1)}k`
  : `$${n.toFixed(2)}`;

const num = (n: number, digits = 2): string =>
  n.toLocaleString(undefined, { maximumFractionDigits: digits });

async function post<T>(body: unknown): Promise<T> {
  const r = await fetch(API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`exchange returned ${r.status}`);
  return (await r.json()) as T;
}

function rows(st: ClearinghouseState, mids: AllMids): Row[] {
  return (st.assetPositions ?? [])
    .map((a) => a.position)
    .filter((p): p is Position => Boolean(p?.liquidationPx))
    .map((p): Row | null => {
      const mid = Number(mids[p.coin]);
      const liq = Number(p.liquidationPx);
      const szi = Number(p.szi);
      if (!mid || !liq || !szi) return null;
      // A LONG is liquidated by price FALLING to liq; a SHORT by price RISING to it.
      return {
        coin: p.coin,
        side: szi > 0 ? 'long' : 'short',
        liq,
        mid,
        dist: (Math.abs(mid - liq) / mid) * 100,
        notional: Math.abs(szi) * mid,
      };
    })
    .filter((r): r is Row => r !== null)
    .sort((a, b) => a.dist - b.dist);
}

function verdict(free: number, used: number): string {
  // Ratio of free collateral to what the exchange requires you to keep. Under 5% and topping up
  // moves the liquidation price by almost nothing.
  const cushion = used > 0 ? free / used : null;
  if (free <= 0) {
    return `<strong>There is nothing to defend with.</strong> Free collateral is zero, so the
      liquidation price cannot be moved without depositing from outside the account.`;
  }
  if (cushion !== null && cushion < 0.05) {
    return `<strong>Almost nothing to defend with.</strong> Free collateral is ${usd(free)} against
      ${usd(used)} of margin in use — topping up would move the liquidation price very little.`;
  }
  return `Free collateral is <strong>${usd(free)}</strong>${
    cushion !== null ? `, roughly ${(cushion * 100).toFixed(0)}% of margin in use` : ''
  }. There is room to push the liquidation price away.`;
}

function reveal(): void {
  $('explain').hidden = false;
  const cta = document.getElementById('alertcta');
  if (cta) cta.hidden = false;
}

function render(st: ClearinghouseState, mids: AllMids): void {
  const ms = st.marginSummary ?? {};
  const av = Number(ms.accountValue ?? 0);
  const used = Number(ms.totalMarginUsed ?? 0);
  const free = Number(st.withdrawable ?? 0);
  const pos = rows(st, mids);
  const out = $('out');

  if (pos.length === 0) {
    // NEVER say "nothing at risk" flatly. Hyperliquid's own docs call this a common pitfall:
    // querying an API/agent wallet returns an EMPTY result, because agent wallets authorise
    // trades but never hold positions. Telling someone with a position 2% from liquidation that
    // they are safe is the worst thing this product could do, so an empty answer has to name the
    // reason it might be wrong.
    const empty = av === 0 && used === 0;
    out.innerHTML = `<div class="answer"><div class="q">No open positions found</div>
      <div class="a calm" style="font-size:1.5rem;line-height:1.3">Nothing to report</div>
      <div class="s">Hyperliquid reports no leveraged positions with a liquidation price for this
      address right now.${
        empty
          ? `<br><br><strong>This account is empty, which has two possible meanings.</strong>
             Either it genuinely holds nothing, or it is an <strong>API / agent wallet</strong> —
             those authorise trades but never hold positions, so the exchange returns an empty
             result for them. If you use one, check the main account you deposit and trade with
             instead.`
          : ''
      }</div></div>`;
    reveal();
    return;
  }

  const worst = pos[0]!;
  const trapped = free <= 0;

  out.innerHTML = `
  <div class="answer">
    <div class="q">Closest liquidation — ${worst.coin} ${worst.side}</div>
    <div class="a ${worst.dist > 15 ? 'calm' : ''}">${worst.dist.toFixed(1)}%</div>
    <div class="s">${worst.coin} is at ${num(worst.mid)}. This position liquidates at
      <strong>${num(worst.liq)}</strong>.<br>${verdict(free, used)}</div>
    <div style="margin-top:.9rem"><span class="prov prov-observed">observed</span>
      <span class="prov-d">read live from Hyperliquid's clearinghouse ·
      ${new Date().toISOString().slice(0, 19)}Z</span></div>
  </div>

  <div class="grid">
    <div class="stat"><div class="k">Account value</div><div class="v">${usd(av)}</div></div>
    <div class="stat"><div class="k">Margin in use</div><div class="v">${usd(used)}</div></div>
    <div class="stat"><div class="k">Free collateral</div>
      <div class="v" style="color:${trapped ? 'var(--hot)' : 'inherit'}">${usd(free)}</div>
      <div class="n">${trapped ? 'cannot defend' : 'can be added to a position'}</div></div>
    <div class="stat"><div class="k">Open positions</div><div class="v">${pos.length}</div></div>
  </div>

  <h2>Every position</h2>
  <div class="scroll"><table>
    <thead><tr><th>Coin</th><th>Side</th><th>Size</th><th>Mark</th><th>Liquidates at</th>
      <th>Distance</th></tr></thead>
    <tbody>${pos
      .map(
        (p) => `<tr><td>${p.coin}</td>
        <td class="${p.side === 'long' ? 'buy' : 'sell'}">${p.side}</td>
        <td>${usd(p.notional)}</td><td>${num(p.mid, 4)}</td><td>${num(p.liq, 4)}</td>
        <td>${p.dist.toFixed(1)}%</td></tr>`,
      )
      .join('')}</tbody>
  </table></div>
  <p class="hint" style="margin-top:.6rem">A distance far above 100% is a position price would
  have to double to reach. The exchange still reports a liquidation price for it, so we show it
  rather than hide it.</p>`;
  reveal();
}

async function check(raw: string): Promise<void> {
  const addr = raw.trim().toLowerCase();
  const out = $('out');
  if (!/^0x[0-9a-f]{40}$/.test(addr)) {
    out.innerHTML = `<div class="note">That does not look like a Hyperliquid address.
      It should be <code>0x</code> followed by 40 hex characters.</div>`;
    return;
  }
  out.innerHTML = '<div class="answer"><div class="q">Reading the exchange…</div></div>';
  try {
    const [st, mids] = await Promise.all([
      post<ClearinghouseState>({ type: 'clearinghouseState', user: addr }),
      post<AllMids>({ type: 'allMids' }),
    ]);
    render(st, mids);
  } catch (e) {
    out.innerHTML = `<div class="note"><strong>Could not reach Hyperliquid.</strong>
      ${e instanceof Error ? e.message : 'unknown error'}. Nothing is cached — this page always
      reads live, so there is no stale answer to fall back on.</div>`;
  }
}

const input = $<HTMLInputElement>('addr');

$<HTMLFormElement>('f').addEventListener('submit', (e) => {
  e.preventDefault();
  void check(input.value);
});

const demo = document.getElementById('demo') as HTMLButtonElement | null;
if (demo?.dataset['address']) {
  demo.addEventListener('click', () => {
    const addr = demo.dataset['address']!;
    input.value = addr;
    void check(addr);
  });
}

const q = new URLSearchParams(location.search).get('a');
if (q) {
  input.value = q;
  void check(q);
}
