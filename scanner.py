"""Educational market scanner for Rapsometeddy Trader.
Public market data only. Produces ranked *conditions*, not trading advice or orders.
"""
import json, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

PAIRS = {
    "EUR/USD":"EURUSD=X","GBP/USD":"GBPUSD=X","USD/JPY":"JPY=X",
    "USD/CAD":"CAD=X","USD/CHF":"CHF=X","AUD/USD":"AUDUSD=X","NZD/USD":"NZDUSD=X",
    "EUR/JPY":"EURJPY=X","GBP/JPY":"GBPJPY=X",
}
STOCKS = {"AAPL":"AAPL","MSFT":"MSFT","NVDA":"NVDA","TSLA":"TSLA","AMZN":"AMZN","META":"META"}

def fetch(symbol):
    u="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol)+"?range=5d&interval=15m&includePrePost=false"
    req=urllib.request.Request(u,headers={"User-Agent":"Rapsometeddy-Trader/1.0"})
    with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)

def frame(payload):
    z=payload["chart"]["result"][0]; q=z["indicators"]["quote"][0]
    rows=[]
    for i,t in enumerate(z.get("timestamp",[])):
        v={k:q[k][i] for k in ("open","high","low","close","volume")}
        if all(x is not None for x in v.values()):
            rows.append({"timestamp":int(t),**{k:float(x) for k,x in v.items()}})
    return pd.DataFrame(rows)

def analyze(df):
    if len(df)<60: return {"signal":"HOLD","score":0,"reason":"Not enough candles"}
    c=df.close
    e9=c.ewm(span=9,adjust=False).mean(); e21=c.ewm(span=21,adjust=False).mean()
    e50=c.ewm(span=50,adjust=False).mean()
    d=c.diff(); gain=d.clip(lower=0).rolling(14).mean(); loss=-d.clip(upper=0).rolling(14).mean()
    rsi=100-(100/(1+gain/loss))
    ema12=c.ewm(span=12,adjust=False).mean(); ema26=c.ewm(span=26,adjust=False).mean()
    macd=ema12-ema26; macd_signal=macd.ewm(span=9,adjust=False).mean()
    tr=pd.concat([df.high-df.low,(df.high-c.shift()).abs(),(df.low-c.shift()).abs()],axis=1).max(axis=1)
    atr=tr.rolling(14).mean()
    typical=(df.high+df.low+c)/3
    vwap=(typical*df.volume).rolling(20).sum()/df.volume.rolling(20).sum().replace(0,pd.NA)
    score=0; reasons=[]
    if e9.iloc[-1]>e21.iloc[-1]>e50.iloc[-1]: score+=2; reasons.append("EMA trend up")
    elif e9.iloc[-1]<e21.iloc[-1]<e50.iloc[-1]: score-=2; reasons.append("EMA trend down")
    if rsi.iloc[-1]>=55: score+=1; reasons.append("RSI momentum up")
    elif rsi.iloc[-1]<=45: score-=1; reasons.append("RSI momentum down")
    if macd.iloc[-1]>macd_signal.iloc[-1]: score+=1; reasons.append("MACD positive")
    elif macd.iloc[-1]<macd_signal.iloc[-1]: score-=1; reasons.append("MACD negative")
    if pd.notna(vwap.iloc[-1]) and c.iloc[-1]>vwap.iloc[-1]: score+=1; reasons.append("above VWAP")
    elif pd.notna(vwap.iloc[-1]) and c.iloc[-1]<vwap.iloc[-1]: score-=1; reasons.append("below VWAP")
    signal="BUY SETUP" if score>=3 else "SELL SETUP" if score<=-3 else "NEUTRAL"
    return {"price":round(float(c.iloc[-1]),6),"signal":signal,"score":score,
            "rsi":round(float(rsi.iloc[-1]),2),"atr":round(float(atr.iloc[-1]),6),
            "macd":round(float(macd.iloc[-1]),6),"vwap":None if pd.isna(vwap.iloc[-1]) else round(float(vwap.iloc[-1]),6),
            "reason":", ".join(reasons),"candles":len(df)}

def main():
    markets={}
    for name,symbol in {**PAIRS,**STOCKS}.items():
        try: markets[name]=analyze(frame(fetch(symbol)))
        except Exception as e: markets[name]={"signal":"UNAVAILABLE","score":0,"reason":str(e)}
    out={"updated_at":datetime.now(timezone.utc).isoformat(),"timeframe":"15m","paper_only":True,
         "session":"New York analysis window 08:00–17:00 local time; scanner is informational.",
         "markets":markets}
    Path("dashboard/scanner.json").write_text(json.dumps(out,indent=2)+"\n")
if __name__=="__main__": main()
