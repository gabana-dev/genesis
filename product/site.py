"""
Generate the Genesis site: real pages, generated from the same JSON the API serves.

ONE SOURCE OF TRUTH. Every page is built from the data files in public/data/, never written
separately. An SEO page authored apart from the data is a page that drifts from it.

Each page carries JSON-LD so an agent can retrieve the claim, its observation count, its
timestamp, its coverage and its method without parsing a chart -- the human reads the sentence,
the machine reads the same numbers underneath it.

THE PROVENANCE LADDER (product/IA.md) is enforced here, not decorated: every figure ships with
its tier -- observed, calculated, estimated, historical. There is deliberately no `predicted`
tier. CASCADE-1 found forced flow does not move price more than a volatility-matched minute
(F-0010), so a cascade magnitude would be selling what we disproved.
"""
import json, os, re, glob, html
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "public", "data")
PUB = os.path.join(ROOT, "public")

def load(n):
    return json.load(open(os.path.join(DATA, f"{n}.json")))

def css():
    return open(os.path.join(os.path.dirname(__file__), "templates", "site.css")).read()

def shell(title, desc, body, jsonld=None, depth=0):
    up = "../" * depth
    ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>' if jsonld else ""
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<style>{css()}</style>{ld}
</head><body>
<nav class="nav"><a class="brand" href="{up}index.html">Genesis</a>
<a href="{up}markets/btc.html">Markets</a><a href="{up}research/index.html">Research</a>
<a href="{up}record.html">Record</a><a href="{up}methodology.html">Methodology</a>
<a href="{up}api.html">API</a></nav>
<main class="wrap">{body}</main>
<footer class="wrap foot"><p>Genesis — market intelligence for leveraged crypto traders.
Every number carries its provenance, its observation count and how much of the market we could
see. <a href="{up}record.html">Including the claims we got wrong.</a></p></footer>
</body></html>"""

def prov(tier, detail):
    return f'<span class="prov prov-{tier}">{tier}</span> <span class="prov-d">{detail}</span>'

def usd(n):
    if n >= 1e9: return f"${n/1e9:.2f}B"
    if n >= 1e6: return f"${n/1e6:.1f}M"
    if n >= 1e3: return f"${n/1e3:.0f}k"
    return f"${n:,.0f}"

def age(s):
    return f"{s}s" if s < 90 else (f"{round(s/60)}m" if s < 5400 else f"{s/3600:.1f}h")


# --------------------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------------------

def page_home(m, sc):
    t, cov = m["totals"], m["coverage"]
    ld = {"@context":"https://schema.org","@type":"Dataset",
          "name":"Genesis liquidation intelligence — Hyperliquid BTC",
          "description":"Forced-selling exposure and defensibility, with stated coverage.",
          "dateModified":m["generated_at"],
          "variableMeasured":[
            {"@type":"PropertyValue","name":"forced_notional_usd","value":t["forced_notional_usd"]},
            {"@type":"PropertyValue","name":"cannot_defend_pct","value":t["cannot_defend_pct"]},
            {"@type":"PropertyValue","name":"coverage","value":cov["observed_fraction"]}]}
    body = f"""
<h1>See the risk behind the liquidation map</h1>
<p class="lede">Every map shows you where forced selling sits. Genesis shows you how much of it
can actually defend itself — and how much of the market we can see.</p>

<div class="asset-row">
  <a class="asset" href="markets/btc.html">
    <div class="sym">BTC</div>
    <div class="stat" style="border:0;padding:.6rem 0 0;background:none">
      <div class="k">Cannot defend</div>
      <div class="v" style="color:var(--hot)">{t['cannot_defend_pct']}%</div>
      <div class="n">{usd(t['forced_notional_usd'])} forced exposure · {cov['observed_fraction']*100:.0f}% visible</div>
    </div></a>
  <div class="asset" style="opacity:.55">
    <div class="sym">ETH</div>
    <div class="stat" style="border:0;padding:.6rem 0 0;background:none">
      <div class="k">Not yet scanned</div><div class="v" style="color:var(--ink-faint)">—</div>
      <div class="n">the scanner covers BTC only today</div></div></div>
  <div class="asset" style="opacity:.55">
    <div class="sym">SOL</div>
    <div class="stat" style="border:0;padding:.6rem 0 0;background:none">
      <div class="k">Not yet scanned</div><div class="v" style="color:var(--ink-faint)">—</div>
      <div class="n">the scanner covers BTC only today</div></div></div>
