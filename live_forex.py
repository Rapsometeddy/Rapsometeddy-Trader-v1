"""Live paper-trading simulator for educational preset testing.

Uses public FX quotes/candles and keeps every position simulated in memory.
No broker credentials or order endpoints are used.
"""
import json, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from bot.strategy import add_indicators, generate_signal
from config import INITIAL_BALANCE, RISK_PER_TRADE, STOP_LOSS_PCT, TAKE_PROFIT_PCT

PAIRS={"EUR/USD":"EURUSD=X","GBP/USD":"GBPUSD=X","USD/JPY":"JPY=X","AUD/USD":"AUDUSD=X","USD/CAD":"CAD=X","USD/CHF":"CHF=X","NZD/USD":"NZDUSD=X"}
PRESETS={
 "Balanced":{"fast_ema":20,"slow_ema":50,"rsi_buy":50,"rsi_sell":50,"sl":0.02,"tp":0.04},
 "Fast Day Trade":{"fast_ema":9,"slow_ema":21,"rsi_buy":55,"rsi_sell":45,"sl":0.01,"tp":0.02},
 "Trend Study":{"fast_ema":20,"slow_ema":50,"rsi_buy":55,"rsi_sell":45,"sl":0.015,"tp":0.03},
 "Conservative":{"fast_ema":50,"slow_ema":200,"rsi_buy":55,"rsi_sell":45,"sl":0.01,"tp":0.02},
}
def fetch(symbol):
 u="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol)+"?range=1d&interval=1m&includePrePost=false"
 r=urllib.request.Request(u,headers={"User-Agent":"Rapsometeddy-Trader/1.0"})
 with urllib.request.urlopen(r,timeout=15) as x:return json.load(x)
def candles(payload):
 z=payload["chart"]["result"][0]; q=z["indicators"]["quote"][0]; rows=[]
 for i,t in enumerate(z.get("timestamp",[])):
  v={k:q[k][i] for k in ("open","high","low","close","volume")}
  if all(x is not None for x in v.values()): rows.append({"timestamp":int(t),**{k:float(x) for k,x in v.items()}})
 return pd.DataFrame(rows)
def test(df,p):
 d=df.copy()
 d["fast"]=d.close.ewm(span=p["fast_ema"],adjust=False).mean()
 d["slow"]=d.close.ewm(span=p["slow_ema"],adjust=False).mean()
 delta=d.close.diff(); gain=delta.clip(lower=0).rolling(14).mean(); loss=-delta.clip(upper=0).rolling(14).mean()
 d["rsi"]=100-(100/(1+gain/loss))
 bal=INITIAL_BALANCE; pos=None; trades=[]
 for _,r in d.iterrows():
  price=float(r.close)
  if pos:
   exit_price=None; reason=None
   if pos["side"]=="BUY":
    if r.low<=pos["sl"]: exit_price=pos["sl"];reason="STOP"
    elif r.high>=pos["tp"]: exit_price=pos["tp"];reason="TARGET"
   else:
    if r.high>=pos["sl"]: exit_price=pos["sl"];reason="STOP"
    elif r.low<=pos["tp"]: exit_price=pos["tp"];reason="TARGET"
   if exit_price:
    pnl=(exit_price-pos["entry"])*pos["qty"]*(1 if pos["side"]=="BUY" else -1);bal+=pnl
    trades.append({"side":pos["side"],"entry":pos["entry"],"exit":exit_price,"pnl":pnl,"reason":reason});pos=None
  if pos is None and pd.notna(r.fast) and pd.notna(r.slow) and pd.notna(r.rsi):
   side="BUY" if r.fast>r.slow and r.rsi>=p["rsi_buy"] else "SELL" if r.fast<r.slow and r.rsi<=p["rsi_sell"] else None
   if side:
    risk=bal*RISK_PER_TRADE; sl=price*(1-p["sl"] if side=="BUY" else 1+p["sl"]);tp=price*(1+p["tp"] if side=="BUY" else 1-p["tp"])
    qty=risk/abs(price-sl);pos={"side":side,"entry":price,"sl":sl,"tp":tp,"qty":qty}
 return {"starting_balance":INITIAL_BALANCE,"ending_balance":round(bal,2),"total_pnl":round(bal-INITIAL_BALANCE,2),"return_pct":round((bal/INITIAL_BALANCE-1)*100,2),"trades":len(trades),"wins":sum(t["pnl"]>0 for t in trades),"losses":sum(t["pnl"]<=0 for t in trades),"last_signal":("BUY" if pos and pos["side"]=="BUY" else "SELL" if pos else "HOLD"),"open_position":None if not pos else {"side":pos["side"],"entry":pos["entry"]}}
def main():
 out={"updated_at":datetime.now(timezone.utc).isoformat(),"paper_only":True,"presets":PRESETS,"markets":{}}
 for pair,symbol in PAIRS.items():
  try:
   df=candles(fetch(symbol)); out["markets"][pair]={"price":float(df.close.iloc[-1]),"timestamp":int(df.timestamp.iloc[-1]),"presets":{n:test(df,p) for n,p in PRESETS.items()}}
  except Exception as e: out["markets"][pair]={"error":str(e)}
 Path("dashboard/live-forex.json").write_text(json.dumps(out,indent=2)+"\n")
if __name__=="__main__":main()
