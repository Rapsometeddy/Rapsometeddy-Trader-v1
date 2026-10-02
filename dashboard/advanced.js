(function(){
const qs=id=>document.getElementById(id);
let market=null, scanner=null;
const WATCH_KEY="rt-watchlist";
const PREF_KEY="rt-prefs";

function fmt(n,d=2){return Number(n).toLocaleString("en-ZA",{minimumFractionDigits:d,maximumFractionDigits:d})}
function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}

function getWatch(){try{return JSON.parse(localStorage.getItem(WATCH_KEY)||'["AAPL","EUR/USD","GBP/USD","USD/JPY","NVDA","MSFT"]')}catch{return ["AAPL"]}}
function setWatch(v){localStorage.setItem(WATCH_KEY,JSON.stringify(v))}
function renderWatch(){
 const list=getWatch(), rows=qs("watchRows");
 if(!rows)return;
 const scan=scanner?.markets||{};
 rows.innerHTML=list.map(sym=>{
   const m=scan[sym], isAapl=sym==="AAPL";
   const price=isAapl?(market?.latest_close):m?.price;
   const signal=isAapl?market?.signal:m?.signal;
   return '<tr><td><b>'+esc(sym)+'</b></td><td>'+(price!=null?fmt(price, sym.includes("/")?5:2):"—")+'</td><td class="'+(signal?.includes("BUY")?"profit":signal?.includes("SELL")?"loss":"")+'">'+esc(signal||"Waiting")+'</td><td><button class="mini-btn" data-remove="'+esc(sym)+'">Remove</button></td></tr>';
 }).join("")||'<tr><td colspan="4">Watchlist is empty.</td></tr>';
 rows.querySelectorAll("[data-remove]").forEach(b=>b.onclick=()=>{setWatch(getWatch().filter(x=>x!==b.dataset.remove));renderWatch()});
}
function addWatch(){
 const input=qs("watchSymbol"), sym=(input.value||"").trim().toUpperCase();
 if(!sym)return;
 const list=getWatch(); if(!list.includes(sym))list.push(sym);
 setWatch(list); input.value=""; renderWatch();
}

function renderLevels(){
 const c=market?.candles||[], box=qs("levelsBody");
 if(!box||c.length<10)return;
 const recent=c.slice(-60), highs=recent.map(x=>x.high), lows=recent.map(x=>x.low);
 const resistance=Math.max(...highs), support=Math.min(...lows), price=recent[recent.length-1].close;
 const atr=recent.reduce((s,x)=>s+(x.high-x.low),0)/recent.length;
 const vol=recent.map(x=>x.close).reduce((s,x,i,a)=>i?s+Math.abs(x-a[i-1]):s,0)/(recent.length-1);
 qs("levelSupport").textContent=fmt(support,2);
 qs("levelResistance").textContent=fmt(resistance,2);
 qs("levelDistance").textContent=fmt(Math.min(Math.abs(price-support),Math.abs(resistance-price)),2);
 qs("volRange").textContent=fmt(atr,2);
 qs("volMove").textContent=fmt(vol,2);
 qs("volRatio").textContent=fmt((atr/price)*100,2)+"%";
 box.textContent="Last 60 available candles";
}

function setupChecklist(){
 const c=(market?.candles||[]), last=c[c.length-1];
 if(!last)return;
 const checks=[
  ["EMA alignment",last.ema_fast!=null&&last.ema_slow!=null?(last.ema_fast>last.ema_slow?"Bullish":"Bearish"):"Waiting"],
  ["RSI",last.rsi!=null?fmt(last.rsi,1):"Waiting"],
  ["Price vs recent range",last.close>=Math.min(...c.slice(-30).map(x=>x.low))&&last.close<=Math.max(...c.slice(-30).map(x=>x.high))?"Inside range":"Outside range"],
  ["Signal",last.signal||"HOLD"]
 ];
 qs("checkRows").innerHTML=checks.map(([a,b])=>'<div><span>'+a+'</span><b>'+esc(b)+'</b></div>').join("");
}

function backtest(){
 const c=(market?.candles||[]).filter(x=>x.ema_fast!=null&&x.ema_slow!=null&&x.rsi!=null);
 if(c.length<3){qs("btRunStatus").textContent="Not enough candles.";return}
 let bal=10000, peak=bal, maxDD=0, wins=0,losses=0,trades=0,pos=null;
 for(const x of c){
   if(pos){
     const hitLong=x.low<=pos.stop||x.high>=pos.tp, hitShort=x.high>=pos.stop||x.low<=pos.tp;
     if((pos.side==="BUY"&&hitLong)||(pos.side==="SELL"&&hitShort)){
       const exit=pos.side==="BUY"?(x.low<=pos.stop?pos.stop:pos.tp):(x.high>=pos.stop?pos.stop:pos.tp);
       const pnl=pos.side==="BUY"?exit-pos.entry:pos.entry-exit;
       bal+=pnl*pos.units; pnl>=0?wins++:losses++; trades++; pos=null;
     }
   }
   if(!pos){
     const sig=x.ema_fast>x.ema_slow&&x.rsi>=50?"BUY":x.ema_fast<x.ema_slow&&x.rsi<=50?"SELL":"HOLD";
     if(sig!=="HOLD"){
       const entry=x.close, risk=bal*.01, dist=entry*.02;
       pos={side:sig,entry,stop:sig==="BUY"?entry-dist:entry+dist,tp:sig==="BUY"?entry+dist*2:entry-dist*2,units:dist?risk/dist:0};
     }
   }
   peak=Math.max(peak,bal); maxDD=Math.max(maxDD,(peak-bal)/peak*100);
 }
 if(pos){const last=c[c.length-1],pnl=pos.side==="BUY"?last.close-pos.entry:pos.entry-last.close;bal+=pnl*pos.units;pnl>=0?wins++:losses++;trades++}
 const pnl=bal-10000,wr=trades?wins/trades*100:0;
 qs("simBalance").textContent="R"+fmt(bal);qs("simPnl").textContent="R"+fmt(pnl);qs("simTrades").textContent=trades;
 qs("simWinRate").textContent=fmt(wr,1)+"%";qs("simDrawdown").textContent=fmt(maxDD,2)+"%";
 qs("btRunStatus").textContent="Simulated "+c.length+" candles using EMA20/50 + RSI14, 1% risk and 2R target. Paper-only.";
}

function exportJournal(){
 const rows=JSON.parse(localStorage.getItem("rt-journal")||"[]");
 if(!rows.length){alert("No journal entries to export.");return}
 const head=["Date","Market","Side","Entry","Exit","Result","Reason"];
 const csv=[head,...rows.map(x=>[x.date,x.market,x.side,x.entry,x.exit,x.result,x.reason])].map(r=>r.map(v=>'"'+String(v??"").replaceAll('"','""')+'"').join(",")).join("\n");
 const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([csv],{type:"text/csv"}));a.download="rapsometeddy-paper-journal.csv";a.click();URL.revokeObjectURL(a.href);
}