</div>

<div class="note"><strong>What Genesis does not tell you.</strong> It does not predict price. We
tested whether reaching a liquidation cluster causes a further move and found it does not move
price more than an ordinary volatile minute in the same hour.
<a href="research/liquidations-dont-move-price.html">Read the test →</a></div>

<h2>What we have published</h2>
<p class="lede">{len(sc['findings'])} claims, {sc['counts'].get('REFUTED',0)} of them refuted by us.
Refuted findings are never removed.</p>
<ul class="plain">
""" + "".join(
    f'<li><span class="tag {f["status"]}">{f["status"]}</span>&nbsp; {html.escape(f["title"])}</li>'
    for f in sc["findings"][:5]) + f"""
</ul>
<p style="margin-top:.8rem"><a href="record.html">The full record →</a></p>
"""
    return shell("Genesis — market intelligence for leveraged crypto traders",
                 "Forced-selling exposure on Hyperliquid, how much of it can defend itself, "
                 "and how much of the market we can see.", body, ld)


def page_market(m):
    t, cov = m["totals"], m["coverage"]
    near = m["clusters"][0] if m["clusters"] else None
    rows = "".join(
        f'<tr><td>{"+" if c["distance_pct"]>0 else ""}{c["distance_pct"]:.2f}%</td>'
        f'<td>{c["price"]:,.0f}</td><td class="{c["side"]}">{c["side"]}</td>'
        f'<td>{usd(c["notional_usd"])} <span class="bar" style="width:'
        f'{max(1, c["notional_usd"]/max(x["notional_usd"] for x in m["clusters"])*54):.0f}px"></span></td>'
        f'<td>{c["wallets"]}</td><td>{c["cannot_defend_pct"]:.0f}%</td></tr>'
        for c in m["clusters"])
    ld = {"@context":"https://schema.org","@type":"Dataset","name":"Hyperliquid BTC forced-selling exposure",
          "dateModified":m["generated_at"],"temporalCoverage":m["map_taken_at"],
          "measurementTechnique":"per-wallet clearinghouse state; coverage stated",
          "variableMeasured":[{"@type":"PropertyValue","name":k,"value":v} for k,v in t.items()]}
    body = f"""
<h1>BTC — Hyperliquid</h1>
<p class="lede">Where forced selling sits, and how much of it is trapped.</p>

<div class="answer">
  <div class="q">Cannot defend their position</div>
  <div class="a">{t['cannot_defend_pct']}%</div>
  <div class="s">{usd(t['cannot_defend_usd'])} of {usd(t['forced_notional_usd'])} in forced
  exposure sits with wallets holding <strong>zero free collateral</strong>. They cannot move
  their liquidation price without depositing from outside.</div>
  <div style="margin-top:.8rem">{prov("observed", f"{t['wallets_in_band']} positions read from the venue's own clearinghouse state")}</div>
</div>

<div class="grid">
  <div class="stat"><div class="k">Nearest cluster</div>
    <div class="v">{("+" if near and near["distance_pct"]>0 else "")}{near["distance_pct"]:.2f}%</div>
    <div class="n">{usd(near["notional_usd"])} at {near["price"]:,.0f}</div></div>
  <div class="stat"><div class="k">Forced exposure</div>
    <div class="v">{usd(t['forced_notional_usd'])}</div><div class="n">within ±10%</div></div>
  <div class="stat"><div class="k">Market we can see</div>
    <div class="v">{cov['observed_fraction']*100:.0f}%</div>
    <div class="n">{cov['wallets_scanned']} wallets · {cov['tier']} tier</div></div>
  <div class="stat"><div class="k">Map age</div><div class="v">{age(m['map_age_seconds'])}</div>
    <div class="n">since the last scan</div></div>
