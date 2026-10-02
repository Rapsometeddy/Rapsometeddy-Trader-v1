(function(){
const $=id=>document.getElementById(id), KEY="rt-strategy-lab";
const defaults={name:"Balanced",fast:20,slow:50,rsiBuy:50,rsiSell:50,stop:2,target:4};
let market=null;
function loadPrefs(){try{return {...defaults,...JSON.parse(localStorage.getItem(KEY)||"{}")}}catch{return {...defaults}}}
function savePrefs(p){localStorage.setItem(KEY,JSON.stringify(p))}
function render(){const p=loadPrefs();["labFast","labSlow","labRsiBuy","labRsiSell","labStop","labTarget"].forEach((id,i)=>{if($(id))$(id).value=[p.fast,p.slow,p.rsiBuy,p.rsiSell,p.stop,p.target][i]});if($("labName"))$("labName").value=p.name;run()}
function run(){
 if(!market?.candles?.length){$("labStatus").textContent="Waiting for market snapshot…";return}
 const p={fast:+$("labFast").value||20,slow:+$("labSlow").value||50,rsiBuy:+$("labRsiBuy").value||50,rsiSell:+$("labRsiSell").value||50,stop:+$("labStop").value||2,target:+$("labTarget").value||4};
 const c=market.candles.filter(x=>x.close!=null&&x.rsi!=null), warm=Math.max(2,p.slow), data=c.slice(warm);
 let bal=10000,peak=bal,dd=0,wins=0,losses=0,trades=0,pos=null;
 for(let i=warm;i<c.length;i++){
  const x=c[i], prev=c.slice(Math.max(0,i-p.fast),i).reduce((s,z)=>s+z.close,0)/Math.max(1,Math.min(p.fast,i));
  const slow=c.slice(Math.max(0,i-p.slow),i).reduce((s,z)=>s+z.close,0)/Math.max(1,Math.min(p.slow,i));
  if(pos){
   const stopHit=pos.side==="BUY"?x.low<=pos.stop:x.high>=pos.stop, tpHit=pos.side==="BUY"?x.high>=pos.tp:x.low<=pos.tp;
   if(stopHit||tpHit){const exit=stopHit?pos.stop:pos.tp, pnl=(pos.side==="BUY"?exit-pos.entry:pos.entry-exit)*pos.units;bal+=pnl;pnl>=0?wins++:losses++;trades++;pos=null}
  }
  if(!pos){
   const sig=prev>slow&&x.rsi>=p.rsiBuy?"BUY":prev<slow&&x.rsi<=p.rsiSell?"SELL":"HOLD";
   if(sig!=="HOLD"){const entry=x.close,risk=bal*.01,dist=entry*p.stop/100;pos={side:sig,entry,stop:sig==="BUY"?entry-dist:entry+dist,tp:sig==="BUY"?entry+entry*p.target/100:entry-entry*p.target/100,units:dist?risk/dist:0}}
  }
  peak=Math.max(peak,bal);dd=Math.max(dd,(peak-bal)/peak*100);
 }
 if(pos){const x=c[c.length-1],pnl=(pos.side==="BUY"?x.close-pos.entry:pos.entry-x.close)*pos.units;bal+=pnl;pnl>=0?wins++:losses++;trades++}
 $("labBalance").textContent="R"+bal.toFixed(2);$("labPnl").textContent="R"+(bal-10000).toFixed(2);$("labTrades").textContent=trades;$("labWinRate").textContent=(trades?wins/trades*100:0).toFixed(1)+"%";$("labDrawdown").textContent=dd.toFixed(2)+"%";
 $("labStatus").textContent="Simulation uses the available AAPL snapshot. Results are historical/paper calculations, not predictions.";
}
async function init(){try{market=await (await fetch("market.json",{cache:"no-store"})).json()}catch{};["labFast","labSlow","labRsiBuy","labRsiSell","labStop","labTarget"].forEach(id=>$(id)?.addEventListener("input",run));$("labRun")?.addEventListener("click",run);$("labSave")?.addEventListener("click",()=>{savePrefs({name:$("labName").value||"Custom",fast:+$("labFast").value,slow:+$("labSlow").value,rsiBuy:+$("labRsiBuy").value,rsiSell:+$("labRsiSell").value,stop:+$("labStop").value,target:+$("labTarget").value});$("labStatus").textContent="Strategy saved on this device."});$("labReset")?.addEventListener("click",()=>{savePrefs(defaults);render()});render()}
window.addEventListener("load",init)})();