function savePrefs(){
 const p={compact:qs("compactMode")?.checked||false,refresh:qs("refreshRate")?.value||60};
 localStorage.setItem(PREF_KEY,JSON.stringify(p));
 document.body.classList.toggle("compact-mode",p.compact);
 qs("prefStatus").textContent="Preferences saved on this device.";
}
function loadPrefs(){
 try{const p=JSON.parse(localStorage.getItem(PREF_KEY)||"{}");if(qs("compactMode"))qs("compactMode").checked=!!p.compact;document.body.classList.toggle("compact-mode",!!p.compact)}catch{}
}

async function init(){
 try{market=await (await fetch("market.json",{cache:"no-store"})).json()}catch{}
 try{scanner=await (await fetch("scanner.json",{cache:"no-store"})).json()}catch{}
 renderWatch();renderLevels();setupChecklist();backtest();loadPrefs();
 qs("addWatch")?.addEventListener("click",addWatch);
 qs("watchSymbol")?.addEventListener("keydown",e=>{if(e.key==="Enter")addWatch()});
 qs("runBacktest")?.addEventListener("click",backtest);
 qs("exportJournal")?.addEventListener("click",exportJournal);
 qs("savePrefs")?.addEventListener("click",savePrefs);
}
window.addEventListener("load",init);
})();