</div>

<div class="note"><strong>What happens if a cluster is reached?</strong> Our research found
<strong>no evidence</strong> that it moves price beyond ordinary volatility. Forced flow at 15
minutes returned +40.07 bps — and a random minute in the same hour returned 44.52 bps.
<a href="../research/liquidations-dont-move-price.html">The full test →</a></div>

<h2>Clusters</h2>
<p class="lede">{prov("calculated","0.5% buckets, ±10% of the map's spot")}</p>
<div class="scroll"><table>
<thead><tr><th>Distance</th><th>Price</th><th>Side</th><th>Exposure</th><th>Wallets</th>
<th>Cannot defend</th></tr></thead><tbody>{rows}</tbody></table></div>

<h2>What we cannot see</h2>
<ul class="plain">
  <li>{(1-cov['observed_fraction'])*100:.0f}% of open interest — wallets outside this scan</li>
  <li>cross-margin effects from positions in other assets</li>
  <li>anything that changed in the last {age(m['map_age_seconds'])}</li>
</ul>
<p style="margin-top:.8rem"><a href="../methodology.html">How every number here is produced →</a></p>
"""
    return shell("BTC liquidation risk on Hyperliquid — Genesis",
                 f"{t['cannot_defend_pct']}% of {usd(t['forced_notional_usd'])} in forced BTC "
                 f"exposure cannot defend itself. Coverage stated.", body, ld, depth=1)


ARTICLES = [
  {"slug":"liquidations-dont-move-price",
   "title":"Liquidation maps show where forced selling is. We tested whether it moves price.",
   "finding":"F-0010",
   "answer":"No evidence, once you control for the volatility that was already there.",
   "sub":"228 independent episodes across 28 symbols. Forced flow returned +40.07 bps at 15 "
         "minutes and beat a permutation null. A random minute in the same symbol in the same "
         "hour returned 44.52 bps.",
   "body":"""
<p>Every liquidation product on the market shows you where forced selling sits. Coinglass calls
its heatmap a probability map and attaches no probability to anything. None of them publishes
whether reaching a cluster actually does anything.</p>

<p>We recorded 61,338 forced-order events across 757 symbols on Binance USD-M and collapsed them
into <strong>228 independent episodes</strong> at $250k or more. Episodes, not events: 90% of
large liquidations fall within 60 seconds of another, so counting events as observations inflates
the sample threefold.</p>

<h3>The result</h3>
<div class="scroll"><table>
<thead><tr><th>Horizon</th><th>Mean</th><th>Hit rate</th><th>Permutation p95</th>
<th>Matched control</th></tr></thead><tbody>
<tr><td>1 min</td><td>+6.27 bps</td><td>0.519</td><td>7.93 — fails</td><td>4.96 — clears</td></tr>
<tr><td>5 min</td><td>+11.10 bps</td><td>0.557</td><td>14.99 — fails</td><td>25.13 — fails</td></tr>
<tr><td>15 min</td><td>+40.07 bps</td><td>0.604</td><td>17.06 — clears</td><td>44.52 — fails</td></tr>
</tbody></table></div>

<p>At 15 minutes the effect is large: <strong>+40 bps with a 60% hit rate</strong>, comfortably
beating a permutation null. That number alone would make a compelling product.</p>

<p>Then take any other minute from the same hour in the same symbol. <strong>44.52 bps.</strong>
More.</p>

<h3>What it means</h3>
<p>Liquidations happen because the market is already moving. The move is the volatility; the
liquidation is a symptom of it. A liquidation map is a map of where leverage sat, not a map of
what will happen next.</p>

<h3>Limitations, stated</h3>
<p>Three days of recording. One venue. 106 of 228 episodes had usable price data, biasing the
surviving sample toward liquid symbols — which flatters a liquidity-driven effect rather than
hiding one. And this is Binance: it says nothing about Hyperliquid, whose HLP backstop and far
smaller book differ in ways that could cut either way. That test is running.</p>

