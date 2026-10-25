"use strict";
const $=id=>document.getElementById(id);
const safe=x=>String(x??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const f=(v,d=0)=>v==null||!Number.isFinite(Number(v))?"—":Number(v).toLocaleString("en-US",{minimumFractionDigits:d,maximumFractionDigits:d});
const format=(k,v)=>v==null?"—":k==="btc"?"$"+f(v):k==="mstr"?"$"+f(v,2):k==="ratio"?f(v,6):k==="mnav"?f(v,2)+"x":f(v,2);
const names={btc:"BTC / USD",ratio:"MSTR / BTC",mnav:"STRATEGY mNAV",mvrv:"MVRV Z-SCORE"};
const statusText={watch:"警戒",clear:"未觸發",unknown:"待驗證"};
let snapshot=null,metric="btc",days=90;
function freshness(data){
  let today=new Date(),todayUtc=Date.UTC(today.getUTCFullYear(),today.getUTCMonth(),today.getUTCDate());
  for(const [key,m] of Object.entries(data.metrics||{})){
    let t=m.date?Date.parse(m.date+"T00:00:00Z"):NaN;
    let age=Number.isFinite(t)?Math.floor((todayUtc-t)/86400000):Infinity;
    if(!Number.isFinite(age)||age>m.max_age_days||age< -1)m.freshness=m.date?"stale":"missing";
  }
  for(const s of data.signals||[]){
    let dependencies=s.id==="weekly"?["btc"]:s.id==="ratio"?["ratio","btc","mstr"]:[s.id];
    if(dependencies.some(k=>data.metrics?.[k]?.freshness!=="fresh")){
      s.status="unknown";s.evidence="來源資料失效或過期，暫停此項風險判定。";
    }
  }
  let counts={watch:0,clear:0,unknown:0};
  for(const s of data.signals||[])counts[s.status]=(counts[s.status]||0)+1;
  data.summary.counts=counts;
  data.summary.regime=counts.unknown>=2?"unknown":counts.watch>=3?"high":counts.watch?"caution":"normal";
}
function render(){
  if(!snapshot)return;
  const d=snapshot,m=d.metrics||{},c=d.summary.counts||{};
  $("updated").textContent=d.generated_at?"更新於 "+new Date(d.generated_at).toLocaleString("zh-TW",{timeZone:"Asia/Taipei"}):"尚未更新";
  $("regime").textContent=({unknown:"資料不足",normal:"暫無警報",caution:"提高警覺",high:"高度警戒"})[d.summary.regime]||"資料不足";
  $("counts").textContent=(c.watch||0)+" 項警示 · "+(c.clear||0)+" 項未觸發 · "+(c.unknown||0)+" 項待驗證";
  $("metrics").innerHTML=["btc","ratio","mnav","mvrv"].map(k=>{
    let x=m[k]||{},st=x.freshness||"missing";
    return '<article class="metric"><div class="tag">'+names[k]+'</div><div class="value">'+safe(format(k,x.value))+'</div><div class="sub '+safe(st)+'">'+(st==="fresh"?"● 有效":st==="stale"?"● 已過期":"● 無資料")+' · '+safe(x.date||"尚未取得")+'</div></article>';
  }).join("");
  $("signals").innerHTML=(d.signals||[]).map(s=>'<div class="row"><div><strong>'+safe(s.title)+'</strong><small>'+safe(s.evidence)+'</small></div><span class="pill '+safe(s.status)+'">'+(statusText[s.status]||"待驗證")+'</span></div>').join("")||"等待第一次更新";
  const w=d.weekly||{},sm=w.sma||{};
  $("weekly").innerHTML=[["最近完整週 K",w.close,w.date],["50 週均線",sm["50"],"50W SMA"],["200 週均線",sm["200"],"200W SMA"],["300 週均線",sm["300"],"300W SMA"]].map(([name,v,detail])=>'<div class="row"><div>'+name+'<small>'+safe(detail||"")+'</small></div><strong>'+(v==null?"—":"$"+f(v))+'</strong></div>').join("");
  $("health").innerHTML=(d.health||[]).map(h=>{
    let fresh=m[h.name]?.freshness,ok=h.status==="ok"&&fresh==="fresh";
    return '<div class="row"><div><strong>'+safe(h.name.toUpperCase())+'</strong><small>'+safe(h.details||m[h.name]?.source||"")+'</small></div><span class="pill '+(ok?"clear":"watch")+'">'+(ok?"正常":h.status==="error"?"讀取失敗":"過期")+'</span></div>';
  }).join("")||"等待第一次更新";
  $("disclosures").textContent=(d.disclosures||[]).join(" · ");
  draw();
}
function draw(){
  if(!snapshot)return;
  const series=(snapshot.series?.[metric]||[]).filter(p=>p&&p.length===2&&Number.isFinite(Number(p[1])));
  const last=series.length?Date.parse(series[series.length-1][0]+"T00:00:00Z"):Date.now();
  const cutoff=days?last-days*86400000:-Infinity;
  const pts=series.filter(p=>Date.parse(p[0]+"T00:00:00Z")>=cutoff);
  $("chart-val").textContent=format(metric,pts.length?pts[pts.length-1][1]:null);
  $("chart-foot").textContent=snapshot.metrics?.[metric]?.source||"資料不足";
  if(pts.length<2){$("graph").textContent="有效歷史觀測值不足，暫無圖表";return}
  const W=780,H=270,L=68,T=18,R=10,B=33;
  const vals=pts.map(p=>Number(p[1])),a=Math.min(...vals),b=Math.max(...vals),pad=(b-a)*.12||(Math.abs(a)*.05)||1,lo=a-pad,hi=b+pad;
  const x=i=>L+i*(W-L-R)/(pts.length-1),y=v=>T+(hi-v)*(H-T-B)/(hi-lo);
  const path=pts.map((p,i)=>(i?"L":"M")+x(i).toFixed(2)+","+y(+p[1]).toFixed(2)).join(" ");
  const grid=Array.from({length:5},(_,i)=>{
    const yy=T+(H-T-B)*i/4,v=hi-(hi-lo)*i/4;
    return '<line x1="'+L+'" y1="'+yy+'" x2="'+(W-R)+'" y2="'+yy+'" stroke="#e9edf4"/><text class="axis" x="'+(L-9)+'" y="'+(yy+4)+'" text-anchor="end">'+(metric==="btc"?Math.round(v/1000)+"K":metric==="ratio"?v.toFixed(4):v.toFixed(2))+'</text>';
  }).join("");
  const axis=[0,Math.floor(pts.length/2),pts.length-1].map((i,j)=>'<text class="axis" x="'+x(i)+'" y="'+(H-6)+'" text-anchor="'+(j===0?"start":j===2?"end":"middle")+'">'+safe(pts[i][0])+'</text>').join("");
  $("graph").innerHTML='<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="none" role="img" aria-label="歷史數據走勢">'+grid+'<path d="'+path+'" fill="none" stroke="#4e83b8" stroke-width="2.7" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'+axis+'</svg>';
}
function setup(group,attr,cb){
  $(group).querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>{
    $(group).querySelectorAll("button").forEach(e=>e.classList.toggle("active",e===b));
    cb(b.dataset[attr]);draw();
  }));
}
setup("tabs","k",v=>metric=v);setup("ranges","d",v=>days=+v);
(async()=>{
  try{
    const r=await fetch("./data/latest.json",{cache:"no-store"});
    if(!r.ok)throw Error("HTTP "+r.status);
    snapshot=await r.json();
    if(snapshot.schema_version!=="1.0")throw Error("unsupported schema");
    freshness(snapshot);render();
  }catch(e){$("regime").textContent="資料讀取失敗";$("updated").textContent=String(e);console.error(e)}
})();