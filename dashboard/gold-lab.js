/* Gold Lab: technical-only, paper-only client renderer. No news/calendar inputs. */
(()=>{
 const $=id=>document.getElementById(id);
 const fmt=n=>Number(n).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});
 function chart(candles){
  const canvas=$("goldChart"); if(!canvas||!candles?.length)return;
  const d=window.devicePixelRatio||1,r=canvas.getBoundingClientRect(); if(!r.width)return;
  canvas.width=r.width*d;canvas.height=260*d;const ctx=canvas.getContext("2d");ctx.scale(d,d);
  const w=r.width,h=260,min=Math.min(...candles.map(c=>c.low)),max=Math.max(...candles.map(c=>c.high)),range=max-min||1;
  const x=i=>i/(candles.length-1||1)*w,y=v=>h-20-(v-min)/range*(h-40),step=w/candles.length,cw=Math.max(1,step*.55);
  candles.forEach((c,i)=>{const xx=x(i),up=c.close>=c.open;ctx.strokeStyle=up?"#86efac":"#fca5a5";ctx.fillStyle=ctx.strokeStyle;ctx.beginPath();ctx.moveTo(xx,y(c.high));ctx.lineTo(xx,y(c.low));ctx.stroke();const top=y(Math.max(c.open,c.close)),bottom=y(Math.min(c.open,c.close));ctx.fillRect(xx-cw/2,top,cw,Math.max(1,bottom-top));});
  for(const [key,color] of [["ema20","#c4b5fd"],["ema50","#93c5fd"]]){ctx.beginPath();candles.forEach((c,i)=>i?ctx.lineTo(x(i),y(c[key])):ctx.moveTo(x(i),y(c[key])));ctx.strokeStyle=color;ctx.lineWidth=2;ctx.stroke();}
  ctx.fillStyle="#e9ddff";ctx.font="11px system-ui";ctx.fillText("EMA 20",8,14);ctx.fillText("EMA 50",70,14);
 }
 async function load(){
  try{
   const r=await fetch("gold.json",{cache:"no-store"});if(!r.ok)throw Error("snapshot not ready");const g=await r.json();
   $("goldPrice").textContent=fmt(g.latest_price);$("goldSignal").textContent=g.signal;
   $("goldSignalNote").textContent="EMA20/50 • RSI14 • ATR14";
   $("goldUpdated").textContent=new Date(g.updated_at).toLocaleTimeString();
   $("goldCandleCount").textContent=(g.candles||[]).length+" recent 1m candles";
   const s=g.simulation||{};$("goldBalance").textContent="$"+fmt(s.ending_balance??10000);
   $("goldPnl").textContent="$"+fmt(s.pnl??0);$("goldWinRate").textContent=fmt(s.win_rate_pct??0)+"%";
   $("goldDrawdown").textContent=fmt(s.max_drawdown_pct??0)+"%";$("goldTrades").textContent=(s.trades??0)+" simulated trades";
   $("goldTradeRows").innerHTML=(g.trade_history||[]).slice().reverse().map(t=>"<tr><td>"+t.side+"</td><td>"+fmt(t.entry)+"</td><td>"+fmt(t.exit)+"</td><td>"+(t.pnl>=0?"+":"")+fmt(t.pnl)+"</td><td>"+t.reason.replaceAll("_"," ")+"</td></tr>").join("")||'<tr><td colspan="5">No completed simulated trades yet.</td></tr>';
   chart(g.candles||[]);$("goldFeedStatus").textContent="Feed: "+g.source+" • Paper simulation only. No real orders.";
  }catch(e){$("goldFeedStatus").textContent="Gold snapshot not available yet. The scheduled GitHub Actions job must run successfully first."}
 }
 window.addEventListener("load",()=>{load();setInterval(load,60000);});
 window.addEventListener("resize",()=>{load();});
})();