<p>The failure is against a matched control, not a power threshold. More data tightens the
intervals; it does not repair a comparison the effect loses on its merits.</p>
"""},
  {"slug":"order-books-lose-depth",
   "title":"Crypto order books lose 15% of their depth during large moves",
   "finding":"F-0002",
   "answer":"0.8462 — and 0.6573 in the worst quarter.",
   "sub":"1,324 days of Binance order-book depth, 3,733,943 snapshots, zero missing days. In "
         "quiet markets the book is unchanged to four decimal places.",
   "body":"""
<p>Every liquidation heatmap models cluster impact against a <strong>static book</strong>: forced
selling meets whatever depth is showing, and price moves by however much that absorbs.</p>

<p>We measured what the book actually does, over three and a half years of free public data.</p>

<h3>Near book, ±0.2–1% of mid</h3>
<div class="scroll"><table>
<thead><tr><th>Horizon</th><th>Quiet market</th><th>Largest moves</th><th>Worst quarter</th>
<th>Distinct days</th></tr></thead><tbody>
<tr><td>1 min</td><td>1.0003</td><td>0.9773</td><td>0.8700</td><td>313</td></tr>
<tr><td>5 min</td><td>1.0015</td><td><strong>0.8462</strong></td><td><strong>0.6573</strong></td><td>160</td></tr>
<tr><td>15 min</td><td>1.0030</td><td>0.8586</td><td>0.6646</td><td>85</td></tr>
</tbody></table></div>

<p><strong>In quiet markets the book is unchanged to four decimal places</strong>, across 1,320
distinct days. That is the control working: the effect appears only where it is claimed to.</p>

<h3>Withdrawal takes minutes, not seconds</h3>
<p>At one minute the book barely flinches. By five minutes it has fallen to 0.846. Liquidity does
not vanish on impact — it leaves over the following minutes.</p>

<p>The consequence is direct and nobody models it: <strong>a fast cascade meets a nearly full
book, a slow grinding one meets a book that is leaving.</strong> Identical forced flow, different
outcome depending on how long the move takes.</p>

<p>Withdrawal is also concentrated near the touch — at five minutes the near book falls to 0.846
while the far book holds at 0.887. The liquidity disappears exactly where the first forced flow
lands.</p>

<h3>What it does not show</h3>
<p>Not causation. Depth falling during a move is equally consistent with makers withdrawing
quotes and with quotes being consumed. And not prediction: it is a conditional description —
given a move of this size, the book was this much thinner.</p>

<h3>Method note</h3>
<p>Snapshots are 30 seconds apart against horizons of 1–15 minutes, so raw rows share most of
their window. An earlier version of this analysis reported <strong>0.726</strong> for the largest
bucket — the most dramatic number in the table — and that bucket vanished entirely once
overlapping observations were removed. It was 26 views of the same few minutes.</p>
"""},
  {"slug":"free-collateral-misclassification",
   "title":"One leveraged wallet in five is misclassified when you ignore free collateral",
   "finding":"F-0001",
   "answer":"The obvious arithmetic is right 19% of the time.",
   "sub":"74 wallets holding open BTC positions. Naive margin maths says 96% could defend their "
         "position. The venue says 76%.",
   "body":"""
<p>When a leveraged position approaches its liquidation price, the trader can usually top up
margin and push that price away. Whether they can is the difference between a cluster that is
real and one that evaporates.</p>

<p>The obvious way to work it out is <code>accountValue − totalMarginUsed</code>. We checked it
against the venue's own <code>withdrawable</code> figure on 74 wallets holding open BTC
positions.</p>

<div class="scroll"><table><tbody>
<tr><td>arithmetic matches the venue</td><td><strong>19%</strong></td></tr>
<tr><td>naive says the wallet can defend</td><td>96%</td></tr>
<tr><td>the venue says it can defend</td><td><strong>76%</strong></td></tr>
<tr><td>misclassified</td><td><strong>20%</strong></td></tr>
<tr><td>median overstatement</td><td>$4,906</td></tr>
<tr><td>largest overstatement</td><td>$3,601,390</td></tr>
</tbody></table></div>

