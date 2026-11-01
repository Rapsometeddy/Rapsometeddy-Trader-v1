"""Fetch public XAU/USD 1-minute candles and build a news-blind paper snapshot."""
import json, math, os, urllib.request
from datetime import datetime, timezone

# Yahoo's 1-minute endpoint only retains a short history. A 5-day window
# includes the most recent completed session when futures are closed (e.g. Sunday).
URL = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?range=5d&interval=1m"
REQ = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 RapsometeddyTrader/1.0"})
with urllib.request.urlopen(REQ, timeout=30) as response:
    raw = json.load(response)

chart = raw.get("chart", {})
if chart.get("error"):
    raise RuntimeError(f"Yahoo Finance chart error: {chart['error']}")
results = chart.get("result") or []
if not results:
    raise RuntimeError("Yahoo Finance returned no GC=F chart data for the 5-day 1-minute window")
result = results[0]
quote = result.get("indicators", {}).get("quote", [{}])[0]
timestamps = result.get("timestamp") or []
candles = []
for i, ts in enumerate(timestamps):
    vals = [quote.get(k, [None] * len(timestamps))[i] for k in ("open","high","low","close","volume")]
    if all(v is not None and math.isfinite(v) for v in vals[:4]):
        candles.append({"timestamp": ts, "open": vals[0], "high": vals[1], "low": vals[2], "close": vals[3], "volume": vals[4] or 0})
if len(candles) < 60:
    meta = result.get("meta", {})
    raise RuntimeError(
        f"Not enough valid GC=F 1-minute candles in 5-day window: {len(candles)}; "
        f"provider={meta.get('fullExchangeName', 'unknown')}, "
        f"currency={meta.get('currency', 'unknown')}. "
        "The feed may be closed or Yahoo may not have supplied intraday history."
    )

closes = [c["close"] for c in candles]
def ema(values, period):
    alpha = 2/(period+1); out=[]; value=values[0]
    for x in values:
        value = x*alpha + value*(1-alpha); out.append(value)
    return out
def rsi(values, period=14):
    out=[None]*len(values)
    gains=[]; losses=[]
    for i in range(1,len(values)):
        change=values[i]-values[i-1]
        gains.append(max(change,0)); losses.append(max(-change,0))
        if i>=period:
            ag=sum(gains[i-period:i])/period; al=sum(losses[i-period:i])/period
            out[i]=100 if al==0 else 100-100/(1+ag/al)
    return out
def atr(data, period=14):
    tr=[]
    for i,c in enumerate(data):
        prev=data[i-1]["close"] if i else c["close"]
        tr.append(max(c["high"]-c["low"],abs(c["high"]-prev),abs(c["low"]-prev)))
    out=[None]*len(data)
    for i in range(period-1,len(data)): out[i]=sum(tr[i-period+1:i+1])/period
    return out

fast=ema(closes,20); slow=ema(closes,50); momentum=rsi(closes); volatility=atr(candles)
for i,c in enumerate(candles):
    c.update({"ema20":fast[i],"ema50":slow[i],"rsi14":momentum[i],"atr14":volatility[i]})
last=candles[-1]
signal="WAIT"
if last["rsi14"] is not None and last["atr14"] and last["ema20"]>last["ema50"] and last["rsi14"]>=50: signal="BUY"
elif last["rsi14"] is not None and last["atr14"] and last["ema20"]<last["ema50"] and last["rsi14"]<=50: signal="SELL"

# Conservative historical paper simulation: enter on the next candle; if SL and TP
# are both touched in one candle, assume SL first. Risk is fixed at 0.5% of equity.
balance=10000.0; peak=balance; max_dd=0.0; position=None; trades=[]
for i in range(50,len(candles)):
    c=candles[i]
    if position:
        exit_price=None; reason=None
        if position["side"]=="BUY":
            if c["low"]<=position["stop"]: exit_price,reason=position["stop"],"STOP_LOSS"
            elif c["high"]>=position["target"]: exit_price,reason=position["target"],"TAKE_PROFIT"
        else:
            if c["high"]>=position["stop"]: exit_price,reason=position["stop"],"STOP_LOSS"
            elif c["low"]<=position["target"]: exit_price,reason=position["target"],"TAKE_PROFIT"
        if exit_price is not None:
            direction=1 if position["side"]=="BUY" else -1
            pnl=(exit_price-position["entry"])*position["units"]*direction
            balance+=pnl
            trades.append({"side":position["side"],"entry":position["entry"],"exit":exit_price,"pnl":pnl,"reason":reason})
            position=None
    if position is None and i>50:
        prev=candles[i-1]
        side="BUY" if prev["ema20"]>prev["ema50"] and prev["rsi14"] is not None and prev["rsi14"]>=50 else "SELL" if prev["ema20"]<prev["ema50"] and prev["rsi14"] is not None and prev["rsi14"]<=50 else None
        if side and prev["atr14"] and prev["atr14"]>0:
            entry=c["open"]; distance=prev["atr14"]
            risk_cash=balance*0.005; units=risk_cash/distance
            position={"side":side,"entry":entry,"units":units,
                "stop":entry-distance if side=="BUY" else entry+distance,
                "target":entry+2*distance if side=="BUY" else entry-2*distance}
    peak=max(peak,balance); max_dd=max(max_dd,(peak-balance)/peak*100 if peak else 0)
if position:
    last_price=candles[-1]["close"]; direction=1 if position["side"]=="BUY" else -1
    pnl=(last_price-position["entry"])*position["units"]*direction; balance+=pnl
    trades.append({"side":position["side"],"entry":position["entry"],"exit":last_price,"pnl":pnl,"reason":"END_OF_WINDOW"})
wins=sum(t["pnl"]>0 for t in trades); losses=sum(t["pnl"]<0 for t in trades)
payload={"symbol":"XAU/USD (GC=F gold futures proxy)","provider_symbol":"GC=F","timeframe":"1m","signal":signal,
 "latest_price":last["close"],"currency":"USD","updated_at":datetime.now(timezone.utc).isoformat(),
 "source":"Yahoo Finance public chart endpoint; futures proxy, not broker XAU/USD quote",
 "news_blind":True,"paper_only":True,"risk_per_trade_pct":0.5,
 "strategy":{"ema_fast":20,"ema_slow":50,"rsi_period":14,"atr_period":14,"stop_atr":1,"target_atr":2},
 "simulation":{"starting_balance":10000,"ending_balance":balance,"pnl":balance-10000,
 "return_pct":(balance/10000-1)*100,"trades":len(trades),"wins":wins,"losses":losses,
 "win_rate_pct":wins/len(trades)*100 if trades else 0,"max_drawdown_pct":max_dd,
 "open_position":None},
 "candles":candles[-360:],"trade_history":trades[-100:]}
os.makedirs("dashboard",exist_ok=True)
with open("dashboard/gold.json","w",encoding="utf-8") as f: json.dump(payload,f,separators=(",",":"))
