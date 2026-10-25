import json, math, re
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0 BTC Research Monitor"

def get(url, params=None, html=False):
    r=S.get(url,params=params,timeout=25); r.raise_for_status()
    return r.text if html else r.json()

def load(name,default):
    try: return json.loads((ROOT/"data"/name).read_text())
    except (OSError,ValueError): return default

def save(name,obj):
    (ROOT/"data"/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")

def merge(a,b):
    d={str(t):float(v) for t,v in a+b if v is not None and math.isfinite(float(v))}
    return [[t,d[t]] for t in sorted(d)[-2600:]]

def age(day,now):
    try:return (now.date()-date.fromisoformat(day)).days
    except (ValueError,TypeError):return 99999

def btc(old,now):
    end=now.date()
    start=(date.fromisoformat(old[-1][0])-timedelta(days=3)) if old and age(old[-1][0],now)<14 else end-timedelta(days=2400)
    data=[]; successes=0
    while start<end:
        stop=min(start+timedelta(days=275),end)
        try:
            bars=get("https://api.exchange.coinbase.com/products/BTC-USD/candles",{
                "granularity":86400,"start":start.isoformat()+"T00:00:00Z","end":stop.isoformat()+"T00:00:00Z"})
            for row in bars:
                dt=datetime.fromtimestamp(row[0],timezone.utc).date()
                if start<=dt<stop and dt<end and row[4]>0:data.append([dt.isoformat(),row[4]])
            successes+=1
        except Exception as e:print("BTC chunk",e)
        start=stop
    if not successes:raise RuntimeError("BTC history unavailable")
    return merge(old,data)

def mstr(old):
    error=None
    for host in ("query1.finance.yahoo.com","query2.finance.yahoo.com"):
        try:
            result=get("https://"+host+"/v8/finance/chart/MSTR",{"range":"2y","interval":"1d"})["chart"]["result"][0]
            pts=[]
            for t,p in zip(result["timestamp"],result["indicators"]["quote"][0]["close"]):
                if p and p>0:pts.append([datetime.fromtimestamp(t,timezone.utc).astimezone(ZoneInfo("America/New_York")).date().isoformat(),p])
            if pts:return merge(old,pts)
        except Exception as e:error=e
    raise RuntimeError("MSTR unavailable: "+str(error))

def parse_mnav_page(html, now):
    soup=BeautifulSoup(html,"html.parser")
    title=soup.title.get_text(" ",strip=True) if soup.title else ""
    value=re.search(r"Strategy\s*\(MSTR\)\s*mNAV\s*(\d+(?:\.\d+)?)\s*[×x]",title,re.I)
    text=soup.get_text(" ",strip=True)
    updated=re.search(r"last updated\s+([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})",text,re.I)
    if not value or not updated:
        raise RuntimeError("Third-party dated mNAV not present: unexpected page shape")
    amount=float(value.group(1))
    day=datetime.strptime(updated.group(1),"%b %d, %Y").date().isoformat()
    if age(day,now)<-1 or age(day,now)>5 or not 0.1<=amount<=20:
        raise RuntimeError("Third-party mNAV not fresh or outside valid bounds")
    return day, amount

def mnav(old,now):
    # Third-party proxy measure, NOT the official net-asset definition.
    html=get("https://www.mnav.com/mnav/strategy",html=True)
    day,amount=parse_mnav_page(html,now)
    return merge(old,[[day,amount]])

def mvrv(old,now):
    result=get("https://raw.githubusercontent.com/akpasz/btc-data/main/data/kpis.json")
    day=result["as_of"]; value=float(result["realised"]["z_close"])
    if age(day,now)<-1:raise RuntimeError("Future MVRV date")
    return merge(old,[[day,value]])

def ratio(stock,prices):
    d=dict(prices);out=[]
    for day,v in stock:
        previous=(date.fromisoformat(day)-timedelta(days=1)).isoformat()
        if previous in d and d[previous]>0:out.append([day,round(v/d[previous],9)])
    return out

def weekly(prices,now,n):
    close=now.date()-timedelta(days=(now.date().weekday()+1)%7)
    if now.date().weekday()==6:close-=timedelta(days=7)
    d=dict(prices); days=[(close-timedelta(weeks=i)).isoformat() for i in range(n)]
    return (round(sum(d[x] for x in days)/n,2) if all(x in d for x in days) else None),close.isoformat()

def metric(points,source,maxage,now):
    p=points[-1] if points else None
    return {"value":p[1] if p else None,"date":p[0] if p else None,
    "freshness":"fresh" if p and -1<=age(p[0],now)<=maxage else "stale" if p else "missing",
    "source":source,"max_age_days":maxage}

def signal(key,title,status,note,day=None):
    return {"id":key,"title":title,"status":status,"evidence":note,"observed_at":day}

def main():
    now=datetime.now(timezone.utc)
    hist=load("history.json",{})
    hist={k:hist.get(k,[]) for k in ("btc","mstr","mnav","mvrv","ratio")}
    health=[]
    feeds=[("btc",lambda:btc(hist["btc"],now)),("mstr",lambda:mstr(hist["mstr"])),("mnav",lambda:mnav(hist["mnav"],now)),("mvrv",lambda:mvrv(hist["mvrv"],now))]
    for key,fn in feeds:
        try:
            hist[key]=fn();health.append({"name":key,"status":"ok"})
        except Exception as e:
            health.append({"name":key,"status":"error","details":str(e)[:200]})
            print(key,"ERROR",e)
    hist["ratio"]=ratio(hist["mstr"],hist["btc"])
    sources={"btc":("Coinbase BTC/USD daily",2),"mstr":("Yahoo Finance unofficial",5),
      "mnav":("mnav.com Strategy MSTR third-party asset-based multiple (NOT official mNAV)",5),
      "mvrv":("akpasz/btc-data Coin Metrics reconstructed",3),
      "ratio":("MSTR close / previous BTC UTC close",5)}
    metrics={k:metric(hist[k],*source,now) for k,source in sources.items()}
    signals=[]
    pts=[p for p in hist["mnav"] if age(p[0],now)<=40]
    if len(pts)>=16 and metrics["mnav"]["freshness"]=="fresh":
        peak=max(x[1] for x in pts);down=100*(pts[-1][1]/peak-1)
        signals.append(signal("mnav","mNAV 高位溢價收縮","watch" if peak>=1.5 and down<=-15 else "clear",
          "40日峰值 %.2fx，收縮 %.1f%%"%(peak,down),pts[-1][0]))
    else:signals.append(signal("mnav","mNAV 高位溢價收縮","unknown","資料累積中：需16筆同口徑歷史觀測後才能判定；這不是來源故障。"))
    pts=[p for p in hist["ratio"] if age(p[0],now)<=45]
    if len(pts)>=20 and metrics["ratio"]["freshness"]=="fresh" and metrics["btc"]["freshness"]=="fresh" and metrics["mstr"]["freshness"]=="fresh":
        vals=[x[1] for x in pts[-20:]];change=(vals[-1]/vals[0]-1)*100
        signals.append(signal("ratio","MSTR/BTC 相對走弱","watch" if change<=-8 and vals[-1]<sum(vals)/len(vals) else "clear",
          "近20交易日變化 %+.1f%%"%change,pts[-1][0]))
    else:signals.append(signal("ratio","MSTR/BTC 相對走弱","unknown","需要20筆近期有效行情"))
    z=metrics["mvrv"]
    signals.append(signal("mvrv","MVRV Z-Score 過熱","unknown" if z["freshness"]!="fresh" else "watch" if z["value"]>=3.5 else "clear",
        "資料過期" if z["freshness"]!="fresh" else "Z-Score %.2f"%z["value"],z["date"]))
    averages={str(n):weekly(hist["btc"],now,n)[0] for n in (50,200,300)}
    wday=weekly(hist["btc"],now,50)[1];close=dict(hist["btc"]).get(wday)
    valid_week=close is not None and averages["50"] is not None and metrics["btc"]["freshness"]=="fresh"
    signals.append(signal("weekly","BTC 週線低於50W MA","unknown" if not valid_week else "watch" if close<averages["50"] else "clear",
      "週線資料不足" if not valid_week else "週收盤 %.0f，50W MA %.0f"%(close,averages["50"]),wday))
    counts={k:sum(x["status"]==k for x in signals) for k in ("watch","clear","unknown")}
    regime="unknown" if counts["unknown"]>=2 else "high" if counts["watch"]>=3 else "caution" if counts["watch"] else "normal"
    latest={"schema_version":"1.0","generated_at":now.isoformat(timespec="seconds"),"metrics":metrics,
      "weekly":{"date":wday,"close":close,"sma":averages},
      "summary":{"regime":regime,"counts":counts,"method":"研究性、未經回測校準"},
      "signals":signals,"health":health,
      "series":{k:v[-2200:] if k=="btc" else v[-730:] for k,v in hist.items()},
      "disclosures":["各指標不是即時行情；注意資料日期與過期狀態。",
      "mNAV 使用 mnav.com 第三方口徑，不等同 Strategy 官方淨資產口徑；不能跨公式比較。",
      "MVRV是第三方重建，不是Glassnode原始數據。",
      "MSTR/BTC為非同步收盤近似；所有風險門檻未回測，非投資建議。"]}
    save("history.json",hist);save("latest.json",latest)
    print("Saved",counts,{h["name"]:h["status"] for h in health})

if __name__=="__main__":main()