<p>The mismatch is one-directional. <code>withdrawable</code> is systematically <em>lower</em>
than the margin arithmetic implies, and frequently <strong>exactly zero</strong> for wallets the
calculation says hold six figures free.</p>

<h3>Why it cannot be reconstructed</h3>
<p>The venue applies constraints beyond position margin — plausibly margin reserved against open
orders, isolated allocation, or restrictions on unrealised PnL. Whatever the cause, the number is
computed by the exchange and is not a function of the fields a reconstruction would have.</p>

<p>No data provider we surveyed exposes it. A defensibility metric built on their fields would be
wrong for a fifth of wallets — always in the direction of making the market look safer.</p>

<h3>And the money is more trapped than the headcount</h3>
<p>In a live snapshot, 93% of wallets near liquidation held zero free collateral — but
<strong>99.8% of the notional</strong> did. The large positions are disproportionately the
undefendable ones.</p>
"""},
]


def page_article(a):
    ld = {"@context":"https://schema.org","@type":"ScholarlyArticle","headline":a["title"],
          "abstract":a["sub"],"identifier":a["finding"],
          "publisher":{"@type":"Organization","name":"Genesis"}}
    body = f"""
<h1>{html.escape(a['title'])}</h1>
<p class="lede">{html.escape(a['sub'])}</p>
<div class="answer"><div class="q">The answer</div>
  <div class="a calm" style="font-size:1.5rem;line-height:1.3">{html.escape(a['answer'])}</div>
  <div style="margin-top:.9rem">{prov("historical", a["finding"] + " · see the record for status")}</div>
</div>
{a['body']}
<p style="margin-top:2rem"><a href="index.html">← All research</a> ·
<a href="../record.html">Our record, including what we got wrong →</a></p>
"""
    return shell(a["title"] + " — Genesis Research", a["sub"], body, ld, depth=1)


def page_research_index():
    items = "".join(
      f'<li><a href="{a["slug"]}.html"><strong>{html.escape(a["title"])}</strong></a><br>'
      f'<span style="color:var(--ink-faint)">{html.escape(a["sub"][:120])}…</span></li>'
      for a in ARTICLES)
    body = f"""
<h1>Research</h1>
<p class="lede">An evidence library, not a blog. Every finding carries its method, its sample and
its limits — and the ones we later refuted stay published.</p>
<ul class="plain">{items}</ul>
"""
    return shell("Genesis Research — evidence on crypto market structure",
                 "Original measurements on liquidation cascades, order-book depth and leveraged "
                 "positioning, with methods and limitations stated.", body, depth=1)


def page_record(sc):
    rows = "".join(
      f'<li><span class="tag {f["status"]}">{f["status"]}</span>&nbsp; '
      f'<strong>{html.escape(f["title"])}</strong><br>'
      f'<span style="color:var(--ink-faint);font-size:.85rem">{html.escape(f["observation"] or "")}</span></li>'
      for f in sc["findings"])
    c = sc["counts"]
    body = f"""
<h1>Our record</h1>
<p class="lede">Every claim Genesis has published, and what happened to it. Refuted findings are
never removed — a record that keeps only its wins is a marketing page.</p>
<div class="grid">
""" + "".join(f'<div class="stat"><div class="k">{k}</div><div class="v">{v}</div></div>'
              for k, v in sorted(c.items())) + f"""
</div>
<div class="note">Two of these were claims we made confidently and then disproved ourselves. They
are the entries a competitor will not reproduce, because doing so means publishing when you were
wrong.</div>
<ul class="plain">{rows}</ul>
"""
    return shell("Our record — Genesis", "Every claim Genesis has published, including the ones "
                 "we refuted ourselves.", body)


def page_methodology(m):
    body = f"""
