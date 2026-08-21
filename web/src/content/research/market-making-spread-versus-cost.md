---
title: "The spread was 0.00154 bps. The cost was 5.19."
finding: "EXEC-1"
answer: "Passive market making on BTCUSDT loses by a factor of about 3,400."
sub: "And a zero maker fee does not rescue it. We checked, because that is the first thing anyone assumes."
---

<p>Market making sounds like the safe way to earn in crypto: quote both sides, capture the
spread, stay flat. We measured what that actually pays on BTCUSDT.</p>

<div class="scroll"><table><tbody>
<tr><td>spread captured per round trip</td><td><strong>0.00154 bps</strong></td></tr>
<tr><td>cost per round trip</td><td><strong>5.19 bps</strong></td></tr>
<tr><td>measured maker advantage</td><td>1.83 bps</td></tr>
</tbody></table></div>

<p>The obvious objection is fees. So we asked what happens at a <strong>zero maker fee</strong> —
the tier the largest firms actually trade on. It still loses. The gap is not a fee problem.</p>

<h3>The finding that outlived the strategy</h3>
<p>The useful result came out of the wreckage. Adverse selection — how much the market moves
against you right after you are filled — is brutal at short horizons and <strong>decays by roughly
a hundredfold</strong> between sixty seconds and one day, to 0.1301 bps.</p>

<p>We had predicted around 1 bps and were wrong by a factor of nine, in the direction that
matters: longer horizons are far more economically survivable than the short-horizon numbers
suggest. That single measurement reopened a line of work the market-making result had closed.</p>

<h3>Why publish a failure</h3>
<p>Because the arithmetic is checkable and the conclusion is not obvious. A ratio of 3,400 to one
is not a near miss to be optimised away — it says the strategy is unavailable at this latency and
this fee tier, and no amount of tuning changes that.</p>
