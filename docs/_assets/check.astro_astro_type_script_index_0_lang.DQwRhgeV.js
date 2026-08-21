const w="https://api.hyperliquid.xyz/info",l=t=>{const e=document.getElementById(t);if(!e)throw new Error(`missing #${t}`);return e},r=t=>t>=1e9?`$${(t/1e9).toFixed(2)}B`:t>=1e6?`$${(t/1e6).toFixed(2)}M`:t>=1e3?`$${(t/1e3).toFixed(1)}k`:`$${t.toFixed(2)}`,h=(t,e=2)=>t.toLocaleString(void 0,{maximumFractionDigits:e});async function f(t){const e=await fetch(w,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(t)});if(!e.ok)throw new Error(`exchange returned ${e.status}`);return await e.json()}function b(t,e){return(t.assetPositions??[]).map(i=>i.position).filter(i=>!!i?.liquidationPx).map(i=>{const s=Number(e[i.coin]),o=Number(i.liquidationPx),a=Number(i.szi);return!s||!o||!a?null:{coin:i.coin,side:a>0?"long":"short",liq:o,mid:s,dist:Math.abs(s-o)/s*100,notional:Math.abs(a)*s}}).filter(i=>i!==null).sort((i,s)=>i.dist-s.dist)}function q(t,e){const i=e>0?t/e:null;return t<=0?`<strong>There is nothing to defend with.</strong> Free collateral is zero, so the
      liquidation price cannot be moved without depositing from outside the account.`:i!==null&&i<.05?`<strong>Almost nothing to defend with.</strong> Free collateral is ${r(t)} against
      ${r(e)} of margin in use — topping up would move the liquidation price very little.`:`Free collateral is <strong>${r(t)}</strong>${i!==null?`, roughly ${(i*100).toFixed(0)}% of margin in use`:""}. There is room to push the liquidation price away.`}function y(){l("explain").hidden=!1;const t=document.getElementById("alertcta");t&&(t.hidden=!1)}function x(t,e){const i=t.marginSummary??{},s=Number(i.accountValue??0),o=Number(i.totalMarginUsed??0),a=Number(t.withdrawable??0),c=b(t,e),p=l("out");if(c.length===0){const n=s===0&&o===0;p.innerHTML=`<div class="answer"><div class="q">No open positions found</div>
      <div class="a calm" style="font-size:1.5rem;line-height:1.3">Nothing to report</div>
      <div class="s">Hyperliquid reports no leveraged positions with a liquidation price for this
      address right now.${n?`<br><br><strong>This account is empty, which has two possible meanings.</strong>
             Either it genuinely holds nothing, or it is an <strong>API / agent wallet</strong> —
             those authorise trades but never hold positions, so the exchange returns an empty
             result for them. If you use one, check the main account you deposit and trade with
             instead.`:""}</div></div>`,y();return}const d=c[0],$=a<=0;p.innerHTML=`
  <div class="answer">
    <div class="q">Closest liquidation — ${d.coin} ${d.side}</div>
    <div class="a ${d.dist>15?"calm":""}">${d.dist.toFixed(1)}%</div>
    <div class="s">${d.coin} is at ${h(d.mid)}. This position liquidates at
      <strong>${h(d.liq)}</strong>.<br>${q(a,o)}</div>
    <div style="margin-top:.9rem"><span class="prov prov-observed">observed</span>
      <span class="prov-d">read live from Hyperliquid's clearinghouse ·
      ${new Date().toISOString().slice(0,19)}Z</span></div>
  </div>

  <div class="grid">
    <div class="stat"><div class="k">Account value</div><div class="v">${r(s)}</div></div>
    <div class="stat"><div class="k">Margin in use</div><div class="v">${r(o)}</div></div>
    <div class="stat"><div class="k">Free collateral</div>
      <div class="v" style="color:${$?"var(--hot)":"inherit"}">${r(a)}</div>
      <div class="n">${$?"cannot defend":"can be added to a position"}</div></div>
    <div class="stat"><div class="k">Open positions</div><div class="v">${c.length}</div></div>
  </div>

  <h2>Every position</h2>
  <div class="scroll"><table>
    <thead><tr><th>Coin</th><th>Side</th><th>Size</th><th>Mark</th><th>Liquidates at</th>
      <th>Distance</th></tr></thead>
    <tbody>${c.map(n=>`<tr><td>${n.coin}</td>
        <td class="${n.side==="long"?"buy":"sell"}">${n.side}</td>
        <td>${r(n.notional)}</td><td>${h(n.mid,4)}</td><td>${h(n.liq,4)}</td>
        <td>${n.dist.toFixed(1)}%</td></tr>`).join("")}</tbody>
  </table></div>
  <p class="hint" style="margin-top:.6rem">A distance far above 100% is a position price would
  have to double to reach. The exchange still reports a liquidation price for it, so we show it
  rather than hide it.</p>`,y()}async function g(t){const e=t.trim().toLowerCase(),i=l("out");if(!/^0x[0-9a-f]{40}$/.test(e)){i.innerHTML=`<div class="note">That does not look like a Hyperliquid address.
      It should be <code>0x</code> followed by 40 hex characters.</div>`;return}i.innerHTML='<div class="answer"><div class="q">Reading the exchange…</div></div>';try{const[s,o]=await Promise.all([f({type:"clearinghouseState",user:e}),f({type:"allMids"})]);x(s,o)}catch(s){i.innerHTML=`<div class="note"><strong>Could not reach Hyperliquid.</strong>
      ${s instanceof Error?s.message:"unknown error"}. Nothing is cached — this page always
      reads live, so there is no stale answer to fall back on.</div>`}}const m=l("addr");l("f").addEventListener("submit",t=>{t.preventDefault(),g(m.value)});const u=document.getElementById("demo");u?.dataset.address&&u.addEventListener("click",()=>{const t=u.dataset.address;m.value=t,g(t)});const v=new URLSearchParams(location.search).get("a");v&&(m.value=v,g(v));