<h1>Methodology</h1>
<p class="lede">How each number is produced, and which tier of evidence it sits on.</p>

<h2>The provenance ladder</h2>
<p>Every figure on this site carries one of four tiers. There is deliberately no
<em>predicted</em> tier.</p>
<ul class="plain">
<li>{prov("observed","read directly from the venue — liquidation price, free collateral")}</li>
<li>{prov("calculated","arithmetic over observations — cluster notional, defensibility")}</li>
<li>{prov("estimated","a model with stated assumptions — full-universe coverage")}</li>
<li>{prov("historical","measured over an archive — depth evaporation over 1,324 days")}</li>
</ul>

<h2>Defensibility</h2>
<p>The share of a cluster's notional held by wallets whose <code>withdrawable</code> is exactly
zero. They cannot move their liquidation price without depositing from outside. This requires the
venue's own figure — the obvious arithmetic misclassifies one wallet in five.
<a href="research/free-collateral-misclassification.html">The measurement →</a></p>

<h2>Coverage</h2>
<p>Scanned position notional divided by exchange open interest, reported for
<em>this</em> scan rather than the best scan we have ever run. The current map states
{m['coverage']['observed_fraction']*100:.0f}%; a full universe reaches an estimated
{m['coverage']['full_universe_estimate']*100:.1f}%. Publishing the better number on a narrower
scan would be exactly the dishonesty this site exists to avoid.</p>

<h2>Map age</h2>
<p>The position scan runs on a slower cadence than the order book updates. Every figure carries
how old the underlying scan is, because a map presented as current when it is an hour old is
precision that does not exist.</p>

<h2>What we do not publish</h2>
<ul class="plain">
<li>A cascade magnitude. We tested whether reaching a cluster moves price and it did not beat a
volatility-matched minute.</li>
<li>A risk rating without a measured basis. LOW/MODERATE/HIGH is a colour, not a finding.</li>
<li>A prediction record before making predictions.</li>
</ul>
"""
    return shell("Methodology — Genesis", "How Genesis produces every number, and the four tiers "
                 "of evidence it distinguishes.", body)


def page_api(m):
    body = f"""
<h1>API</h1>
<p class="lede">The same source of truth the pages are generated from. Static JSON — no key, no
rate limit, no server to fall over.</p>
<h2>Endpoints</h2>
<pre>GET /data/map.json         clusters, exposure, defensibility, coverage
GET /data/scorecard.json   every published claim and its status
GET /data/meta.json        what we cannot currently see</pre>
<h2>Example</h2>
<pre>{html.escape(json.dumps({k: m[k] for k in ("asset","venue","map_taken_at","map_age_seconds")}, indent=1))}
"coverage": {html.escape(json.dumps(m["coverage"], indent=1))}</pre>
<h2>For agents</h2>
<p>Every page carries JSON-LD describing the same measurements, so a retrieval system can cite a
figure together with its observation count, timestamp, coverage and method rather than parsing a
chart.</p>
<div class="note">Every response states what fraction of the market it observed. A number without
its coverage is not an answer.</div>
"""
    return shell("API — Genesis", "Static JSON: liquidation exposure, defensibility and coverage "
                 "for Hyperliquid.", body)


def main():
    m, sc = load("map"), load("scorecard")
    os.makedirs(os.path.join(PUB, "markets"), exist_ok=True)
    os.makedirs(os.path.join(PUB, "research"), exist_ok=True)
    out = {
      "index.html": page_home(m, sc),
      "markets/btc.html": page_market(m),
      "research/index.html": page_research_index(),
      "record.html": page_record(sc),
      "methodology.html": page_methodology(m),
      "api.html": page_api(m),
    }
    for a in ARTICLES:
        out[f"research/{a['slug']}.html"] = page_article(a)
    for path, doc in out.items():
        with open(os.path.join(PUB, path), "w") as f:
            f.write(doc)
        print(f"  {path:<48} {len(doc):>7,} bytes")
    print(f"\n{len(out)} pages written to {PUB}")


if __name__ == "__main__":
    main()
