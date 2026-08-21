---
title: "Liquidation maps show where forced selling is. We tested whether it moves price."
finding: "F-0010"
answer: "No evidence, once you control for the volatility that was already there."
sub: "228 independent episodes across 28 symbols. Forced flow returned +40.07 bps at 15 minutes and beat a permutation null. A random minute in the same symbol in the same hour returned 44.52 bps."
---

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
