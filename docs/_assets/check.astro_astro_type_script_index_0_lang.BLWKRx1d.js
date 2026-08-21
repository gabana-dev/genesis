const y="https://api.hyperliquid.xyz/info",l=t=>{const e=document.getElementById(t);if(!e)throw new Error(`missing #${t}`);return e},r=t=>t>=1e9?`$${(t/1e9).toFixed(2)}B`:t>=1e6?`$${(t/1e6).toFixed(2)}M`:t>=1e3?`$${(t/1e3).toFixed(1)}k`:`$${t.toFixed(2)}`,v=(t,e=2)=>t.toLocaleString(void 0,{maximumFractionDigits:e});async function f(t){const e=await fetch(y,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(t)});if(!e.ok)throw new Error(`exchange returned ${e.status}`);return await e.json()}function b(t,e){return(t.assetPositions??[]).map(i=>i.position).filter(i=>!!i?.liquidationPx).map(i=>{const s=Number(e[i.coin]),o=Number(i.liquidationPx),n=Number(i.szi);return!s||!o||!n?null:{coin:i.coin,side:n>0?"long":"short",liq:o,mid:s,dist:Math.abs(s-o)/s*100,notional:Math.abs(n)*s}}).filter(i=>i!==null).sort((i,s)=>i.dist-s.dist)}function q(t,e){const i=e>0?t/e:null;return t<=0?`<strong>There is nothing to defend with.</strong> Free collateral is zero, so the
      liquidation price cannot be moved without depositing from outside the account.`:i!==null&&i<.05?`<strong>Almost nothing to defend with.</strong> Free collateral is ${r(t)} against
      ${r(e)} of margin in use — topping up would move the liquidation price very little.`:`Free collateral is <strong>${r(t)}</strong>${i!==null?`, roughly ${(i*100).toFixed(0)}% of margin in use`:""}. There is room to push the liquidation price away.`}function w(){l("explain").hidden=!1;const t=document.getElementById("alertcta");t&&(t.hidden=!1)}function x(t,e){const i=t.marginSummary??{},s=Number(i.accountValue??0),o=Number(i.totalMarginUsed??0),n=Number(t.withdrawable??0),c=b(t,e),p=l("out");if(c.length===0){p.innerHTML=`<div class="answer"><div class="q">No open positions</div>
      <div class="a calm" style="font-size:1.5rem;line-height:1.3">Nothing at risk</div>
      <div class="s">This address has no leveraged positions with a liquidation price on
      Hyperliquid right now.</div></div>`,w();return}const a=c[0],$=n<=0;p.innerHTML=`
  <div class="answer">
    <div class="q">Closest liquidation — ${a.coin} ${a.side}</div>
    <div class="a ${a.dist>15?"calm":""}">${a.dist.toFixed(1)}%</div>
    <div class="s">${a.coin} is at ${v(a.mid)}. This position liquidates at
      <strong>${v(a.liq)}</strong>.<br>${q(n,o)}</div>
    <div style="margin-top:.9rem"><span class="prov prov-observed">observed</span>
      <span class="prov-d">read live from Hyperliquid's clearinghouse ·
      ${new Date().toISOString().slice(0,19)}Z</span></div>
  </div>

  <div class="grid">
    <div class="stat"><div class="k">Account value</div><div class="v">${r(s)}</div></div>
    <div class="stat"><div class="k">Margin in use</div><div class="v">${r(o)}</div></div>
    <div class="stat"><div class="k">Free collateral</div>
      <div class="v" style="color:${$?"var(--hot)":"inherit"}">${r(n)}</div>
      <div class="n">${$?"cannot defend":"can be added to a position"}</div></div>
    <div class="stat"><div class="k">Open positions</div><div class="v">${c.length}</div></div>
  </div>

  <h2>Every position</h2>
  <div class="scroll"><table>
    <thead><tr><th>Coin</th><th>Side</th><th>Size</th><th>Mark</th><th>Liquidates at</th>
      <th>Distance</th></tr></thead>
    <tbody>${c.map(d=>`<tr><td>${d.coin}</td>
        <td class="${d.side==="long"?"buy":"sell"}">${d.side}</td>
        <td>${r(d.notional)}</td><td>${v(d.mid,4)}</td><td>${v(d.liq,4)}</td>
        <td>${d.dist.toFixed(1)}%</td></tr>`).join("")}</tbody>
  </table></div>
  <p class="hint" style="margin-top:.6rem">A distance far above 100% is a position price would
  have to double to reach. The exchange still reports a liquidation price for it, so we show it
  rather than hide it.</p>`,w()}async function m(t){const e=t.trim().toLowerCase(),i=l("out");if(!/^0x[0-9a-f]{40}$/.test(e)){i.innerHTML=`<div class="note">That does not look like a Hyperliquid address.
      It should be <code>0x</code> followed by 40 hex characters.</div>`;return}i.innerHTML='<div class="answer"><div class="q">Reading the exchange…</div></div>';try{const[s,o]=await Promise.all([f({type:"clearinghouseState",user:e}),f({type:"allMids"})]);x(s,o)}catch(s){i.innerHTML=`<div class="note"><strong>Could not reach Hyperliquid.</strong>
      ${s instanceof Error?s.message:"unknown error"}. Nothing is cached — this page always
      reads live, so there is no stale answer to fall back on.</div>`}}const g=l("addr");l("f").addEventListener("submit",t=>{t.preventDefault(),m(g.value)});const u=document.getElementById("demo");u?.dataset.address&&u.addEventListener("click",()=>{const t=u.dataset.address;g.value=t,m(t)});const h=new URLSearchParams(location.search).get("a");h&&(g.value=h,m(h));
