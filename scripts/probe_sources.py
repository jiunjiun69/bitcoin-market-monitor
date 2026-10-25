from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import re
urls = [
 "https://www.mnav.com/mnav/strategy",
 "https://mnav.com/mnav/strategy",
 "https://strategyviewer.com/api/stock/mstr/financial-metrics/",
 "https://www.strategy.com/",
]
for u in urls:
 try:
  r=requests.get(u,timeout=18,headers={"User-Agent":"Mozilla/5.0 (compatible; MarketMonitor/1.0; research dashboard)"})
  soup=BeautifulSoup(r.text,"html.parser")
  t=soup.get_text(" ",strip=True)
  matches={k:(re.search(k,t,re.I).group(0) if re.search(k,t,re.I) else None) for k in [r"last updated.{0,34}",r"Market valuation.{0,150}",r"(?:Strategy\s+MSTR).{0,150}"]}
  print("PROBE",u,"status",r.status_code,"len",len(r.content),"title",str(soup.title.get_text(" ",strip=True) if soup.title else "")[:100],"samples",matches,"jsonkeys",list(r.json().keys())[:12] if r.headers.get("content-type","").startswith("application/json") else None)
 except Exception as e: print("PROBE",u,type(e).__name__,str(e)[:150])
