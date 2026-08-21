---
title: "One leveraged wallet in five is misclassified when you ignore free collateral"
finding: "F-0001"
answer: "The obvious arithmetic is right 19% of the time."
sub: "74 wallets holding open BTC positions. Naive margin maths says 96% could defend their position. The venue says 76%."
---

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
