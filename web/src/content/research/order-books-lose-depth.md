---
title: "Crypto order books lose 15% of their depth during large moves"
finding: "F-0002"
answer: "0.8462 — and 0.6573 in the worst quarter."
sub: "1,324 days of Binance order-book depth, 3,733,943 snapshots, zero missing days. In quiet markets the book is unchanged to four decimal places."
---

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
